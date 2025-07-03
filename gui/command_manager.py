import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional
from models.database import DatabaseManager


class CommandManager(ttk.Frame):
    def __init__(self, parent, on_snippet_select: Callable):
        super().__init__(parent)
        self.on_snippet_select = on_snippet_select
        self.db_manager = DatabaseManager()
        self.setup_ui()
        self.load_commands()
        
    def setup_ui(self):
        """Setup the command manager UI"""
        # Commands list
        list_frame = ttk.LabelFrame(self, text="Command Snippets", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Treeview for commands
        columns = ("Category", "Description")
        self.commands_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=10)
        
        # Configure columns
        self.commands_tree.heading("#0", text="Name")
        self.commands_tree.column("#0", width=150)
        for col in columns:
            self.commands_tree.heading(col, text=col)
            self.commands_tree.column(col, width=120)
            
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.commands_tree.yview)
        self.commands_tree.configure(yscrollcommand=scrollbar.set)
        
        self.commands_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event
        self.commands_tree.bind("<Double-1>", self.on_command_double_click)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="Add", command=self.add_command).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Edit", command=self.edit_command).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete", command=self.delete_command).pack(side=tk.LEFT)
        
    def load_commands(self):
        """Load commands from database"""
        # Clear existing items
        for item in self.commands_tree.get_children():
            self.commands_tree.delete(item)
            
        # Load commands
        commands = self.db_manager.get_all_commands()
        for cmd in commands:
            self.commands_tree.insert("", "end", cmd['id'], text=cmd['name'], 
                                    values=(cmd.get('category', 'General'), 
                                           cmd.get('description', '')))
                                           
    def add_command(self):
        """Add a new command snippet"""
        dialog = CommandDialog(self, "Add Command Snippet")
        if dialog.result:
            command_data = dialog.result
            # Save to database
            self.db_manager.add_command(command_data)
            self.load_commands()
            
    def edit_command(self):
        """Edit selected command"""
        selection = self.commands_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a command to edit.")
            return
            
        command_id = selection[0]
        command_data = self.db_manager.get_command(command_id)
        if command_data:
            dialog = CommandDialog(self, "Edit Command Snippet", command_data)
            if dialog.result:
                # Update in database
                self.db_manager.update_command(command_id, dialog.result)
                self.load_commands()
                
    def delete_command(self):
        """Delete selected command"""
        selection = self.commands_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a command to delete.")
            return
            
        command_id = selection[0]
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this command?"):
            self.db_manager.delete_command(command_id)
            self.load_commands()
            
    def on_command_double_click(self, event):
        """Handle double-click on command"""
        selection = self.commands_tree.selection()
        if selection:
            command_id = selection[0]
            command_data = self.db_manager.get_command(command_id)
            if command_data:
                self.on_snippet_select(command_data)


class CommandDialog:
    def __init__(self, parent, title, command_data=None):
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui(command_data)
        
        # Wait for dialog to close
        parent.wait_window(self.dialog)
        
    def setup_ui(self, command_data):
        """Setup the dialog UI"""
        # Command name
        ttk.Label(self.dialog, text="Snippet Name:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.name_entry = ttk.Entry(self.dialog, width=50)
        self.name_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Category
        ttk.Label(self.dialog, text="Category:").pack(anchor=tk.W, padx=10, pady=(0, 5))
        self.category_entry = ttk.Entry(self.dialog, width=50)
        self.category_entry.insert(0, "General")
        self.category_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Command
        ttk.Label(self.dialog, text="Command:").pack(anchor=tk.W, padx=10, pady=(0, 5))
        self.command_text = tk.Text(self.dialog, height=6, width=50)
        self.command_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Quick command buttons
        quick_frame = ttk.LabelFrame(self.dialog, text="Quick Commands", padding=5)
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        quick_commands = [
            ("ls -la", "List files"),
            ("pwd", "Current directory"),
            ("whoami", "Current user"),
            ("df -h", "Disk usage"),
            ("ps aux", "All processes"),
            ("top", "System monitor"),
            ("cat", "View file"),
            ("grep", "Search text"),
            ("find", "Find files"),
            ("tar", "Archive files")
        ]
        
        for i, (command, description) in enumerate(quick_commands):
            btn = ttk.Button(
                quick_frame, 
                text=f"{description}",
                command=lambda cmd=command: self.insert_command(cmd)
            )
            btn.grid(row=i//5, column=i%5, sticky="ew", padx=2, pady=2)
            
        # Configure grid weights
        for i in range(5):
            quick_frame.columnconfigure(i, weight=1)
            
        # Description
        ttk.Label(self.dialog, text="Description:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.desc_text = tk.Text(self.dialog, height=3, width=50)
        self.desc_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT)
        
        # Load existing data
        if command_data:
            self.name_entry.insert(0, command_data.get('name', ''))
            self.category_entry.delete(0, tk.END)
            self.category_entry.insert(0, command_data.get('category', 'General'))
            self.command_text.insert('1.0', command_data.get('command', ''))
            self.desc_text.insert('1.0', command_data.get('description', ''))
            
    def insert_command(self, command: str):
        """Insert a quick command into the command text"""
        self.command_text.insert(tk.INSERT, command)
        
    def save(self):
        """Save the command data"""
        name = self.name_entry.get().strip()
        category = self.category_entry.get().strip()
        command = self.command_text.get('1.0', tk.END).strip()
        description = self.desc_text.get('1.0', tk.END).strip()
        
        if not all([name, command]):
            messagebox.showwarning("Validation", "Name and command are required.")
            return
            
        if not category:
            category = "General"
            
        self.result = {
            'name': name,
            'command': command,
            'category': category,
            'description': description
        }
        
        self.dialog.destroy()
        
    def cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy() 