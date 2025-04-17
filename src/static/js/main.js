/**
 * Main JavaScript for osu! to Clone Hero converter
 */

document.addEventListener("DOMContentLoaded", function() {
    // Theme switching functionality
    const themeToggle = document.getElementById('theme-toggle');
    
    // Check for saved theme preference or use default (dark)
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    // Apply the saved theme on load
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        themeToggle.checked = false;
    } else {
        document.body.classList.remove('light-theme');
        themeToggle.checked = true;
    }
    
    // Handle theme toggle click
    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            // Dark theme
            document.body.classList.remove('light-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            // Light theme
            document.body.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('.btn-copy');
    
    if (copyButtons) {
        copyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const outputElement = document.querySelector(this.getAttribute('data-target'));
                if (outputElement) {
                    // Create a temporary textarea element to copy from
                    const textarea = document.createElement('textarea');
                    textarea.value = outputElement.textContent;
                    textarea.style.position = 'fixed';  // Prevent scrolling to bottom
                    document.body.appendChild(textarea);
                    textarea.select();
                    
                    try {
                        // Execute copy command
                        const successful = document.execCommand('copy');
                        if (successful) {
                            // Update button text temporarily
                            const originalText = this.textContent;
                            this.textContent = 'Copied!';
                            setTimeout(() => {
                                this.textContent = originalText;
                            }, 2000);
                        } else {
                            console.error('Copy command failed');
                        }
                    } catch (err) {
                        console.error('Error copying text: ', err);
                    }
                    
                    // Clean up
                    document.body.removeChild(textarea);
                }
            });
        });
    }
    
    // Form validation
    const convertForm = document.getElementById('convert-form');
    if (convertForm) {
        convertForm.addEventListener('submit', function(e) {
            const urlInput = document.getElementById('beatmap_url');
            if (!urlInput.value.trim()) {
                e.preventDefault();
                showError('Please enter a beatmap URL');
                return false;
            }
            
            // Simple URL validation 
            const urlPattern = /^https?:\/\/osu\.ppy\.sh\/beatmapsets\/\d+/;
            if (!urlPattern.test(urlInput.value)) {
                e.preventDefault();
                showError('Invalid osu! beatmap URL. Please enter a URL like: https://osu.ppy.sh/beatmapsets/123456');
                return false;
            }
            
            // Show loading state
            const submitButton = convertForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="loading-spinner"></span> Processing...';
            }
            
            return true;
        });
    }
    
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            setTimeout(() => {
                message.style.opacity = '0';
                setTimeout(() => {
                    message.remove();
                }, 500);
            }, 5000);
        });
    }
});

/**
 * Show error message
 * @param {string} message - The error message to display
 */
function showError(message) {
    // Check if an error message already exists
    let errorElement = document.querySelector('.alert-danger');
    
    if (!errorElement) {
        // Create new error element
        errorElement = document.createElement('div');
        errorElement.className = 'alert alert-danger';
        
        // Insert at the top of the form
        const form = document.getElementById('convert-form');
        form.parentNode.insertBefore(errorElement, form);
    }
    
    errorElement.textContent = message;
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        errorElement.style.opacity = '0';
        setTimeout(() => {
            errorElement.remove();
        }, 500);
    }, 5000);
} 