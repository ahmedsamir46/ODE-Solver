from flask import Flask, render_template, request, jsonify
import numpy as np
import sympy as sp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import logging
from scipy.integrate import solve_ivp
from scipy.optimize import root_scalar, brentq
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Filter warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

app = Flask(__name__)

# Mathematical constants and validation
SUPPORTED_FUNCTIONS = {
    'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
    'sinh', 'cosh', 'tanh', 'exp', 'log', 'log10', 'sqrt',
    'pi', 'e'
}

class ODESolverError(Exception):
    """Custom exception for ODE solver errors"""
    pass

def validate_equation(equation_str):
    """Validate equation string and check for supported functions"""
    if not equation_str or not equation_str.strip():
        raise ODESolverError("Equation cannot be empty")
    
    # Check for potentially dangerous operations
    dangerous_patterns = ['import', '__', 'exec', 'eval', 'open', 'file']
    for pattern in dangerous_patterns:
        if pattern in equation_str.lower():
            raise ODESolverError(f"Potentially dangerous operation detected: {pattern}")
    
    return True

def parse_equation(equation_str):
    """Parse equation string with enhanced error handling"""
    try:
        validate_equation(equation_str)
        
        x, y, yp = sp.symbols('x y yp')
        
        # Standardize equation format
        equation_str = equation_str.strip()
        if not equation_str.startswith("y''"):
            equation_str = f"y'' = {equation_str}"
        
        # Replace derivatives
        equation_str = equation_str.replace("y''", 'd2y')
        equation_str = equation_str.replace("y'", 'yp')
        
        # Parse the equation
        equation = sp.sympify(equation_str.split('=')[1].strip())
        
        # Validate the equation structure
        if equation.has(x, y, yp):
            return equation
        else:
            raise ODESolverError("Equation must contain x, y, and/or y'")
            
    except sp.SympifyError as e:
        raise ODESolverError(f"Invalid equation syntax: {str(e)}")
    except Exception as e:
        raise ODESolverError(f"Error parsing equation: {str(e)}")

def equation_to_function(equation_str):
    """Convert equation string to a callable function with validation"""
    try:
        x, y, p = sp.symbols('x y p')
        equation = parse_equation(equation_str)
        
        # Convert to lambda function
        func = sp.lambdify((x, y, p), equation, 'numpy')
        
        def odefunc(x, Y):
            try:
                y, p = Y
                dydt = p
                dpdt = func(x, y, p)
                
                # Check for numerical issues
                if not np.isfinite(dpdt):
                    logger.warning(f"Non-finite derivative detected at x={x}, y={y}, p={p}")
                    dpdt = np.nan_to_num(dpdt)
                
                return [dydt, dpdt]
            except Exception as e:
                logger.error(f"Error in ODE function: {str(e)}")
                raise ODESolverError(f"Evaluation error: {str(e)}")
        
        return odefunc
        
    except Exception as e:
        raise ODESolverError(f"Error converting equation to function: {str(e)}")

