
// Use relative API base for FastAPI
const API_BASE_URL = '/api/v1/auth';

/**
 * Validates email format
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
}

/**
 * Handle user login
 */
async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorBox = document.getElementById('loginError');
    errorBox.style.display = 'none';

    if (!validateEmail(email) || !password) {
        errorBox.textContent = 'Please enter a valid email and password.';
        errorBox.style.display = 'block';
        return;
    }

    try {
        const btn = document.querySelector('.auth-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = 'Logging in...';
        btn.disabled = true;

        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Login failed');
        }

        // Save the JWT Token
        localStorage.setItem('auth_token', data.access_token);

        // Redirect to dashboard
        window.location.href = '/app/dashboard';

    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.style.display = 'block';
    } finally {
        const btn = document.querySelector('.auth-btn');
        if (btn) {
            btn.innerHTML = 'Log in →';
            btn.disabled = false;
        }
    }
}

/**
 * Handle user registration
 */
async function handleRegister(event) {
    event.preventDefault();

    // The account type selector
    const accountTypeRadio = document.querySelector('input[name="accountType"]:checked');
    const accountType = accountTypeRadio ? accountTypeRadio.value : 'company';

    const firstName = document.getElementById('firstName').value;
    const lastName = document.getElementById('lastName').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const name = `${firstName} ${lastName}`;

    const errorBox = document.getElementById('registerError');
    errorBox.style.display = 'none';

    if (!validateEmail(email)) {
        errorBox.textContent = 'Please enter a valid email address.';
        errorBox.style.display = 'block';
        return;
    }
    if (password.length < 6) {
        errorBox.textContent = 'Password must be at least 6 characters long.';
        errorBox.style.display = 'block';
        return;
    }

    try {
        const btn = document.querySelector('.auth-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = 'Creating account...';
        btn.disabled = true;

        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Registration failed');
        }

        // Registration success, redirect to login
        window.location.href = '/app/login';

    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.style.display = 'block';
    } finally {
        const btn = document.querySelector('.auth-btn');
        if (btn) {
            btn.innerHTML = 'Create account →';
            btn.disabled = false;
        }
    }
}

/**
 * Check if user is logged in
 */
function isAuthenticated() {
    return !!localStorage.getItem('auth_token');
}

/**
 * Logout utility
 */
function logout() {
    localStorage.removeItem('auth_token');
    window.location.href = '/app/login';
}

// Bind events on load depending on which page we are on
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    // Protect dashboard route
    if (window.location.pathname === '/app/dashboard') {
        if (!isAuthenticated()) {
            window.location.href = '/app/login';
        }
    }
});
