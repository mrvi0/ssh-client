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

// SSH Client Web Application JavaScript

class SSHClientApp {
    constructor() {
        this.socket = null;
        this.currentUser = null;
        this.token = localStorage.getItem('token');
        this.currentConnection = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkAuth();
    }
    
    setupEventListeners() {
        // Auth forms
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));
        
        // Connection form
        document.getElementById('connectionForm').addEventListener('submit', (e) => this.handleAddConnection(e));
        
        // Snippet form
        document.getElementById('snippetForm').addEventListener('submit', (e) => this.handleAddSnippet(e));
        
        // Group form
        document.getElementById('groupForm').addEventListener('submit', (e) => this.handleAddGroup(e));
        
        // Tab switching
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.getAttribute('onclick').match(/'([^']+)'/)[1];
                this.showTab(tabName);
            });
        });
    }
    
    checkAuth() {
        if (this.token) {
            this.verifyToken();
        } else {
            this.showAuthModal();
        }
    }
    
    async verifyToken() {
        try {
            const response = await fetch('/api/verify', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                this.showMainApp();
                this.loadData();
            } else {
                this.showAuthModal();
            }
        } catch (error) {
            console.error('Token verification failed:', error);
            this.showAuthModal();
        }
    }
    
    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
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
                this.token = data.token;
                this.currentUser = data.user;
                localStorage.setItem('token', this.token);
                this.hideAuthModal();
                this.showMainApp();
                this.loadData();
                this.showNotification('Login successful', 'success');
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Login failed:', error);
            this.showNotification('Login failed', 'error');
        }
    }
    
    async handleRegister(e) {
        e.preventDefault();
        
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.token = data.token;
                this.currentUser = data.user;
                localStorage.setItem('token', this.token);
                this.hideAuthModal();
                this.showMainApp();
                this.loadData();
                this.showNotification('Registration successful', 'success');
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Registration failed:', error);
            this.showNotification('Registration failed', 'error');
        }
    }
    
    async loadData() {
        await Promise.all([
            this.loadConnections(),
            this.loadSnippets(),
            this.loadGroups(),
            this.loadAdminStats()
        ]);
    }
    
    async loadConnections() {
        try {
            const response = await fetch('/api/connections', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                const connections = await response.json();
                this.renderConnections(connections);
            }
        } catch (error) {
            console.error('Failed to load connections:', error);
        }
    }
    
    async loadSnippets() {
        try {
            const response = await fetch('/api/commands', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                const snippets = await response.json();
                this.renderSnippets(snippets);
            }
        } catch (error) {
            console.error('Failed to load snippets:', error);
        }
    }
    
    async loadGroups() {
        try {
            const response = await fetch('/api/groups', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                const groups = await response.json();
                this.renderGroups(groups);
            }
        } catch (error) {
            console.error('Failed to load groups:', error);
        }
    }
    
    async loadAdminStats() {
        if (!this.currentUser?.is_admin) return;
        
        try {
            const response = await fetch('/api/admin/stats', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                const stats = await response.json();
                this.renderAdminStats(stats);
            }
        } catch (error) {
            console.error('Failed to load admin stats:', error);
        }
    }
    
    renderConnections(connections) {
        const container = document.getElementById('connectionsList');
        container.innerHTML = '';
        
        connections.forEach(conn => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${conn.name}</div>
                        <div class="list-item-subtitle">${conn.host}:${conn.port} - ${conn.username}</div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-small" onclick="app.connectToServer(${conn.id})">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn btn-small" onclick="app.editConnection(${conn.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-small" onclick="app.deleteConnection(${conn.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(item);
        });
    }
    
    renderSnippets(snippets) {
        const container = document.getElementById('snippetsList');
        container.innerHTML = '';
        
        snippets.forEach(snippet => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${snippet.name}</div>
                        <div class="list-item-subtitle">${snippet.category} - ${snippet.command}</div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-small" onclick="app.executeSnippet('${snippet.command}')">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn btn-small" onclick="app.editSnippet(${snippet.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-small" onclick="app.deleteSnippet(${snippet.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(item);
        });
    }
    
    renderGroups(groups) {
        const container = document.getElementById('groupsList');
        container.innerHTML = '';
        
        groups.forEach(group => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div class="list-item-header">
                    <div>
                        <div class="list-item-title">${group.name}</div>
                        <div class="list-item-subtitle">${group.members.length} members</div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-small" onclick="app.editGroup(${group.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-small" onclick="app.deleteGroup(${group.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(item);
        });
    }
    
    renderAdminStats(stats) {
        document.getElementById('connectionsCount').textContent = stats.connections_count;
        document.getElementById('snippetsCount').textContent = stats.commands_count;
        document.getElementById('groupsCount').textContent = stats.groups_count;
        document.getElementById('usersCount').textContent = stats.total_users;
    }
    
    async handleAddConnection(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('connName').value,
            host: document.getElementById('connHost').value,
            port: parseInt(document.getElementById('connPort').value),
            username: document.getElementById('connUsername').value,
            password: document.getElementById('connPassword').value,
            key_path: document.getElementById('connKeyPath').value,
            description: document.getElementById('connDescription').value
        };
        
        try {
            const response = await fetch('/api/connections', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                this.closeConnectionModal();
                this.loadConnections();
                this.showNotification('Connection added successfully', 'success');
            } else {
                const data = await response.json();
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Failed to add connection:', error);
            this.showNotification('Failed to add connection', 'error');
        }
    }
    
    async handleAddSnippet(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('snippetName').value,
            category: document.getElementById('snippetCategory').value,
            command: document.getElementById('snippetCommand').value,
            description: document.getElementById('snippetDescription').value
        };
        
        try {
            const response = await fetch('/api/commands', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                this.closeSnippetModal();
                this.loadSnippets();
                this.showNotification('Snippet added successfully', 'success');
            } else {
                const data = await response.json();
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Failed to add snippet:', error);
            this.showNotification('Failed to add snippet', 'error');
        }
    }
    
    async handleAddGroup(e) {
        e.preventDefault();
        
        const members = document.getElementById('groupMembers').value
            .split('\n')
            .map(m => m.trim())
            .filter(m => m);
            
        const formData = {
            name: document.getElementById('groupName').value,
            description: document.getElementById('groupDescription').value,
            members: members
        };
        
        try {
            const response = await fetch('/api/groups', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                this.closeGroupModal();
                this.loadGroups();
                this.showNotification('Group added successfully', 'success');
            } else {
                const data = await response.json();
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Failed to add group:', error);
            this.showNotification('Failed to add group', 'error');
        }
    }
    
    connectToServer(connectionId) {
        // This would connect to the SSH server
        this.currentConnection = connectionId;
        this.updateConnectionStatus('Connected');
        this.addTerminalLine('Connected to server', 'success');
    }
    
    executeSnippet(command) {
        if (!this.currentConnection) {
            this.showNotification('Please connect to a server first', 'warning');
            return;
        }
        
        this.addTerminalLine(`$ ${command}`, 'command');
        // This would execute the command on the SSH server
        this.addTerminalLine('Command executed successfully', 'output');
    }
    
    addTerminalLine(text, type = 'output') {
        const terminal = document.getElementById('terminalOutput');
        const line = document.createElement('div');
        line.className = 'terminal-line';
        
        if (type === 'command') {
            line.innerHTML = `<span class="prompt">$</span><span class="command">${text}</span>`;
        } else if (type === 'error') {
            line.innerHTML = `<span class="error">${text}</span>`;
        } else if (type === 'success') {
            line.innerHTML = `<span class="output" style="color: #4caf50;">${text}</span>`;
        } else {
            line.innerHTML = `<span class="output">${text}</span>`;
        }
        
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        statusElement.textContent = status;
        statusElement.className = status === 'Connected' ? 'status-online' : 'status-offline';
    }
    
    showTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Show selected tab
        document.getElementById(`${tabName}Tab`).classList.add('active');
        document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
        
        // Show/hide admin elements
        if (this.currentUser?.is_admin) {
            document.getElementById('adminTab').style.display = 'block';
            document.getElementById('addGroupBtn').style.display = 'block';
        } else {
            document.getElementById('adminTab').style.display = 'none';
            document.getElementById('addGroupBtn').style.display = 'none';
        }
    }
    
    showAuthModal() {
        document.getElementById('authModal').style.display = 'block';
        document.getElementById('mainApp').style.display = 'none';
    }
    
    hideAuthModal() {
        document.getElementById('authModal').style.display = 'none';
    }
    
    showMainApp() {
        document.getElementById('authModal').style.display = 'none';
        document.getElementById('mainApp').style.display = 'block';
        document.getElementById('userDisplay').textContent = this.currentUser.username;
    }
    
    showAddConnectionModal() {
        document.getElementById('connectionModal').style.display = 'block';
    }
    
    closeConnectionModal() {
        document.getElementById('connectionModal').style.display = 'none';
        document.getElementById('connectionForm').reset();
    }
    
    showAddSnippetModal() {
        document.getElementById('snippetModal').style.display = 'block';
    }
    
    closeSnippetModal() {
        document.getElementById('snippetModal').style.display = 'none';
        document.getElementById('snippetForm').reset();
    }
    
    showAddGroupModal() {
        document.getElementById('groupModal').style.display = 'block';
    }
    
    closeGroupModal() {
        document.getElementById('groupModal').style.display = 'none';
        document.getElementById('groupForm').reset();
    }
    
    clearTerminal() {
        document.getElementById('terminalOutput').innerHTML = `
            <div class="terminal-line">
                <span class="prompt">$</span>
                <span class="command">Terminal cleared</span>
            </div>
        `;
    }
    
    saveTerminal() {
        const terminal = document.getElementById('terminalOutput').innerText;
        const blob = new Blob([terminal], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'terminal-output.txt';
        a.click();
        URL.revokeObjectURL(url);
        this.showNotification('Terminal output saved', 'success');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    logout() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('token');
        this.showAuthModal();
        this.showNotification('Logged out successfully', 'success');
    }
}

// Global functions for HTML onclick handlers
function showTab(tabName) {
    app.showTab(tabName);
}

function showAddConnectionModal() {
    app.showAddConnectionModal();
}

function closeConnectionModal() {
    app.closeConnectionModal();
}

function showAddSnippetModal() {
    app.showAddSnippetModal();
}

function closeSnippetModal() {
    app.closeSnippetModal();
}

function showAddGroupModal() {
    app.showAddGroupModal();
}

function closeGroupModal() {
    app.closeGroupModal();
}

function clearTerminal() {
    app.clearTerminal();
}

function saveTerminal() {
    app.saveTerminal();
}

function logout() {
    app.logout();
}

function closeAuthModal() {
    app.hideAuthModal();
}

function switchAuthForm() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const authTitle = document.getElementById('authTitle');
    const switchText = document.getElementById('switchText');
    const switchLink = document.getElementById('switchLink');
    
    if (loginForm.style.display === 'none') {
        // Show login form
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        authTitle.textContent = 'Login';
        switchText.textContent = "Don't have an account?";
        switchLink.textContent = 'Register';
    } else {
        // Show register form
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        authTitle.textContent = 'Register';
        switchText.textContent = 'Already have an account?';
        switchLink.textContent = 'Login';
    }
}

// Initialize the application
const app = new SSHClientApp(); 