def finite_difference_method(equation_str, a, b, alpha, beta, bc_type, h):
    """Enhanced finite difference method with better error handling"""
    try:
        # Validate inputs
        if b <= a:
            raise ODESolverError("Upper bound must be greater than lower bound")
        if h <= 0:
            raise ODESolverError("Step size must be positive")
        if h > (b - a) / 2:
            raise ODESolverError("Step size too large for given interval")
        
        x, y = sp.symbols('x y')
        n = int((b - a) / h) + 1
        
        if n < 3:
            raise ODESolverError("Too few grid points. Use smaller step size.")
        
        x_vals = np.linspace(a, b, n)
        
        # Parse equation
        equation = parse_equation(equation_str)
        if equation is None:
            raise ODESolverError("Failed to parse equation")
        
        # Extract linear components: y'' = P(x)y' + Q(x)y + R(x)
        x_sym, y_sym, yp_sym = sp.symbols('x y yp')
        try:
            f_expr = equation.expand()
            P_expr = sp.diff(f_expr, yp_sym)
            Q_expr = sp.diff(f_expr, y_sym)
            R_expr = f_expr - P_expr * yp_sym - Q_expr * y_sym
            
            if P_expr.has(y_sym, yp_sym) or Q_expr.has(y_sym, yp_sym):
                raise ODESolverError("Finite Difference method only supports Linear ODEs. Please use the Shooting Method for non-linear equations.")
            
            # Convert to functions
            P_func = sp.lambdify((x_sym), P_expr, 'numpy')
            Q_func = sp.lambdify((x_sym), Q_expr, 'numpy')
            R_func = sp.lambdify((x_sym), R_expr, 'numpy')
        except ODESolverError:
            raise
        except Exception as e:
            logger.error(f"Error extracting linear components, equation might not be a valid linear ODE: {str(e)}")
            raise ODESolverError("Finite Difference method requires a valid Linear ODE. For non-linear, please use the Shooting Method.")

        # Build system matrix
        A = np.zeros((n, n))
        B = np.zeros(n)
        
        # Interior points (standard central difference)
        for i in range(1, n - 1):
            xi = x_vals[i]
            Pi = P_func(xi)
            Qi = Q_func(xi)
            Ri = R_func(xi)
            
            # Discretization: y_{i-1}(2 + hP_i) - y_i(4 + 2h^2Q_i) + y_{i+1}(2 - hP_i) = 2h^2R_i
            A[i, i - 1] = 2 + h * Pi
            A[i, i] = -(4 + 2 * h**2 * Qi)
            A[i, i + 1] = 2 - h * Pi
            B[i] = 2 * h**2 * Ri
        
        # Boundary conditions
        if bc_type == "dirichlet":
            A[0, 0] = 1
            B[0] = alpha
            A[-1, -1] = 1
            B[-1] = beta
        else:  # Neumann at right boundary: y'(b) = beta
            A[0, 0] = 1
            B[0] = alpha
            if n >= 3:
                # 2nd-order backward difference for y'(b) to maintain O(h^2) precision
                A[-1, -3] = 1
                A[-1, -2] = -4
                A[-1, -1] = 3
                B[-1] = 2 * h * beta
            else:
                # Backward difference for y'(b): (y_n - y_{n-1}) / h = beta
                A[-1, -2] = -1
                A[-1, -1] = 1
                B[-1] = h * beta
        
        # Solve system
        try:
            # Check condition number for numerical stability
            cond_num = np.linalg.cond(A)
            if cond_num > 1e12:
                logger.warning(f"System is ill-conditioned (cond={cond_num:.2e})")
            
            y_vals = np.linalg.solve(A, B)
            
            # Validate solution
            if not np.all(np.isfinite(y_vals)):
                raise ODESolverError("Solution contains non-finite values (Check for singular matrix or small h)")
            
            # Compute 2nd-order precision numerical derivative for consistency in frontend
            yp_vals = np.zeros_like(y_vals)
            if n >= 3:
                yp_vals[0] = (-3*y_vals[0] + 4*y_vals[1] - y_vals[2]) / (2*h)
                yp_vals[-1] = (3*y_vals[-1] - 4*y_vals[-2] + y_vals[-3]) / (2*h)
                yp_vals[1:-1] = (y_vals[2:] - y_vals[:-2]) / (2*h)
            else:
                yp_vals[0] = (y_vals[1] - y_vals[0]) / h
                yp_vals[1] = yp_vals[0]
            
            return x_vals, y_vals, yp_vals
            
        except np.linalg.LinAlgError as e:
            raise ODESolverError(f"Linear algebra error: {str(e)}")
        except Exception as e:
            raise ODESolverError(f"Error solving system: {str(e)}")
            
    except ODESolverError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in finite difference method: {str(e)}")
        raise ODESolverError(f"Finite difference method failed: {str(e)}")

