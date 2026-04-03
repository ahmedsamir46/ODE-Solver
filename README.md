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
  - Interactive tour guide for seamless user onboarding
- **Advanced Numerical Solvers**:
  - **Finite Difference Method**: Strictly supports linear ODEs of the form $y'' = P(x)y' + Q(x)y + R(x)$ with second-order accuracy, featuring second-order backward difference implementations for Neumann boundary conditions.
  - **Shooting Method**: Robust RK45-based solver with adaptive step size control, utilizing an advanced scanning and bracketing root-finding strategy and extracting high-precision derivatives directly from the integration engine.
- **Full Boundary Condition Support**:
  - Dirichlet boundary conditions ($y(a) = \alpha$, $y(b) = \beta$)
  - Mixed/Neumann boundary conditions ($y(a) = \alpha$, $y'(b) = \beta$)
- **Interactive Visuals & Tools**: 
  - Real-time plotting with high-quality result tables and "Quick Templates" for rapid testing.
  - One-click CSV export functionality for all numerical result tables.
  - Robust error reporting with clear, actionable feedback when solvers fail to converge.
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
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Multi-container orchestration
├── Procfile               # Heroku deployment configuration
├── requirements.txt       # Unified Python dependencies
├── README.md              # Project documentation
├── static/                # Frontend assets
│   ├── css/
│   │   └── style.css      # Premium unified stylesheet
│   └── js/
│       ├── script.js      # AJAX handling & interactive logic
│       └── tour.js        # Interactive user onboarding guide
└── templates/             # HTML5 Templates
    ├── base.html          # Shared layout with glassmorphism navbar
    ├── index.html         # Interactive solver dashboard
    └── documentation.html # Technical guide & math theory
```

## 🔬 Technical Details

### Numerical Engine
- **Finite Difference**: Uses central difference approximations for the domain and second-order backward differences for boundary conditions. The engine automatically extracts linear coefficients ($P, Q, R$) using **SymPy** to build and solve tridiagonal matrix systems.
- **Shooting Method**: Implements a "Projectile" approach converting BVPs to IVPs. Uses **solve_ivp** (RK45) alongside robust scanning and bracketing capabilities for high-precision determination of the initial slope, guaranteeing mathematical rigor.

### Accuracy & Stability
- **FD**: $O(h^2)$ consistent truncation error across the domain and boundaries.
- **Shooting**: $O(h^5)$ local error, extremely stable for complex non-linear systems due to adaptive step size and pre-scanned bracketing strategies.

## 🤝 Contributing
Contributions are welcome! Whether it's adding new solvers, improving UI aesthetics, or fixing bugs, feel free to fork and PR.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**⭐ Star this repository if you find it useful!**
