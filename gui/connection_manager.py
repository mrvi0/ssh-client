import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional
from models.database import DatabaseManager


class ConnectionManager(ttk.Frame):
    def __init__(self, parent, on_connection_select: Callable):
        super().__init__(parent)
        self.on_connection_select = on_connection_select
        self.db_manager = DatabaseManager()
        self.setup_ui()
        self.load_connections()
        
    def setup_ui(self):
        """Setup the connection manager UI"""
        # Connections list
        list_frame = ttk.LabelFrame(self, text="Connections", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Treeview for connections
        columns = ("Host", "Port", "Username", "Description")
        self.connections_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=10)
        
        # Configure columns
        self.connections_tree.heading("#0", text="Name")
        self.connections_tree.column("#0", width=150)
        for col in columns:
            self.connections_tree.heading(col, text=col)
            self.connections_tree.column(col, width=100)
            
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.connections_tree.yview)
        self.connections_tree.configure(yscrollcommand=scrollbar.set)
        
        self.connections_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event
        self.connections_tree.bind("<Double-1>", self.on_connection_double_click)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="Add", command=self.add_connection).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Edit", command=self.edit_connection).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete", command=self.delete_connection).pack(side=tk.LEFT)
        
    def load_connections(self):
        """Load connections from database"""
        # Clear existing items
        for item in self.connections_tree.get_children():
            self.connections_tree.delete(item)
            
        # Load connections
        connections = self.db_manager.get_all_connections()
        for conn in connections:
            self.connections_tree.insert("", "end", conn['id'], text=conn['name'], 
                                       values=(conn['host'], conn['port'], conn['username'], 
                                              conn.get('description', '')))
                                              
    def add_connection(self):
        """Add a new connection"""
        dialog = ConnectionDialog(self, "Add Connection")
        if dialog.result:
            connection_data = dialog.result
            # Save to database
            self.db_manager.add_connection(connection_data)
            self.load_connections()
            
    def edit_connection(self):
        """Edit selected connection"""
        selection = self.connections_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a connection to edit.")
            return
            
        connection_id = selection[0]
        connection_data = self.db_manager.get_connection(connection_id)
        if connection_data:
            dialog = ConnectionDialog(self, "Edit Connection", connection_data)
            if dialog.result:
                # Update in database
                self.db_manager.update_connection(connection_id, dialog.result)
                self.load_connections()
                
    def delete_connection(self):
        """Delete selected connection"""
        selection = self.connections_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a connection to delete.")
            return
            
        connection_id = selection[0]
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this connection?"):
            self.db_manager.delete_connection(connection_id)
            self.load_connections()
            
    def on_connection_double_click(self, event):
        """Handle double-click on connection"""
        selection = self.connections_tree.selection()
        if selection:
            connection_id = selection[0]
            connection_data = self.db_manager.get_connection(connection_id)
            if connection_data:
                self.on_connection_select(connection_data)


class ConnectionDialog:
    def __init__(self, parent, title, connection_data=None):
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui(connection_data)
        
        # Wait for dialog to close
        parent.wait_window(self.dialog)
        
    def setup_ui(self, connection_data):
        """Setup the dialog UI"""
        # Connection name
        ttk.Label(self.dialog, text="Connection Name:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.name_entry = ttk.Entry(self.dialog, width=40)
        self.name_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Host
        ttk.Label(self.dialog, text="Host:").pack(anchor=tk.W, padx=10, pady=(0, 5))
        self.host_entry = ttk.Entry(self.dialog, width=40)
        self.host_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Port
        ttk.Label(self.dialog, text="Port:").pack(anchor=tk.W, padx=10, pady=(0, 5))
        self.port_entry = ttk.Entry(self.dialog, width=40)
        self.port_entry.insert(0, "22")
        self.port_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Username
        ttk.Label(self.dialog, text="Username:").pack(anchor=tk.W, padx=10, pady=(0, 5))
        self.username_entry = ttk.Entry(self.dialog, width=40)
        self.username_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Authentication method
        auth_frame = ttk.LabelFrame(self.dialog, text="Authentication", padding=10)
        auth_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.auth_method = tk.StringVar(value="password")
        ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_method, 
                       value="password", command=self.on_auth_method_change).pack(anchor=tk.W)
        ttk.Radiobutton(auth_frame, text="Private Key", variable=self.auth_method, 
                       value="key", command=self.on_auth_method_change).pack(anchor=tk.W)
        
        # Password frame
        self.password_frame = ttk.Frame(auth_frame)
        self.password_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(self.password_frame, text="Password:").pack(anchor=tk.W)
        self.password_entry = ttk.Entry(self.password_frame, width=40, show="*")
        self.password_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Key frame
        self.key_frame = ttk.Frame(auth_frame)
        ttk.Label(self.key_frame, text="Private Key Path:").pack(anchor=tk.W)
        key_input_frame = ttk.Frame(self.key_frame)
        key_input_frame.pack(fill=tk.X, pady=(5, 0))
        self.key_entry = ttk.Entry(key_input_frame, width=30)
        self.key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(key_input_frame, text="Browse", command=self.browse_key_file).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Description
        ttk.Label(self.dialog, text="Description:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.desc_text = tk.Text(self.dialog, height=3, width=40)
        self.desc_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT)
        
        # Load existing data
        if connection_data:
            self.name_entry.insert(0, connection_data.get('name', ''))
            self.host_entry.insert(0, connection_data.get('host', ''))
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, str(connection_data.get('port', 22)))
            self.username_entry.insert(0, connection_data.get('username', ''))
            self.desc_text.insert('1.0', connection_data.get('description', ''))
            
            # Set authentication method
            if connection_data.get('key_path'):
                self.auth_method.set("key")
                self.key_entry.insert(0, connection_data.get('key_path', ''))
            else:
                self.auth_method.set("password")
                self.password_entry.insert(0, connection_data.get('password', ''))
                
        # Initialize auth method display
        self.on_auth_method_change()
        
    def on_auth_method_change(self):
        """Handle authentication method change"""
        if self.auth_method.get() == "password":
            self.password_frame.pack(fill=tk.X, pady=(5, 0))
            self.key_frame.pack_forget()
        else:
            self.password_frame.pack_forget()
            self.key_frame.pack(fill=tk.X, pady=(5, 0))
            
    def browse_key_file(self):
        """Browse for private key file"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select Private Key File",
            filetypes=[("All files", "*.*"), ("PEM files", "*.pem"), ("Key files", "*.key")]
        )
        if filename:
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, filename)
            
    def save(self):
        """Save the connection data"""
        name = self.name_entry.get().strip()
        host = self.host_entry.get().strip()
        port = self.port_entry.get().strip()
        username = self.username_entry.get().strip()
        
        if not all([name, host, port, username]):
            messagebox.showwarning("Validation", "Please fill in all required fields.")
            return
            
        try:
            port = int(port)
        except ValueError:
            messagebox.showwarning("Validation", "Port must be a number.")
            return
            
        # Get authentication data
        password = None
        key_path = None
        
        if self.auth_method.get() == "password":
            password = self.password_entry.get()
            if not password:
                messagebox.showwarning("Validation", "Password is required.")
                return
        else:
            key_path = self.key_entry.get().strip()
            if not key_path:
                messagebox.showwarning("Validation", "Private key path is required.")
                return
                
        description = self.desc_text.get('1.0', tk.END).strip()
        
        self.result = {
            'name': name,
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'key_path': key_path,
            'description': description
        }
        
        self.dialog.destroy()
        
    def cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy() 