def shooting_method(equation_str, a, b, alpha, beta, bc_type, h):
    """Enhanced shooting method with robust root finding"""
    try:
        # Validate inputs
        if b <= a:
            raise ODESolverError("Upper bound must be greater than lower bound")
        if h <= 0:
            raise ODESolverError("Step size must be positive")
        
        x_sym, y_sym, yp_sym = sp.symbols('x y yp')
        
        # Parse equation
        equation_str = equation_str.strip()
        if not equation_str.startswith("y''"):
            equation_str = f"y'' = {equation_str}"
        
        equation_str = equation_str.replace("y''", 'd2y')
        equation_str = equation_str.replace("y'", 'yp')
        
        try:
            equation = sp.sympify(equation_str.split('=')[1].strip())
        except sp.SympifyError as e:
            raise ODESolverError(f"Invalid equation syntax: {str(e)}")
        
        # Build RHS function
        f_expr = equation.subs('yp', yp_sym)
        f = sp.lambdify((x_sym, y_sym, yp_sym), f_expr, 'numpy')
        
        def system(x, Y):
            """System of first-order ODEs"""
            try:
                y1, y2 = Y  # y1 = y, y2 = y'
                dy1dt = y2
                dy2dt = f(x, y1, y2)
                
                # Handle numerical issues
                if not np.isfinite(dy2dt):
                    dy2dt = np.nan_to_num(dy2dt)
                
                return [dy1dt, dy2dt]
            except Exception as e:
                logger.error(f"Error in system function: {str(e)}")
                return [0, 0]
        
        def solve_for_guess(guess):
            """Solve IVP for given initial slope guess with reinforced grid"""
            try:
                # Use linspace to ensure 'b' is always included correctly
                n_points = int((b - a) / h) + 1
                t_eval = np.linspace(a, b, n_points)
                
                sol = solve_ivp(
                    system, 
                    (a, b), 
                    [alpha, guess], 
                    t_eval=t_eval,
                    method='RK45',
                    rtol=1e-8,
                    atol=1e-10
                )
                
                if not sol.success:
                    return np.nan
                
                # Check boundary condition mismatch
                if bc_type == "dirichlet":
                    return sol.y[0, -1] - beta
                else:  # mixed: y'(b) = beta
                    return sol.y[1, -1] - beta
                    
            except Exception as e:
                logger.warning(f"IVP solver error: {str(e)}")
                return np.nan
        
        # Robust root finding: Scan for a sign change to bracket the root
        best_root = None
        found_bracket = False
        
        # Strategy: Scan multiple ranges with increasing width
        scan_ranges = [(-10, 10), (-100, 100), (-1000, 1000)]
        
        for low, high in scan_ranges:
            if found_bracket: break
            
            # Divide range into segments to find sign change
            scan_points = np.linspace(low, high, 41)
            prev_guess = scan_points[0]
            prev_val = solve_for_guess(prev_guess)
            
            for current_guess in scan_points[1:]:
                current_val = solve_for_guess(current_guess)
                
                if not np.isnan(prev_val) and not np.isnan(current_val):
                    if prev_val * current_val <= 0:
                        # Root bracketed between prev_guess and current_guess
                        try:
                            sol = root_scalar(
                                solve_for_guess, 
                                bracket=[prev_guess, current_guess], 
                                method='brentq',
                                xtol=1e-8
                            )
                            if sol.converged:
                                best_root = sol.root
                                found_bracket = True
                                break
                        except Exception:
                            pass
                
                prev_guess, prev_val = current_guess, current_val
        
        if best_root is None:
            raise ODESolverError("Shooting Method: Could not find an initial slope that satisfies the boundary condition. The problem may be unstable or requires a slope outside the scanned range.")
        
        # Final high-precision solution
        try:
            n_points = int((b - a) / h) + 1
            t_eval = np.linspace(a, b, n_points)
            final_sol = solve_ivp(
                system, 
                (a, b), 
                [alpha, best_root], 
                t_eval=t_eval,
                method='RK45',
                rtol=1e-10,
                atol=1e-12
            )
            
            if not final_sol.success:
                raise ODESolverError(f"Shooting Method: Final integration failed: {final_sol.message}")
            
            return final_sol.t, final_sol.y[0], final_sol.y[1]
            
        except Exception as e:
            raise ODESolverError(f"Shooting Method error: {str(e)}")
            
    except ODESolverError:
        raise
    except Exception as e:
        logger.error(f"Critical error in shooting method: {str(e)}")
        raise ODESolverError(f"Shooting Method failure: {str(e)}")

