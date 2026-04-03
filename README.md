# ODE Solver Web Application

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.1+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![NumPy](https://img.shields.io/badge/numpy-1.21+-yellow.svg)
![SciPy](https://img.shields.io/badge/scipy-1.7+-purple.svg)

A premium, modern web application for solving Ordinary Differential Equations (ODEs) using advanced numerical methods. Built with Python, Flask, and a high-performance numerical engine, this tool provides both theoretical foundations and practical implementations for second-order boundary value problems (BVPs).

## 🎯 Features

- **Modern & Responsive UI**: 
  - Fully responsive design (Mobile-ready)
  - Inter font family for superior readability
  - Premium glassmorphism navbar and dark-themed hero sections
  - Fluid micro-animations for an enhanced user experience
- **Advanced Numerical Solvers**:
  - **Finite Difference Method**: Now supports linear ODEs of the form $y'' = P(x)y' + Q(x)y + R(x)$ with second-order accuracy.
  - **Shooting Method**: Robust RK45-based solver with adaptive step size control, capable of handling general non-linear ODEs.
- **Full Boundary Condition Support**:
  - Dirichlet boundary conditions ($y(a) = \alpha$, $y(b) = \beta$)
  - Mixed/Neumann boundary conditions ($y(a) = \alpha$, $y'(b) = \beta$)
- **Interactive Visuals**: Real-time plotting with high-quality result tables and "Quick Templates" for rapid testing.
- **Educational Resources**: In-depth mathematical documentation explaining the theory behind each solver.


## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Setup

1. **Clone the repository**:
```bash
git clone https://github.com/ahmedsamir46/ODE-Solver.git
cd ODE-Solver
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
python app.py
```

4. **Access the portal**: Open `http://localhost:8000` in your browser.

## 📁 Project Structure

```
ode-solver/
├── app.py                 # Main Flask application & Solver Engine
├── requirements.txt       # Unified Python dependencies
├── README.md             # Project documentation
├── static/               # Frontend assets
│   ├── css/
│   │   └── style.css     # Premium unified stylesheet
│   └── js/
│       └── script.js     # AJAX handling & interactive logic
└── templates/            # HTML5 Templates
    ├── base.html         # Shared layout with glassmorphism navbar
    ├── index.html        # Interactive solver dashboard
    └── documentation.html # Technical guide & math theory
```

## 🔬 Technical Details

### Numerical Engine
- **Finite Difference**: Uses central difference approximations. The engine automatically extracts linear coefficients ($P, Q, R$) using **SymPy** to build and solve tridiagonal matrix systems.
- **Shooting Method**: Implements a "Projectile" approach converting BVPs to IVPs. Uses **solve_ivp** (RK45) and **Brent's method** for high-precision root finding of the initial slope.

### Accuracy & Stability
- **FD**: $O(h^2)$ truncation error.
- **Shooting**: $O(h^5)$ local error, extremely stable for non-linear systems.

## 🤝 Contributing
Contributions are welcome! Whether it's adding new solvers, improving UI aesthetics, or fixing bugs, feel free to fork and PR.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**⭐ Star this repository if you find it useful!**
