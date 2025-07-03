import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Optional, Dict, Any
import json
import os

from models.database import DatabaseManager
from ssh.ssh_client import SSHClient
from gui.connection_manager import ConnectionManagerFrame
from gui.command_manager import CommandManagerFrame
from gui.terminal_frame import TerminalFrame


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SSH Client")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Current connection state
        self.current_connection: Optional[Dict[str, Any]] = None
        self.ssh_client: Optional[SSHClient] = None
        
        self.setup_ui()
        self.setup_menu()
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Connections tab
        self.connection_frame = ConnectionManagerFrame(
            self.notebook, 
            self.db_manager,
            self.on_connection_selected
        )
        self.notebook.add(self.connection_frame, text="Connections")
        
        # Commands tab
        self.command_frame = CommandManagerFrame(
            self.notebook,
            self.db_manager
        )
        self.notebook.add(self.command_frame, text="Commands")
        
        # Terminal tab
        self.terminal_frame = TerminalFrame(
            self.notebook,
            self.on_ssh_command
        )
        self.notebook.add(self.terminal_frame, text="Terminal")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_menu(self):
        """Setup application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import Connections", command=self.import_connections)
        file_menu.add_command(label="Export Connections", command=self.export_connections)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self.show_preferences)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def on_connection_selected(self, connection: Dict[str, Any]):
        """Handle connection selection"""
        self.current_connection = connection
        self.status_var.set(f"Selected: {connection['name']} ({connection['host']}:{connection['port']})")
        
        # Enable terminal tab
        self.terminal_frame.set_connection(connection)
        
    def on_ssh_command(self, command: str):
        """Handle SSH command execution"""
        if not self.current_connection:
            messagebox.showerror("Error", "No connection selected")
            return
            
        if not self.ssh_client or not self.ssh_client.is_connected():
            # Connect first
            self.connect_to_server()
            
        if self.ssh_client and self.ssh_client.is_connected():
            try:
                result = self.ssh_client.execute_command(command)
                self.terminal_frame.append_output(f"$ {command}\n{result}\n")
            except Exception as e:
                self.terminal_frame.append_output(f"Error: {str(e)}\n")
                
    def connect_to_server(self):
        """Connect to the selected server"""
        if not self.current_connection:
            return
            
        try:
            self.ssh_client = SSHClient()
            self.ssh_client.connect(
                hostname=self.current_connection['host'],
                port=self.current_connection['port'],
                username=self.current_connection['username'],
                password=self.current_connection.get('password'),
                key_path=self.current_connection.get('key_path')
            )
            self.status_var.set(f"Connected to {self.current_connection['name']}")
            self.terminal_frame.append_output("Connected to server\n")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.status_var.set("Connection failed")
            
    def disconnect_from_server(self):
        """Disconnect from current server"""
        if self.ssh_client:
            self.ssh_client.disconnect()
            self.ssh_client = None
            self.status_var.set("Disconnected")
            self.terminal_frame.append_output("Disconnected from server\n")
            
    def import_connections(self):
        """Import connections from JSON file"""
        filename = filedialog.askopenfilename(
            title="Import Connections",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    connections = json.load(f)
                    
                for conn in connections:
                    self.db_manager.add_connection(**conn)
                    
                self.connection_frame.refresh_connections()
                messagebox.showinfo("Success", f"Imported {len(connections)} connections")
            except Exception as e:
                messagebox.showerror("Import Error", str(e))
                
    def export_connections(self):
        """Export connections to JSON file"""
        filename = filedialog.asksaveasfilename(
            title="Export Connections",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                connections = self.db_manager.get_all_connections()
                with open(filename, 'w') as f:
                    json.dump(connections, f, indent=2)
                messagebox.showinfo("Success", f"Exported {len(connections)} connections")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
                
    def show_preferences(self):
        """Show preferences dialog"""
        # TODO: Implement preferences dialog
        messagebox.showinfo("Preferences", "Preferences dialog not implemented yet")
        
    def show_about(self):
        """Show about dialog"""
        about_text = """SSH Client v1.0

A simple SSH client application with local data storage.

Features:
- Local connection management
- Command templates
- Terminal interface
- Encrypted data storage

Built with Python and tkinter"""
        messagebox.showinfo("About", about_text)
        
    def run(self):
        """Start the application"""
        self.root.mainloop()
        
    def cleanup(self):
        """Cleanup resources before exit"""
        if self.ssh_client:
            self.ssh_client.disconnect()
        self.db_manager.close() 