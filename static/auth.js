// Authentication functions
function requireAuth() {
    if (!getCurrentUser()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

function getCurrentUser() {
    // This would normally come from the server session
    // For now, we'll use a simple implementation
    const username = sessionStorage.getItem('username');
    if (username) {
        return {
            username: username,
            wallet: JSON.parse(localStorage.getItem('phantomWalletState') || '{}')
        };
    }
    return null;
}

function checkAuth() {
    return fetch('/api/wallet-data')
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/login';
                throw new Error('Not authenticated');
            }
            return response.json();
        });
}

function saveWalletData(data) {
    return fetch('/api/save-wallet-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
}

// Initialize auth check on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the login page
    if (window.location.pathname === '/login') return;
    
    checkAuth().catch(error => {
        console.log('Authentication check failed:', error);
    });
});