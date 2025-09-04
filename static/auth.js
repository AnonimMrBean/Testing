// Authentication functions
async function apiRequest(endpoint, data = {}) {
    try {
        const response = await fetch(`/api/${endpoint}`, {
            method: data.method || 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: data.body ? JSON.stringify(data.body) : undefined,
            credentials: 'include'
        });
        
        if (response.status === 401) {
            window.location.href = '/login';
            throw new Error('Not authenticated');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Get wallet data from server
async function getWalletData() {
    return await apiRequest('wallet-data', { method: 'GET' });
}

// Save wallet data to server
async function saveWalletData(data) {
    return await apiRequest('save-wallet-data', { 
        body: data,
        method: 'POST'
    });
}

// Check authentication status
async function checkAuth() {
    try {
        const data = await getWalletData();
        return data;
    } catch (error) {
        console.log('Authentication check failed:', error);
        return null;
    }
}

// Initialize auth check on page load
document.addEventListener('DOMContentLoaded', async function() {
    // Check if we're on the login page
    if (window.location.pathname === '/login') return;
    
    try {
        const walletData = await checkAuth();
        if (walletData) {
            // Initialize app with server data
            if (typeof initializeApp === 'function') {
                initializeApp(walletData);
            }
        }
    } catch (error) {
        console.log('Failed to initialize app:', error);
    }
});