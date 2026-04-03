/**
 * ODE Solver Tour Guide
 * A simple, native implementation for interactive onboarding.
 */

const tourSteps = [
    {
        element: '#odeForm',
        title: 'System Configuration',
        content: 'This is where you define your Boundary Value Problem. Enter the right-hand side of your second-order ODE.',
        position: 'bottom'
    },
    {
        element: '#equation',
        title: 'The Equation',
        content: 'Enter the expression for y\'\'. You can use x, y, and y\' (as yp). Example: -y + sin(x).',
        position: 'bottom'
    },
    {
        element: '#a',
        title: 'Interval Boundaries',
        content: 'Define the start (a) and end (b) points of the calculation interval.',
        position: 'right'
    },
    {
        element: '#dirichlet',
        title: 'Boundary Conditions',
        content: 'Choose between Dirichlet (fixed values) or Mixed (value at a, derivative at b).',
        position: 'top'
    },
    {
        element: '#h',
        title: 'Step Size',
        content: 'Control the density of the grid. Smaller values increase accuracy but take more computation time.',
        position: 'top'
    },
    {
        element: '.btn-primary',
        title: 'Solve!',
        content: 'Click here to compute the solution using both Finite Difference and Shooting methods.',
        position: 'top'
    }
];

let currentStep = 0;
let tourOverlay = null;

function startTour() {
    currentStep = 0;
    createTourOverlay();
    showStep(currentStep);
}

function createTourOverlay() {
    if (tourOverlay) return;
    
    tourOverlay = document.createElement('div');
    tourOverlay.className = 'tour-overlay';
    document.body.appendChild(tourOverlay);
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tour-tooltip card shadow-lg';
    tooltip.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center bg-primary text-white">
            <h6 class="mb-0 fw-bold tour-title"></h6>
            <button type="button" class="btn-close btn-close-white small" onclick="endTour()"></button>
        </div>
        <div class="card-body">
            <p class="tour-content small mb-3"></p>
            <div class="d-flex justify-content-between">
                <button class="btn btn-sm btn-outline-secondary tour-prev" onclick="prevStep()">Prev</button>
                <div class="text-muted small align-self-center tour-progress"></div>
                <button class="btn btn-sm btn-primary tour-next" onclick="nextStep()">Next</button>
            </div>
        </div>
    `;
    document.body.appendChild(tooltip);
}

function showStep(stepIndex) {
    const step = tourSteps[stepIndex];
    const element = document.querySelector(step.element);
    const tooltip = document.querySelector('.tour-tooltip');
    
    if (!element) {
        nextStep();
        return;
    }
    
    // Highlight element
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));
    element.classList.add('tour-highlight');
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Update tooltip
    tooltip.querySelector('.tour-title').textContent = step.title;
    tooltip.querySelector('.tour-content').textContent = step.content;
    tooltip.querySelector('.tour-progress').textContent = `${stepIndex + 1} / ${tourSteps.length}`;
    
    tooltip.querySelector('.tour-prev').disabled = stepIndex === 0;
    tooltip.querySelector('.tour-next').textContent = stepIndex === tourSteps.length - 1 ? 'Finish' : 'Next';
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    let top, left;
    const offset = 15;
    
    if (step.position === 'bottom') {
        top = rect.bottom + scrollTop + offset;
        left = rect.left + scrollLeft + (rect.width / 2) - (tooltip.offsetWidth / 2);
    } else if (step.position === 'top') {
        top = rect.top + scrollTop - tooltip.offsetHeight - offset;
        left = rect.left + scrollLeft + (rect.width / 2) - (tooltip.offsetWidth / 2);
    } else if (step.position === 'right') {
        top = rect.top + scrollTop + (rect.height / 2) - (tooltip.offsetHeight / 2);
        left = rect.right + scrollLeft + offset;
    }
    
    // Keep in viewport
    left = Math.max(10, Math.min(left, window.innerWidth - tooltip.offsetWidth - 10));
    top = Math.max(10, Math.min(top, document.documentElement.scrollHeight - tooltip.offsetHeight - 10));
    
    tooltip.style.display = 'block';
    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
    tooltip.classList.add('fade-in');
}

function nextStep() {
    if (currentStep < tourSteps.length - 1) {
        currentStep++;
        showStep(currentStep);
    } else {
        endTour();
    }
}

function prevStep() {
    if (currentStep > 0) {
        currentStep--;
        showStep(currentStep);
    }
}

function endTour() {
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));
    if (tourOverlay) {
        tourOverlay.remove();
        tourOverlay = null;
    }
    const tooltip = document.querySelector('.tour-tooltip');
    if (tooltip) tooltip.remove();
}
