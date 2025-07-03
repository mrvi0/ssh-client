import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable
import json


class ConnectionManagerFrame(ttk.Frame):
    def __init__(self, parent, db_manager, on_connection_selected: Callable):
        super().__init__(parent)
        self.db_manager = db_manager
        self.on_connection_selected = on_connection_selected
        self.setup_ui()
        self.refresh_connections()
        
    def setup_ui(self):
        """Setup the connection manager interface"""
        # Left panel - connection list
        left_panel = ttk.Frame(self)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Connection list header
        list_header = ttk.Frame(left_panel)
        list_header.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(list_header, text="Connections", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Buttons frame
        buttons_frame = ttk.Frame(list_header)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="Add", command=self.add_connection).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Edit", command=self.edit_connection).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Delete", command=self.delete_connection).pack(side=tk.LEFT, padx=2)
        
        # Connection list
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for connections
        columns = ("Name", "Host", "Port", "Username")
        self.connection_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        for col in columns:
            self.connection_tree.heading(col, text=col)
            self.connection_tree.column(col, width=100)
            
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.connection_tree.yview)
        self.connection_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.connection_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event
        self.connection_tree.bind("<Double-1>", self.on_connection_double_click)
        
        # Right panel - connection details
        right_panel = ttk.Frame(self)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Details header
        ttk.Label(right_panel, text="Connection Details", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Details frame
        details_frame = ttk.LabelFrame(right_panel, text="Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Connection details labels
        self.detail_labels = {}
        detail_fields = [
            ("Name", "name"),
            ("Host", "host"),
            ("Port", "port"),
            ("Username", "username"),
            ("Key Path", "key_path"),
            ("Description", "description")
        ]
        
        for i, (label_text, field_name) in enumerate(detail_fields):
            ttk.Label(details_frame, text=f"{label_text}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            label = ttk.Label(details_frame, text="", foreground="gray")
            label.grid(row=i, column=1, sticky=tk.W, pady=2, padx=(10, 0))
            self.detail_labels[field_name] = label
            
        # Test connection button
        test_frame = ttk.Frame(right_panel)
        test_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(test_frame, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT)
        ttk.Button(test_frame, text="Connect", command=self.connect_to_selected).pack(side=tk.LEFT, padx=(5, 0))
        
    def refresh_connections(self):
        """Refresh the connection list"""
        # Clear existing items
        for item in self.connection_tree.get_children():
            self.connection_tree.delete(item)
            
        # Get connections from database
        try:
            connections = self.db_manager.get_all_connections()
            for conn in connections:
                self.connection_tree.insert("", tk.END, values=(
                    conn.get('name', ''),
                    conn.get('host', ''),
                    conn.get('port', ''),
                    conn.get('username', '')
                ), tags=(conn.get('id'),))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load connections: {str(e)}")
            
    def on_connection_double_click(self, event):
        """Handle double-click on connection"""
        selection = self.connection_tree.selection()
        if selection:
            item = selection[0]
            conn_id = self.connection_tree.item(item, "tags")[0]
            connection = self.db_manager.get_connection(conn_id)
            if connection:
                self.show_connection_details(connection)
                self.on_connection_selected(connection)
                
    def show_connection_details(self, connection: Dict[str, Any]):
        """Show connection details in the right panel"""
        for field_name, label in self.detail_labels.items():
            value = connection.get(field_name, '')
            if field_name == 'password':
                value = '*' * len(value) if value else ''
            label.config(text=str(value))
            
    def add_connection(self):
        """Add a new connection"""
        dialog = ConnectionDialog(self, "Add Connection")
        if dialog.result:
            try:
                self.db_manager.add_connection(**dialog.result)
                self.refresh_connections()
                messagebox.showinfo("Success", "Connection added successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add connection: {str(e)}")
                
    def edit_connection(self):
        """Edit selected connection"""
        selection = self.connection_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a connection to edit")
            return
            
        item = selection[0]
        conn_id = self.connection_tree.item(item, "tags")[0]
        connection = self.db_manager.get_connection(conn_id)
        
        if connection:
            dialog = ConnectionDialog(self, "Edit Connection", connection)
            if dialog.result:
                try:
                    self.db_manager.update_connection(conn_id, **dialog.result)
                    self.refresh_connections()
                    messagebox.showinfo("Success", "Connection updated successfully")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update connection: {str(e)}")
                    
    def delete_connection(self):
        """Delete selected connection"""
        selection = self.connection_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a connection to delete")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this connection?"):
            item = selection[0]
            conn_id = self.connection_tree.item(item, "tags")[0]
            try:
                self.db_manager.delete_connection(conn_id)
                self.refresh_connections()
                messagebox.showinfo("Success", "Connection deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete connection: {str(e)}")
                
    def test_connection(self):
        """Test the selected connection"""
        selection = self.connection_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a connection to test")
            return
            
        item = selection[0]
        conn_id = self.connection_tree.item(item, "tags")[0]
        connection = self.db_manager.get_connection(conn_id)
        
        if connection:
            # TODO: Implement actual connection test
            messagebox.showinfo("Test Connection", "Connection test not implemented yet")
            
    def connect_to_selected(self):
        """Connect to the selected connection"""
        selection = self.connection_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a connection")
            return
            
        item = selection[0]
        conn_id = self.connection_tree.item(item, "tags")[0]
        connection = self.db_manager.get_connection(conn_id)
        
        if connection:
            self.on_connection_selected(connection)


class ConnectionDialog:
    def __init__(self, parent, title, connection=None):
        self.result = None
        self.connection = connection or {}
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.setup_ui()
        self.load_connection_data()
        
        # Wait for dialog to close
        parent.wait_window(self.dialog)
        
    def setup_ui(self):
        """Setup the dialog interface"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        fields = [
            ("Name", "name"),
            ("Host", "host"),
            ("Port", "port"),
            ("Username", "username"),
            ("Password", "password", True),  # Password field
            ("Key Path", "key_path"),
            ("Description", "description")
        ]
        
        self.entries = {}
        for i, field_info in enumerate(fields):
            label_text = field_info[0]
            field_name = field_info[1]
            is_password = len(field_info) > 2 and field_info[2]
            
            ttk.Label(main_frame, text=f"{label_text}:").grid(row=i, column=0, sticky=tk.W, pady=5)
            
            if is_password:
                entry = ttk.Entry(main_frame, show="*")
            else:
                entry = ttk.Entry(main_frame)
                
            entry.grid(row=i, column=1, sticky="ew", pady=5, padx=(10, 0))
            self.entries[field_name] = entry
            
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT)
        
    def load_connection_data(self):
        """Load existing connection data into form"""
        if self.connection:
            for field_name, entry in self.entries.items():
                value = self.connection.get(field_name, '')
                entry.insert(0, str(value))
                
    def save(self):
        """Save the connection data"""
        data = {}
        for field_name, entry in self.entries.items():
            value = entry.get().strip()
            if field_name == 'port':
                try:
                    value = int(value) if value else 22
                except ValueError:
                    messagebox.showerror("Error", "Port must be a number")
                    return
            data[field_name] = value
            
        # Validate required fields
        if not data.get('name'):
            messagebox.showerror("Error", "Name is required")
            return
        if not data.get('host'):
            messagebox.showerror("Error", "Host is required")
            return
        if not data.get('username'):
            messagebox.showerror("Error", "Username is required")
            return
            
        self.result = data
        self.dialog.destroy()
        
    def cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy() 