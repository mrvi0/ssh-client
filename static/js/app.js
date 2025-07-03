// Global variables
let socket = null;
let currentUser = null;
let currentConnection = null;
let connections = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Check if user is logged in
    const token = localStorage.getItem('auth_token');
    if (!token) {
        showLoginModal();
    } else {
        // Verify token and load data
        verifyToken(token);
    }
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Initialize Socket.IO
    initializeSocket();
}

function initializeEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const page = this.dataset.page;
            navigateToPage(page);
        });
    });
    
    // Modal controls
    document.getElementById('new-connection-btn').addEventListener('click', showConnectionModal);
    document.getElementById('add-connection-btn').addEventListener('click', showConnectionModal);
    document.getElementById('modal-close').addEventListener('click', hideConnectionModal);
    document.getElementById('cancel-btn').addEventListener('click', hideConnectionModal);
    
    // Forms
    document.getElementById('connection-form').addEventListener('submit', handleConnectionSubmit);
    document.getElementById('login-form').addEventListener('submit', handleLoginSubmit);
    document.getElementById('register-btn').addEventListener('click', handleRegister);
    
    // Authentication method toggle
    document.getElementById('auth-method').addEventListener('change', toggleAuthMethod);
    
    // Terminal controls
    document.getElementById('command-input').addEventListener('keypress', handleCommandKeypress);
    document.getElementById('clear-terminal').addEventListener('click', clearTerminal);
    document.getElementById('disconnect-btn').addEventListener('click', disconnectSSH);
}

function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
    });
    
    socket.on('ssh_connected', function(data) {
        console.log('SSH connected:', data);
        addTerminalLine(`Connected to ${currentConnection.name}`, 'success');
        updateConnectionStatus(currentConnection.id, 'connected');
    });
    
    socket.on('ssh_output', function(data) {
        console.log('SSH output:', data);
        if (data.output) {
            addTerminalLine(data.output, 'output');
        }
        if (data.error) {
            addTerminalLine(data.error, 'error');
        }
    });
    
    socket.on('ssh_error', function(data) {
        console.log('SSH error:', data);
        addTerminalLine(`Error: ${data.message}`, 'error');
    });
    
    socket.on('ssh_disconnected', function(data) {
        console.log('SSH disconnected:', data);
        addTerminalLine('Disconnected from server', 'warning');
        updateConnectionStatus(currentConnection.id, 'disconnected');
        currentConnection = null;
    });
}

// Navigation
function navigateToPage(page) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    // Update page content
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`${page}-page`).classList.add('active');
    
    // Update page title
    const titles = {
        'dashboard': 'Dashboard',
        'connections': 'Connections',
        'terminal': 'Terminal',
        'settings': 'Settings'
    };
    document.getElementById('page-title').textContent = titles[page];
    
    // Load page-specific data
    if (page === 'connections') {
        loadConnections();
    } else if (page === 'dashboard') {
        loadDashboard();
    }
}

// Authentication
function showLoginModal() {
    document.getElementById('login-modal').classList.add('active');
}

function hideLoginModal() {
    document.getElementById('login-modal').classList.remove('active');
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('auth_token', data.token);
            currentUser = data.user;
            hideLoginModal();
            loadDashboard();
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed');
    }
}

async function handleRegister() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        alert('Please enter username and password');
        return;
    }
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Registration successful! Please login.');
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('Registration failed');
    }
}

async function verifyToken(token) {
    try {
        const response = await fetch('/api/verify', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            loadDashboard();
        } else {
            localStorage.removeItem('auth_token');
            showLoginModal();
        }
    } catch (error) {
        console.error('Token verification error:', error);
        localStorage.removeItem('auth_token');
        showLoginModal();
    }
}

// Connections
function showConnectionModal() {
    document.getElementById('connection-modal').classList.add('active');
    document.getElementById('modal-title').textContent = 'New Connection';
    document.getElementById('connection-form').reset();
}

function hideConnectionModal() {
    document.getElementById('connection-modal').classList.remove('active');
}

