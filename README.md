# SSH Client - Professional Terminal

A modern, professional SSH client application with both desktop and web interfaces. Features a terminal-like interface, user groups, command snippets, and comprehensive admin controls.

## 🚀 Features

### Desktop Application
- **Real Terminal Interface**: Command input directly in terminal window
- **SSH Connection Management**: Secure storage with encryption
- **Command History**: Navigate through command history with arrow keys
- **Auto-completion**: Tab completion for common commands
- **User Groups**: Organize connections by teams/users
- **Command Snippets**: Reusable command templates
- **File Transfer**: Upload/download files via SFTP
- **Directory Browsing**: Browse remote file systems
- **Local Storage**: All data stored locally with encryption

### Web Application
- **User Authentication**: JWT-based authentication with bcrypt
- **Admin Panel**: Comprehensive admin dashboard
- **User Groups**: Create and manage user groups
- **Connection Sharing**: Share connections within groups
- **Command Snippets**: Create and share command templates
- **Real-time Updates**: WebSocket support for live updates
- **Responsive Design**: Modern UI that works on all devices

### Security Features
- **Encrypted Storage**: All sensitive data encrypted with Fernet
- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt for secure password storage
- **Admin Access Control**: Role-based access control
- **Environment Configuration**: Secure configuration management

## 🏗️ Architecture

### Desktop App (Python/Tkinter)
```
ssh-client/
├── main.py                 # Desktop app entry point
├── gui/                    # GUI components
│   ├── main_window.py     # Main application window
│   ├── terminal_frame.py  # Terminal interface
│   ├── connection_manager.py  # Connection management
│   └── command_manager.py # Command snippets
├── ssh/                   # SSH functionality
│   └── ssh_client.py      # SSH client implementation
├── models/                # Data models
│   └── database.py        # Database operations
└── utils/                 # Utilities
    ├── encryption.py      # Encryption utilities
    └── config.py          # Configuration management
```

### Web App (Flask/JavaScript)
```
ssh-client/
├── app.py                 # Web server
├── templates/             # HTML templates
│   └── index.html        # Main web interface
├── static/               # Static assets
│   ├── css/style.css     # Modern styling
│   └── js/app.js         # Frontend logic
└── config.py             # Configuration settings
```

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip
- tkinter (usually included with Python)

### Desktop Application
```bash
# Clone the repository
git clone <repository-url>
cd ssh-client

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Web Application
```bash
# Install web dependencies
pip install -r requirements_web.txt

# Set environment variables (optional)
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=secure_password
export SECRET_KEY=your-secret-key

# Run the web server
python app.py
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file or set environment variables:

```bash
# Admin Settings
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@localhost
ADMIN_PASSWORD=admin123
ADMIN_ENABLED=True

# Security
SECRET_KEY=your-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# Web Server
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=True

# SSH Settings
SSH_TIMEOUT=30
SSH_MAX_CONNECTIONS=10
```

## 🎯 Usage

### Desktop Application

1. **Adding Connections**
   - Click "New Connection" in the toolbar
   - Fill in connection details (host, port, username)
   - Choose authentication method (password or private key)
   - Save the connection

2. **Using the Terminal**
   - Select a connection from the left panel
   - Type commands directly in the terminal
   - Use arrow keys to navigate command history
   - Press Tab for auto-completion

3. **Managing Groups**
   - Switch to "Groups" tab
   - Create user groups for organizing connections
   - Add members and assign connections

4. **Command Snippets**
   - Switch to "Snippets" tab
   - Create reusable command templates
   - Double-click to execute snippets

### Web Application

1. **Authentication**
   - Register a new account or login
   - Admin users get additional privileges

2. **Admin Panel**
   - View system statistics
   - Manage user groups
   - Monitor connections and usage

3. **Connection Management**
   - Add, edit, and delete connections
   - Share connections within groups
   - View connection history

## 🔒 Security

### Data Encryption
- All sensitive data (passwords, keys) are encrypted using Fernet
- Encryption keys are stored securely
- Database is encrypted at rest

### Authentication
- JWT tokens for web authentication
- bcrypt password hashing
- Token expiration and refresh

### Access Control
- Role-based access control
- Admin-only features protected
- Secure API endpoints

## 🧪 Testing

### Desktop App Testing
```bash
# Run the desktop application
python main.py

# Test SSH connections
# Test command execution
# Test file transfers
```

### Web App Testing
```bash
# Start the web server
python app.py

# Open browser to http://localhost:5000
# Test user registration/login
# Test admin functionality
# Test API endpoints
```

## 🚀 Development

### Project Structure
```
ssh-client/
├── main.py                 # Desktop app entry point
├── app.py                  # Web app entry point
├── config.py               # Configuration settings
├── requirements.txt        # Desktop dependencies
├── requirements_web.txt    # Web dependencies
├── gui/                    # Desktop GUI
├── ssh/                    # SSH functionality
├── models/                 # Data models
├── utils/                  # Utilities
├── templates/              # Web templates
├── static/                 # Web assets
└── instance/               # Database and config files
```

### Adding Features
1. Follow the existing code structure
2. Use conventional commits for version control
3. Test both desktop and web interfaces
4. Update documentation

### Conventional Commits
This project uses conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code examples

## 🔄 Roadmap

### Planned Features
- [ ] Multi-factor authentication
- [ ] SSH key management
- [ ] Connection tunneling
- [ ] Session recording
- [ ] Plugin system
- [ ] Mobile app
- [ ] Cloud sync
- [ ] Advanced terminal features

### Known Issues
- Some terminal features may not work on all platforms
- Web interface requires modern browser
- Large file transfers may timeout

---

**SSH Client** - Professional terminal management made simple and secure. 