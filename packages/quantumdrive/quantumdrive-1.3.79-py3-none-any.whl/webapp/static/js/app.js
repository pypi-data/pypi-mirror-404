// app.js

document.addEventListener('DOMContentLoaded', function() {
    console.log("App.js loaded. Document is ready.");

    // Disable submit button on form submission to prevent duplicate submissions
    const taskForm = document.querySelector('form');
    if (taskForm) {
        taskForm.addEventListener('submit', function(event) {
            const submitButton = taskForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Processing...';
            }
        });
    }

    // Automatically fade out alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    if (alerts) {
        setTimeout(() => {
            alerts.forEach(alert => {
                alert.style.transition = 'opacity 1s ease-out';
                alert.style.opacity = '0';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.parentNode.removeChild(alert);
                    }
                }, 1000);
            });
        }, 5000);
    }
});
