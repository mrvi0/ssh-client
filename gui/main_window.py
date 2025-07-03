import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional
import json
import os

from .connection_manager import ConnectionManager
from .command_manager import CommandManager
from .terminal_frame import TerminalFrame
from models.database import DatabaseManager
from ssh.ssh_client import SSHClient


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.db_manager = DatabaseManager()
        self.ssh_client: Optional[SSHClient] = None
        self.current_connection: Optional[Dict[str, Any]] = None
        
        self.setup_window()
        self.setup_ui()
        self.setup_menu()
        
    def setup_window(self):
        """Setup the main window"""
        self.title("SSH Client - Professional Terminal")
        self.geometry("1400x900")
        self.minsize(1000, 600)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        self.configure(bg='#2b2b2b')
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='white')
        style.configure('TButton', background='#404040', foreground='white')
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top toolbar
        self.setup_toolbar(main_frame)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left panel - Connections and Groups
        left_panel = ttk.Frame(content_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self.setup_left_panel(left_panel)
        
        # Right panel - Terminal
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_right_panel(right_panel)
        
    def setup_toolbar(self, parent):
        """Setup the toolbar"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Connection status
        self.status_label = ttk.Label(toolbar, text="Ready", foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
        # Toolbar buttons
        ttk.Button(toolbar, text="New Connection", command=self.new_connection).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(toolbar, text="New Group", command=self.new_group).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(toolbar, text="Settings", command=self.open_settings).pack(side=tk.RIGHT, padx=(5, 0))
        
    def setup_left_panel(self, parent):
        """Setup the left panel with connections and groups"""
        # Notebook for tabs
        self.left_notebook = ttk.Notebook(parent)
        self.left_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Connections tab
        connections_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(connections_frame, text="Connections")
        
        self.connection_manager = ConnectionManager(connections_frame, self.on_connection_select)
        self.connection_manager.pack(fill=tk.BOTH, expand=True)
        
        # Groups tab (new)
        groups_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(groups_frame, text="Groups")
        
        self.setup_groups_tab(groups_frame)
        
        # Commands tab (now for command snippets)
        commands_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(commands_frame, text="Snippets")
        
        self.command_manager = CommandManager(commands_frame, self.on_snippet_select)
        self.command_manager.pack(fill=tk.BOTH, expand=True)
        
    def setup_groups_tab(self, parent):
        """Setup the groups tab"""
        # Groups list
        groups_list_frame = ttk.LabelFrame(parent, text="User Groups", padding=5)
        groups_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Treeview for groups
        columns = ("Name", "Members", "Connections")
        self.groups_tree = ttk.Treeview(groups_list_frame, columns=columns, show="tree headings", height=10)
        
        # Configure columns
        self.groups_tree.heading("#0", text="Group")
        self.groups_tree.column("#0", width=150)
        for col in columns:
            self.groups_tree.heading(col, text=col)
            self.groups_tree.column(col, width=100)
            
        # Scrollbar
        groups_scrollbar = ttk.Scrollbar(groups_list_frame, orient=tk.VERTICAL, command=self.groups_tree.yview)
        self.groups_tree.configure(yscrollcommand=groups_scrollbar.set)
        
        self.groups_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        groups_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Groups buttons
        groups_buttons_frame = ttk.Frame(parent)
        groups_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(groups_buttons_frame, text="Add Group", command=self.add_group).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(groups_buttons_frame, text="Edit Group", command=self.edit_group).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(groups_buttons_frame, text="Delete Group", command=self.delete_group).pack(side=tk.LEFT)
        
        # Load groups
        self.load_groups()
        
    def setup_right_panel(self, parent):
        """Setup the right panel with terminal"""
        # Terminal frame
        self.terminal_frame = TerminalFrame(parent, self.execute_ssh_command)
        self.terminal_frame.pack(fill=tk.BOTH, expand=True)
        
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Connection", command=self.new_connection)
        file_menu.add_command(label="New Group", command=self.new_group)
        file_menu.add_separator()
        file_menu.add_command(label="Import Connections", command=self.import_connections)
        file_menu.add_command(label="Export Connections", command=self.export_connections)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Settings", command=self.open_settings)
        edit_menu.add_command(label="Preferences", command=self.open_preferences)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Clear Terminal", command=self.clear_terminal)
        view_menu.add_command(label="Save Terminal Output", command=self.save_terminal_output)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        
    def on_connection_select(self, connection: Dict[str, Any]):
        """Handle connection selection"""
        self.current_connection = connection
        self.terminal_frame.set_connection(connection)
        self.status_label.config(text=f"Connected to: {connection['name']}", foreground="green")
        
        # Connect SSH
        self.connect_ssh(connection)
        
    def on_snippet_select(self, snippet: Dict[str, Any]):
        """Handle command snippet selection"""
        if self.current_connection:
            # Insert snippet into terminal
            self.terminal_frame.write_output(f"\n# Snippet: {snippet['name']}\n", "yellow")
            self.terminal_frame.write_output(f"{snippet['command']}\n", "cyan")
            # Execute the snippet
            self.execute_ssh_command(snippet['command'])
        else:
            messagebox.showwarning("No Connection", "Please select a connection first.")
            
    def connect_ssh(self, connection: Dict[str, Any]):
        """Connect to SSH server"""
        try:
            self.ssh_client = SSHClient()
            self.ssh_client.connect(connection)
            self.status_label.config(text=f"SSH Connected: {connection['name']}", foreground="green")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.status_label.config(text="Connection Failed", foreground="red")
            
    def execute_ssh_command(self, command: str) -> str:
        """Execute SSH command and return result"""
        if not self.ssh_client:
            return "Error: No SSH connection"
            
        try:
            result = self.ssh_client.execute_command(command)
            return result
        except Exception as e:
            return f"Error: {str(e)}"
            
    def new_connection(self):
        """Open new connection dialog"""
        self.connection_manager.add_connection()
        
    def new_group(self):
        """Open new group dialog"""
        self.add_group()
        
    def add_group(self):
        """Add a new group"""
        dialog = GroupDialog(self, "Add Group")
        if dialog.result:
            group_data = dialog.result
            # Save to database
            self.db_manager.add_group(group_data)
            self.load_groups()
            
    def edit_group(self):
        """Edit selected group"""
        selection = self.groups_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a group to edit.")
            return
            
        group_id = selection[0]
        group_data = self.db_manager.get_group(group_id)
        if group_data:
            dialog = GroupDialog(self, "Edit Group", group_data)
            if dialog.result:
                # Update in database
                self.db_manager.update_group(group_id, dialog.result)
                self.load_groups()
                
    def delete_group(self):
        """Delete selected group"""
        selection = self.groups_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a group to delete.")
            return
            
        group_id = selection[0]
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this group?"):
            self.db_manager.delete_group(group_id)
            self.load_groups()
            
    def load_groups(self):
        """Load groups from database"""
        # Clear existing items
        for item in self.groups_tree.get_children():
            self.groups_tree.delete(item)
            
        # Load groups
        groups = self.db_manager.get_all_groups()
        for group in groups:
            self.groups_tree.insert("", "end", group['id'], text=group['name'], 
                                  values=(group['name'], len(group.get('members', [])), 
                                         len(group.get('connections', []))))
                                         
    def open_settings(self):
        """Open settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog will be implemented.")
        
    def open_preferences(self):
        """Open preferences dialog"""
        messagebox.showinfo("Preferences", "Preferences dialog will be implemented.")
        
    def clear_terminal(self):
        """Clear the terminal"""
        self.terminal_frame.clear_terminal()
        
    def save_terminal_output(self):
        """Save terminal output to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.terminal_frame.save_output(filename)
            
    def import_connections(self):
        """Import connections from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    connections = json.load(f)
                # Import connections
                for conn in connections:
                    self.db_manager.add_connection(conn)
                self.connection_manager.load_connections()
                messagebox.showinfo("Import", f"Imported {len(connections)} connections.")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import: {str(e)}")
                
    def export_connections(self):
        """Export connections to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                connections = self.db_manager.get_all_connections()
                with open(filename, 'w') as f:
                    json.dump(connections, f, indent=2)
                messagebox.showinfo("Export", f"Exported {len(connections)} connections.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
                
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", "SSH Client v1.0\nProfessional SSH terminal client")
        
    def show_documentation(self):
        """Show documentation"""
        messagebox.showinfo("Documentation", "Documentation will be available online.")
        
    def on_closing(self):
        """Handle window closing"""
        if self.ssh_client:
            self.ssh_client.close()
        if hasattr(self.terminal_frame, 'cleanup'):
            self.terminal_frame.cleanup()
        self.db_manager.close()
        self.quit()


class GroupDialog:
    def __init__(self, parent, title, group_data=None):
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui(group_data)
        
        # Wait for dialog to close
        parent.wait_window(self.dialog)
        
    def setup_ui(self, group_data):
        """Setup the dialog UI"""
        # Group name
        ttk.Label(self.dialog, text="Group Name:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.name_entry = ttk.Entry(self.dialog, width=40)
        self.name_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Description
        ttk.Label(self.dialog, text="Description:").pack(anchor=tk.W, padx=10, pady=(0, 5))
        self.desc_text = tk.Text(self.dialog, height=3, width=40)
        self.desc_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Members
        ttk.Label(self.dialog, text="Members (one per line):").pack(anchor=tk.W, padx=10, pady=(0, 5))
        self.members_text = tk.Text(self.dialog, height=5, width=40)
        self.members_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT)
        
        # Load existing data
        if group_data:
            self.name_entry.insert(0, group_data.get('name', ''))
            self.desc_text.insert('1.0', group_data.get('description', ''))
            self.members_text.insert('1.0', '\n'.join(group_data.get('members', [])))
            
    def save(self):
        """Save the group data"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Group name is required.")
            return
            
        description = self.desc_text.get('1.0', tk.END).strip()
        members = [m.strip() for m in self.members_text.get('1.0', tk.END).split('\n') if m.strip()]
        
        self.result = {
            'name': name,
            'description': description,
            'members': members,
            'connections': []
        }
        
        self.dialog.destroy()
        
    def cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy() 