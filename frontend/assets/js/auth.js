// Authentication logic to handle JWTs with a mock backend

// Simulated API Base URL (replace this when a real backend is attached)
const API_BASE_URL = 'http://localhost:3000/api';

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

        /*
        // REAL BACKEND IMPLEMENTATION:
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Login failed');
        }
        
        // Save the JWT Token
        localStorage.setItem('auth_token', data.token);
        */

        // MOCK BACKEND IMPLEMENTATION (for demonstration):
        await new Promise(resolve => setTimeout(resolve, 1000));

        if (email === 'demo@company.com' && password === 'password') {
            // Success mock
            localStorage.setItem('auth_token', 'mock_jwt_token_12345');
            window.location.href = '../v1.html'; // Redirect to dashboard
        } else {
            // Fail mock
            throw new Error('Invalid email or password. Try demo@company.com / password');
        }

    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.style.display = 'block';
    } finally {
        const btn = document.querySelector('.auth-btn');
        if (btn) {
            btn.innerHTML = 'Log in &rarr;';
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

    // Company name is optional if it's an individual account
    const company = accountType === 'company' ? document.getElementById('companyName').value : null;

    const errorBox = document.getElementById('registerError');

    errorBox.style.display = 'none';

    if (!validateEmail(email)) {
        errorBox.textContent = 'Please enter a valid email address.';
        errorBox.style.display = 'block';
        return;
    }

    if (password.length < 8) {
        errorBox.textContent = 'Password must be at least 8 characters long.';
        errorBox.style.display = 'block';
        return;
    }

    try {
        const btn = document.querySelector('.auth-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = 'Creating account...';
        btn.disabled = true;

        /*
        // REAL BACKEND IMPLEMENTATION:
        const payload = { accountType, firstName, lastName, email, password };
        if(accountType === 'company') payload.company = company;

        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Registration failed');
        }
        
        // Save the JWT Token and redirect
        localStorage.setItem('auth_token', data.token);
        */

        // MOCK BACKEND IMPLEMENTATION (for demonstration):
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Simulate success
        console.log("Mock Registration Request Payload:", { accountType, firstName, lastName, email, company, password });
        localStorage.setItem('auth_token', 'mock_jwt_token_67890');
        window.location.href = '../v1.html'; // Redirect to dashboard

    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.style.display = 'block';
    } finally {
        const btn = document.querySelector('.auth-btn');
        if (btn) {
            btn.innerHTML = 'Create account &rarr;';
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
    window.location.href = 'pages/login.html';
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

    /*
    // OPTIONAL: If we want to check auth on protected pages, uncomment this:
    if(!isAuthenticated() && window.location.pathname.includes('/dashboard')) {
        window.location.href = '/pages/login.html';
    }
    */
});
