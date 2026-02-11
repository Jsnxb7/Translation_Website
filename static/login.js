document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');

    loginForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const email = document.getElementById('emaillog').value;
        const password = document.getElementById('passlog').value;

        // Create a data object to send to the server
        const data = {
            email: email,
            password: password
        };

        // Send a POST request to the server for verification
        fetch('/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            // Check the response from the server
            if (data.success) {
                // Redirect to a success page
                window.location.href = '/success';
            } else {
                // Display an error message on the login page
                const errorDiv = document.createElement('div');
                errorDiv.textContent = 'Login failed. Please check your credentials.';
                loginForm.appendChild(errorDiv);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});
