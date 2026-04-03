let currentResults = null;

function setSampleEquation(eq) {
    document.getElementById('equation').value = eq;
    // Add visual feedback
    const input = document.getElementById('equation');
    input.classList.add('is-valid');
    setTimeout(() => input.classList.remove('is-valid'), 2000);
}

// Helper to trigger file downloads
function triggerDownload(content, fileName, contentType) {
    const a = document.createElement('a');
    const file = new Blob([content], {type: contentType});
    a.href = URL.createObjectURL(file);
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(a.href);
}

function downloadImage(method) {
    const container = document.getElementById(`${method}-plot`);
    const img = container.querySelector('img');
    if (!img) return;
    
    const a = document.createElement('a');
    a.href = img.src;
    a.download = `ode_solver_${method}_plot.png`;
    a.click();
}

function exportData(method) {
    if (!currentResults || !currentResults[method === 'fd' ? 'finite_difference' : 'shooting']) {
        alert('No data available to export. Please solve an ODE first.');
        return;
    }
    
    const methodData = currentResults[method === 'fd' ? 'finite_difference' : 'shooting'];
    const equation = document.getElementById('equation').value.replace(/[^a-z0-9]/gi, '_');
    const fileName = `ode_results_${method}_${equation}.csv`;
    
    // Build CSV content
    let csv = 'Index,x_i,y(x_i),y\'(x_i)\n';
    
    methodData.table.forEach((row, index) => {
        csv += `${row.i},${row.x},${row.y},${row.yp}\n`;
    });
    
    triggerDownload(csv, fileName, 'text/csv');
}

$(document).ready(function() {
    // Only add jQuery form handler if form exists
    if ($('#odeForm').length > 0) {
        $('#odeForm').on('submit', function(e) {
            e.preventDefault();
        
            // UI Feedback
            $('#loading').show();
            $('#error-display').hide();
            $('#results').hide();
        
            // Get form data
            const formData = new FormData(this);
        
            // Submit form data via AJAX
            $.ajax({
                url: '/solve',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    $('#loading').hide();
                    
                    if (response.success) {
                        currentResults = response.results; // Store for export
                        displayResults(response.results);
                    } else {
                        $('#error-display').text('Error: ' + response.error).show();
                    }
                },
                error: function() {
                    $('#loading').hide();
                    $('#error-display').text('Server error. Please try again.').show();
                }
            });
        });
    }
    
    // Handle displaying the results from the solver
    function displayResults(results) {
        // Handle warnings
        const warningsContainer = $('#warnings-container');
        const warningsContent = $('#warnings-content');
        if (results.warnings && results.warnings.length > 0) {
            warningsContent.empty();
            results.warnings.forEach(w => {
                warningsContent.append(`<div>• ${w}</div>`);
            });
            warningsContainer.show();
        } else {
            warningsContainer.hide();
        }

        // Process each method
        const methods = ['finite_difference', 'shooting'];
        methods.forEach(m => {
            const methodKey = m;
            const prefix = m === 'finite_difference' ? 'fd' : 'shooting';
            const data = results[methodKey];

            if (data) {
                // Update stats
                $(`#${prefix}-points`).text(data.grid_points);
                $(`#${prefix}-step`).text(data.step_size);

                // Update Plot
                const plotContainer = $(`#${prefix}-plot`);
                plotContainer.html(`<img src="data:image/png;base64,${data.plot}" alt="${data.method} Plot" class="img-fluid fade-in shadow-sm">`);

                // Update Table
                const tableBody = $(`#${prefix}-table-body`);
                tableBody.empty();

                data.table.forEach((row, index) => {
                    const yVal = (row.y !== null && typeof row.y === 'number') ? row.y.toFixed(6) : (row.y || 'N/A');
                    const ypVal = (row.yp !== null && typeof row.yp === 'number') ? row.yp.toFixed(6) : (row.yp || 'N/A');
                    
                    const rowHtml = `
                        <tr>
                            <td class="text-muted small">${row.i}</td>
                            <td class="fw-500">${row.x}</td>
                            <td class="text-primary fw-bold">${yVal}</td>
                            <td class="text-muted">${ypVal}</td>
                        </tr>
                    `;
                    tableBody.append(rowHtml);
                });

                $(`#${prefix}-plot`).closest('.card').show();
            } else {
                $(`#${prefix}-plot`).closest('.card').hide();
            }
        });

        // Trigger MathJax to re-process the new content if needed
        if (window.MathJax && window.MathJax.typeset) {
            window.MathJax.typeset();
        }

        $('#results').fadeIn(600);
    }
});