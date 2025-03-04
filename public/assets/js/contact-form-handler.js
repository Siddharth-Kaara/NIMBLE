/**
 * Contact Form Error Handling
 * 
 * This script handles displaying error messages when redirected back from form submission
 */

document.addEventListener('DOMContentLoaded', function() {
    // Function to get URL parameters
    function getUrlParameter(name) {
        name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
        var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
        var results = regex.exec(location.search);
        return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
    }
    
    // Check if there's an error message in the URL
    var errorMessage = getUrlParameter('error');
    if (errorMessage) {
        // Find the contact form and error element
        var contactForm = document.getElementById('contactForm');
        var errorElement = document.getElementById('contactFormError');
        
        if (contactForm && errorElement) {
            // Set the error message
            errorElement.textContent = errorMessage;
            
            // Make the error element visible
            errorElement.style.display = 'block';
            
            // Scroll to the form - using a safer selector
            try {
                // First try to find the contact section
                var contactSection = document.getElementById('contact');
                if (contactSection) {
                    contactSection.scrollIntoView({ behavior: 'smooth' });
                } else {
                    // Fallback to the form itself
                    contactForm.scrollIntoView({ behavior: 'smooth' });
                }
            } catch (e) {
                console.error('Error scrolling to contact form:', e);
                // Another fallback - just scroll to the form
                contactForm.scrollIntoView({ behavior: 'smooth' });
            }
        }
    }
    
    // Add form submission logging
    var contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(event) {
            // Log form submission
            console.log('Contact form submitted');
            
            // Get form data
            var formData = new FormData(contactForm);
            var formDataObj = {};
            formData.forEach(function(value, key) {
                formDataObj[key] = value;
            });
            
            // Log form data (excluding message for privacy)
            console.log('Form data:', {
                name: formDataObj.name,
                email: formDataObj.email,
                phone: formDataObj.phone,
                message: formDataObj.message ? '(message content)' : '(empty)'
            });
            
            // Continue with normal form submission
            // No need to prevent default - let the form submit normally
        });
    }
}); 