function toggleAuthMethod() {
    const method = document.getElementById('auth-method').value;
    const passwordGroup = document.getElementById('password-group');
    const keyGroup = document.getElementById('key-group');
    const passphraseGroup = document.getElementById('passphrase-group');
    
    if (method === 'password') {
        passwordGroup.style.display = 'block';
        keyGroup.style.display = 'none';
        passphraseGroup.style.display = 'none';
    } else {
        passwordGroup.style.display = 'none';
        keyGroup.style.display = 'block';
        passphraseGroup.style.display = 'block';
    }
}

async function handleConnectionSubmit(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('conn-name').value,
        host: document.getElementById('conn-host').value,
        port: parseInt(document.getElementById('conn-port').value),
        username: document.getElementById('conn-username').value,
        group: document.getElementById('conn-group').value,
        tags: document.getElementById('conn-tags').value,
        notes: document.getElementById('conn-notes').value
    };
    
    const authMethod = document.getElementById('auth-method').value;
    if (authMethod === 'password') {
        formData.password = document.getElementById('conn-password').value;
    } else {
        formData.private_key = document.getElementById('conn-private-key').value;
        formData.passphrase = document.getElementById('conn-passphrase').value;
    }
    
    try {
        const response = await fetch('/api/connections', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            hideConnectionModal();
            loadConnections();
            alert('Connection saved successfully!');
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Connection save error:', error);
        alert('Failed to save connection');
    }
}

async function loadConnections() {
    try {
        const response = await fetch('/api/connections', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            }
        });
        
        if (response.ok) {
            connections = await response.json();
            renderConnections();
        }
    } catch (error) {
        console.error('Load connections error:', error);
    }
}

function renderConnections() {
    const grid = document.getElementById('connections-grid');
    grid.innerHTML = '';
    
    connections.forEach(connection => {
        const card = document.createElement('div');
        card.className = 'connection-card';
        card.innerHTML = `
            <div class="connection-name">
                <span class="status disconnected"></span>
                ${connection.name}
            </div>
            <div class="connection-details">
                ${connection.host}:${connection.port} • ${connection.username}
            </div>
            <div class="connection-actions">
                <button class="btn btn-small" onclick="connectToServer(${connection.id})">Connect</button>
                <button class="btn btn-small" onclick="editConnection(${connection.id})">Edit</button>
                <button class="btn btn-small" onclick="deleteConnection(${connection.id})">Delete</button>
            </div>
        `;
        grid.appendChild(card);
    });
}

function connectToServer(connectionId) {
    const connection = connections.find(c => c.id === connectionId);
    if (!connection) return;
    
    currentConnection = connection;
    navigateToPage('terminal');
    
    // Clear terminal
    clearTerminal();
    addTerminalLine(`Connecting to ${connection.name}...`, 'prompt');
    
    // Send connection request
    socket.emit('ssh_connect', { connection_id: connectionId });
}

function updateConnectionStatus(connectionId, status) {
    const card = document.querySelector(`[onclick="connectToServer(${connectionId})"]`).closest('.connection-card');
    const statusIndicator = card.querySelector('.status');
    
    statusIndicator.className = `status ${status}`;
    card.className = `connection-card ${status === 'connected' ? 'connected' : ''}`;
}

// Terminal
function addTerminalLine(text, type = 'output') {
    const terminal = document.getElementById('terminal');
    const line = document.createElement('div');
    line.className = `terminal-line terminal-${type}`;
    line.textContent = text;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

function handleCommandKeypress(e) {
    if (e.key === 'Enter') {
        const command = e.target.value.trim();
        if (command && currentConnection) {
            addTerminalLine(`$ ${command}`, 'prompt');
            socket.emit('ssh_command', {
                connection_id: currentConnection.id,
                command: command
            });
            e.target.value = '';
        }
    }
}

function clearTerminal() {
    document.getElementById('terminal').innerHTML = '';
}

function disconnectSSH() {
    if (currentConnection) {
        socket.emit('ssh_disconnect', { connection_id: currentConnection.id });
    }
}

// Dashboard
async function loadDashboard() {
    await loadConnections();
    
    document.getElementById('total-connections').textContent = connections.length;
    document.getElementById('active-connections').textContent = 
        connections.filter(c => c.status === 'connected').length;
}

// Utility functions
function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this with a proper notification library
    alert(message);
}

// Logout
function logout() {
    localStorage.removeItem('auth_token');
    currentUser = null;
    currentConnection = null;
    connections = [];
    showLoginModal();
} 