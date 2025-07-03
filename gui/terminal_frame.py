import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, Callable, Optional


class TerminalFrame(ttk.Frame):
    def __init__(self, parent, on_ssh_command: Callable):
        super().__init__(parent)
        self.on_ssh_command = on_ssh_command
        self.current_connection: Optional[Dict[str, Any]] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the terminal interface"""
        # Terminal header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(header_frame, text="SSH Terminal", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Connection info
        self.connection_info = ttk.Label(header_frame, text="No connection selected", foreground="gray")
        self.connection_info.pack(side=tk.RIGHT)
        
        # Terminal output area
        output_frame = ttk.LabelFrame(self, text="Output", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Scrolled text widget for output
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="black",
            fg="white",
            insertbackground="white"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Make output read-only
        self.output_text.config(state=tk.DISABLED)
        
        # Command input area
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(input_frame, text="Command:").pack(side=tk.LEFT)
        
        self.command_entry = ttk.Entry(input_frame)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.command_entry.bind("<Return>", self.execute_command)
        
        ttk.Button(input_frame, text="Execute", command=self.execute_command).pack(side=tk.RIGHT)
        
        # Command history
        history_frame = ttk.LabelFrame(self, text="Command History", padding=5)
        history_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Listbox for command history
        self.history_listbox = tk.Listbox(history_frame, height=6, font=("Consolas", 9))
        history_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click on history item
        self.history_listbox.bind("<Double-1>", self.on_history_select)
        
        # Quick command buttons
        quick_frame = ttk.LabelFrame(self, text="Quick Commands", padding=5)
        quick_frame.pack(fill=tk.X, pady=(5, 0))
        
        quick_commands = [
            ("ls -la", "List files"),
            ("pwd", "Current directory"),
            ("whoami", "Current user"),
            ("df -h", "Disk usage"),
            ("top", "System processes"),
            ("ps aux", "All processes")
        ]
        
        for i, (command, description) in enumerate(quick_commands):
            btn = ttk.Button(
                quick_frame, 
                text=f"{description} ({command})",
                command=lambda cmd=command: self.quick_command(cmd)
            )
            btn.grid(row=i//3, column=i%3, sticky="ew", padx=2, pady=2)
            
        # Configure grid weights
        for i in range(3):
            quick_frame.columnconfigure(i, weight=1)
            
    def set_connection(self, connection: Dict[str, Any]):
        """Set the current connection"""
        self.current_connection = connection
        if connection:
            self.connection_info.config(
                text=f"Connected to: {connection['name']} ({connection['host']}:{connection['port']})",
                foreground="green"
            )
            self.append_output(f"Connected to {connection['name']} ({connection['host']}:{connection['port']})\n")
        else:
            self.connection_info.config(text="No connection selected", foreground="gray")
            
    def append_output(self, text: str):
        """Append text to the output area"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        
    def execute_command(self, event=None):
        """Execute the command in the input field"""
        command = self.command_entry.get().strip()
        if not command:
            return
            
        if not self.current_connection:
            self.append_output("Error: No connection selected\n")
            return
            
        # Add to history
        self.add_to_history(command)
        
        # Clear input
        self.command_entry.delete(0, tk.END)
        
        # Execute command
        self.on_ssh_command(command)
        
    def quick_command(self, command: str):
        """Execute a quick command"""
        if not self.current_connection:
            self.append_output("Error: No connection selected\n")
            return
            
        self.add_to_history(command)
        self.on_ssh_command(command)
        
    def add_to_history(self, command: str):
        """Add command to history"""
        # Avoid duplicates
        history_items = self.history_listbox.get(0, tk.END)
        if command not in history_items:
            self.history_listbox.insert(0, command)
            # Keep only last 50 commands
            if self.history_listbox.size() > 50:
                self.history_listbox.delete(tk.END)
                
    def on_history_select(self, event):
        """Handle history item selection"""
        selection = self.history_listbox.curselection()
        if selection:
            command = self.history_listbox.get(selection[0])
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, command)
            
    def clear_output(self):
        """Clear the output area"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
    def save_output(self, filename: str):
        """Save output to file"""
        try:
            with open(filename, 'w') as f:
                f.write(self.output_text.get(1.0, tk.END))
        except Exception as e:
            self.append_output(f"Error saving output: {str(e)}\n") 