def create_plot(x, y, method_name):
    """Create an enhanced plot with better styling"""
    try:
        plt.figure(figsize=(12, 8))
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Plot solution
        plt.plot(x, y, 'b-', linewidth=2.5, label=f'{method_name} Solution', alpha=0.8)
        plt.scatter(x, y, color='red', s=30, alpha=0.7, zorder=5, label='Grid Points')
        
        # Enhanced styling
        plt.xlabel('x', fontsize=12, fontweight='600')
        plt.ylabel('y(x)', fontsize=12, fontweight='600')
        plt.title(f'Solution using {method_name}', fontsize=14, fontweight='700', pad=20)
        
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.legend(fontsize=10, loc='best')
        
        # Add error information if available
        if len(x) > 2:
            # Estimate numerical derivative for smoothness indication
            dy_dx = np.gradient(y, x)
            max_slope = np.max(np.abs(dy_dx))
            plt.text(0.02, 0.98, f'Max |dy/dx| = {max_slope:.2e}', 
                    transform=plt.gca().transAxes, fontsize=9,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        # Convert plot to PNG image
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=150, facecolor='white')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close()
        
        return plot_url
        
    except Exception as e:
        logger.error(f"Error creating plot: {str(e)}")
        # Return a simple error plot
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f'Plot Error: {str(e)}', 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes, fontsize=12)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close()
        
        return plot_url

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    """Enhanced solve endpoint with comprehensive error handling"""
    try:
        # Validate and parse form data
        equation = request.form.get('equation', '').strip()
        if not equation:
            return jsonify({'success': False, 'error': 'Equation is required'})
        
        try:
            a = float(request.form.get('a', 0))
            b = float(request.form.get('b', 1))
            alpha = float(request.form.get('alpha', 0))
            beta = float(request.form.get('beta', 1))
            bc_type = request.form.get('bc_type', 'dirichlet')
            h = float(request.form.get('h', 0.1))
        except ValueError as e:
            return jsonify({'success': False, 'error': f'Invalid numerical input: {str(e)}'})
        
        # Additional validation
        if b <= a:
            return jsonify({'success': False, 'error': 'Upper bound must be greater than lower bound'})
        if h <= 0:
            return jsonify({'success': False, 'error': 'Step size must be positive'})
        if h > (b - a) / 2:
            return jsonify({'success': False, 'error': 'Step size too large for the given interval'})
        
        logger.info(f"Solving ODE: {equation} on [{a}, {b}] with h={h}")
        
        results = {}
        errors = []
        
        # Solve using finite difference method
        try:
            x_fd, y_fd, yp_fd = finite_difference_method(equation, a, b, alpha, beta, bc_type, h)
            if x_fd is not None and y_fd is not None:
                plot_url_fd = create_plot(x_fd, y_fd, "Finite Difference Method")
                
                fd_table = []
                for i, (xi, yi, ypi) in enumerate(zip(x_fd, y_fd, yp_fd)):
                    fd_table.append({
                        'i': i, 
                        'x': round(xi, 6), 
                        'y': round(float(yi), 8) if np.isfinite(yi) else None,
                        'yp': round(float(ypi), 8) if np.isfinite(ypi) else None
                    })
                
                results['finite_difference'] = {
                    'plot': plot_url_fd,
                    'table': fd_table,
                    'method': 'Finite Difference',
                    'grid_points': len(x_fd),
                    'step_size': h
                }
            else:
                errors.append("Finite difference method failed to converge")
        except Exception as e:
            logger.error(f"Finite difference error: {str(e)}")
            errors.append(f"Finite difference error: {str(e)}")
        
        # Solve using shooting method
        try:
            x_shooting, y_shooting, yp_shooting = shooting_method(equation, a, b, alpha, beta, bc_type, h)
            if x_shooting is not None and y_shooting is not None:
                plot_url_shooting = create_plot(x_shooting, y_shooting, "Shooting Method")
                
                shooting_table = []
                for i, (xi, yi, ypi) in enumerate(zip(x_shooting, y_shooting, yp_shooting)):
                    shooting_table.append({
                        'i': i, 
                        'x': round(xi, 6), 
                        'y': round(float(yi), 8) if np.isfinite(yi) else None,
                        'yp': round(float(ypi), 8) if np.isfinite(ypi) else None
                    })
                
                results['shooting'] = {
                    'plot': plot_url_shooting,
                    'table': shooting_table,
                    'method': 'Shooting Method',
                    'grid_points': len(x_shooting),
                    'step_size': h
                }
            else:
                errors.append("Shooting method failed to converge")
        except Exception as e:
            logger.error(f"Shooting method error: {str(e)}")
            errors.append(f"Shooting method error: {str(e)}")
        
        if not results:
            error_msg = "Both methods failed. " + "; ".join(errors)
            return jsonify({'success': False, 'error': error_msg})
        
        # Add warnings if any method failed
        if errors:
            results['warnings'] = errors
        
        logger.info(f"Successfully solved ODE with {len(results)} method(s)")
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        logger.error(f"Unexpected error in solve endpoint: {str(e)}")
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'})

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

@app.route('/license')
def license():
    try:
        with open('LICENSE', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/plain'}
    except FileNotFoundError:
        return "License file not found.", 404




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)