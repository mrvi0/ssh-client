import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable


class CommandManagerFrame(ttk.Frame):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
        self.refresh_commands()
        
    def setup_ui(self):
        """Setup the command manager interface"""
        # Left panel - command list
        left_panel = ttk.Frame(self)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Command list header
        list_header = ttk.Frame(left_panel)
        list_header.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(list_header, text="Commands", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Buttons frame
        buttons_frame = ttk.Frame(list_header)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="Add", command=self.add_command).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Edit", command=self.edit_command).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Delete", command=self.delete_command).pack(side=tk.LEFT, padx=2)
        
        # Command list
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for commands
        columns = ("Name", "Command", "Category")
        self.command_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        for col in columns:
            self.command_tree.heading(col, text=col)
            self.command_tree.column(col, width=150)
            
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.command_tree.yview)
        self.command_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.command_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event
        self.command_tree.bind("<Double-1>", self.on_command_double_click)
        
        # Right panel - command details
        right_panel = ttk.Frame(self)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Details header
        ttk.Label(right_panel, text="Command Details", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Details frame
        details_frame = ttk.LabelFrame(right_panel, text="Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Command details labels
        self.detail_labels = {}
        detail_fields = [
            ("Name", "name"),
            ("Command", "command"),
            ("Category", "category"),
            ("Description", "description"),
            ("Arguments", "arguments")
        ]
        
        for i, (label_text, field_name) in enumerate(detail_fields):
            ttk.Label(details_frame, text=f"{label_text}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            label = ttk.Label(details_frame, text="", foreground="gray", wraplength=300)
            label.grid(row=i, column=1, sticky=tk.W, pady=2, padx=(10, 0))
            self.detail_labels[field_name] = label
            
        # Execute button
        execute_frame = ttk.Frame(right_panel)
        execute_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(execute_frame, text="Execute Command", command=self.execute_command).pack(side=tk.LEFT)
        
    def refresh_commands(self):
        """Refresh the command list"""
        # Clear existing items
        for item in self.command_tree.get_children():
            self.command_tree.delete(item)
            
        # Get commands from database
        try:
            commands = self.db_manager.get_all_commands()
            for cmd in commands:
                self.command_tree.insert("", tk.END, values=(
                    cmd.get('name', ''),
                    cmd.get('command', ''),
                    cmd.get('category', '')
                ), tags=(cmd.get('id'),))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load commands: {str(e)}")
            
    def on_command_double_click(self, event):
        """Handle double-click on command"""
        selection = self.command_tree.selection()
        if selection:
            item = selection[0]
            cmd_id = self.command_tree.item(item, "tags")[0]
            command = self.db_manager.get_command(cmd_id)
            if command:
                self.show_command_details(command)
                
    def show_command_details(self, command: Dict[str, Any]):
        """Show command details in the right panel"""
        for field_name, label in self.detail_labels.items():
            value = command.get(field_name, '')
            label.config(text=str(value))
            
    def add_command(self):
        """Add a new command"""
        dialog = CommandDialog(self, "Add Command")
        if dialog.result:
            try:
                self.db_manager.add_command(**dialog.result)
                self.refresh_commands()
                messagebox.showinfo("Success", "Command added successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add command: {str(e)}")
                
    def edit_command(self):
        """Edit selected command"""
        selection = self.command_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a command to edit")
            return
            
        item = selection[0]
        cmd_id = self.command_tree.item(item, "tags")[0]
        command = self.db_manager.get_command(cmd_id)
        
        if command:
            dialog = CommandDialog(self, "Edit Command", command)
            if dialog.result:
                try:
                    self.db_manager.update_command(cmd_id, **dialog.result)
                    self.refresh_commands()
                    messagebox.showinfo("Success", "Command updated successfully")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update command: {str(e)}")
                    
    def delete_command(self):
        """Delete selected command"""
        selection = self.command_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a command to delete")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this command?"):
            item = selection[0]
            cmd_id = self.command_tree.item(item, "tags")[0]
            try:
                self.db_manager.delete_command(cmd_id)
                self.refresh_commands()
                messagebox.showinfo("Success", "Command deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete command: {str(e)}")
                
    def execute_command(self):
        """Execute the selected command"""
        selection = self.command_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a command to execute")
            return
            
        item = selection[0]
        cmd_id = self.command_tree.item(item, "tags")[0]
        command = self.db_manager.get_command(cmd_id)
        
        if command:
            # TODO: Implement command execution
            messagebox.showinfo("Execute Command", f"Would execute: {command.get('command', '')}")


class CommandDialog:
    def __init__(self, parent, title, command=None):
        self.result = None
        self.command = command or {}
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.setup_ui()
        self.load_command_data()
        
        # Wait for dialog to close
        parent.wait_window(self.dialog)
        
    def setup_ui(self):
        """Setup the dialog interface"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        fields = [
            ("Name", "name"),
            ("Command", "command"),
            ("Category", "category"),
            ("Description", "description"),
            ("Arguments", "arguments")
        ]
        
        self.entries = {}
        for i, (label_text, field_name) in enumerate(fields):
            ttk.Label(main_frame, text=f"{label_text}:").grid(row=i, column=0, sticky=tk.W, pady=5)
            
            if field_name in ['description', 'arguments']:
                # Use Text widget for longer fields
                text_widget = tk.Text(main_frame, height=3, width=40)
                text_widget.grid(row=i, column=1, sticky="ew", pady=5, padx=(10, 0))
                self.entries[field_name] = text_widget
            else:
                entry = ttk.Entry(main_frame, width=40)
                entry.grid(row=i, column=1, sticky="ew", pady=5, padx=(10, 0))
                self.entries[field_name] = entry
                
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT)
        
    def load_command_data(self):
        """Load existing command data into form"""
        if self.command:
            for field_name, widget in self.entries.items():
                value = self.command.get(field_name, '')
                if isinstance(widget, tk.Text):
                    widget.insert("1.0", str(value))
                else:
                    widget.insert(0, str(value))
                    
    def save(self):
        """Save the command data"""
        data = {}
        for field_name, widget in self.entries.items():
            if isinstance(widget, tk.Text):
                value = widget.get("1.0", tk.END).strip()
            else:
                value = widget.get().strip()
            data[field_name] = value
            
        # Validate required fields
        if not data.get('name'):
            messagebox.showerror("Error", "Name is required")
            return
        if not data.get('command'):
            messagebox.showerror("Error", "Command is required")
            return
            
        self.result = data
        self.dialog.destroy()
        
    def cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy() 