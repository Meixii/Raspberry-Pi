// API endpoint
const API_URL = 'http://192.168.1.49:5000/api';

// Development bypass function
function handleBypassLogin() {
    // Store mock user data for development
    localStorage.setItem('user', JSON.stringify({
        id: 'dev-user',
        name: 'Developer',
        email: 'dev@example.com',
        picture: 'https://ui-avatars.com/api/?name=Developer'
    }));
    
    // Store mock token
    localStorage.setItem('token', 'dev-token');
    
    // Redirect to dashboard
    window.location.href = 'index.html';
}

// Form visibility functions
function showLogin() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('forgot-password-form').style.display = 'none';
    document.getElementById('login-toggle').style.display = 'block';
    document.getElementById('register-toggle').style.display = 'none';
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.getElementById('forgot-password-form').style.display = 'none';
    document.getElementById('login-toggle').style.display = 'none';
    document.getElementById('register-toggle').style.display = 'block';
}

function showForgotPassword() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('forgot-password-form').style.display = 'block';
    document.getElementById('login-toggle').style.display = 'none';
    document.getElementById('register-toggle').style.display = 'none';
}

// Handle login form submission
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (data.success) {
            // Store token and user info
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Redirect to dashboard
            window.location.href = 'index.html';
        } else {
            alert(data.message || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('An error occurred during login. Please try again.');
    }
}

// Handle registration form submission
async function handleRegistration(event) {
    event.preventDefault();
    
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;

    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
            showLogin();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('An error occurred during registration. Please try again.');
    }
}

// Handle forgot password form submission
async function handleForgotPassword(event) {
    event.preventDefault();
    
    const email = document.getElementById('forgot-email').value;

    try {
        const response = await fetch(`${API_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
            showLogin();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Forgot password error:', error);
        alert('An error occurred. Please try again.');
    }
}

// Handle Google login
async function handleGoogleLogin(response) {
    try {
        const res = await fetch(`${API_URL}/auth/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ credential: response.credential })
        });

        const data = await res.json();

        if (data.success) {
            // Store token and user info
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Redirect to dashboard
            window.location.href = '/dashboard.html';
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Google login error:', error);
        alert('An error occurred during Google login. Please try again.');
    }
}

// Check if user is already logged in
function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        window.location.href = '../website/index.html';
    }
}

// Handle Google Sign-In
function handleCredentialResponse(response) {
    // Send the token to your backend
    fetch(`${API_URL}/auth/google`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            credential: response.credential
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            localStorage.setItem('token', data.token);
            window.location.href = 'index.html';
        } else {
            showError('Authentication failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Authentication failed');
    });
}

// Error handling
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

// Initialize Google Sign-In
window.onload = function() {
    google.accounts.id.initialize({
        client_id: "168778392576-u4asnjk51fvlrnv9upig2pp0orgqpsbv.apps.googleusercontent.com",
        callback: handleCredentialResponse
    });
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    
    // Add bypass button event listener
    const bypassBtn = document.getElementById('bypass-login-btn');
    if (bypassBtn) {
        bypassBtn.addEventListener('click', handleBypassLogin);
    }
}); 