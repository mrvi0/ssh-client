import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, Callable, Optional
import threading
import queue


class TerminalFrame(ttk.Frame):
    def __init__(self, parent, on_ssh_command: Callable):
        super().__init__(parent)
        self.on_ssh_command = on_ssh_command
        self.current_connection: Optional[Dict[str, Any]] = None
        self.command_history = []
        self.history_index = 0
        self.current_prompt = "$ "
        self.command_queue = queue.Queue()
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
        
        # Terminal output area - теперь это основной терминал
        self.terminal_text = tk.Text(
            self,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="black",
            fg="white",
            insertbackground="white",
            selectbackground="blue",
            cursor="ibeam"
        )
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.terminal_text.yview)
        h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.terminal_text.xview)
        self.terminal_text.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack terminal and scrollbars
        self.terminal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events for terminal-like behavior
        self.terminal_text.bind("<KeyPress>", self.on_key_press)
        self.terminal_text.bind("<Return>", self.on_return)
        self.terminal_text.bind("<Up>", self.on_up_arrow)
        self.terminal_text.bind("<Down>", self.on_down_arrow)
        self.terminal_text.bind("<Tab>", self.on_tab)
        self.terminal_text.bind("<Control-c>", self.on_copy)
        self.terminal_text.bind("<Control-v>", self.on_paste)
        self.terminal_text.bind("<Control-l>", self.on_clear)
        
        # Set initial prompt
        self.write_prompt()
        
        # Start command processing thread
        self.running = True
        self.command_thread = threading.Thread(target=self.process_commands, daemon=True)
        self.command_thread.start()
        
    def write_prompt(self):
        """Write the current prompt to terminal"""
        self.terminal_text.insert(tk.END, self.current_prompt)
        self.terminal_text.see(tk.END)
        self.terminal_text.mark_set(tk.INSERT, tk.END)
        
    def write_output(self, text: str, color: str = "white"):
        """Write output to terminal with color"""
        self.terminal_text.insert(tk.END, text, color)
        self.terminal_text.see(tk.END)
        self.terminal_text.mark_set(tk.INSERT, tk.END)
        
    def on_key_press(self, event):
        """Handle key press events"""
        # Prevent editing above the current line
        current_line = self.terminal_text.index(tk.INSERT).split('.')[0]
        last_prompt_line = self.get_last_prompt_line()
        
        if int(current_line) < last_prompt_line:
            return "break"
            
    def on_return(self, event):
        """Handle Enter key - execute command"""
        # Get the current line
        current_line = self.terminal_text.index(tk.INSERT).split('.')[0]
        line_start = f"{current_line}.0"
        line_end = f"{current_line}.end"
        
        # Get command from current line
        line_content = self.terminal_text.get(line_start, line_end)
        command = line_content.replace(self.current_prompt, "").strip()
        
        if command:
            # Add to history
            if command not in self.command_history:
                self.command_history.append(command)
            self.history_index = len(self.command_history)
            
            # Execute command
            self.execute_command(command)
        else:
            # Just add new line with prompt
            self.terminal_text.insert(tk.END, "\n")
            self.write_prompt()
            
        return "break"
        
    def on_up_arrow(self, event):
        """Handle up arrow - previous command in history"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.replace_current_line(self.command_history[self.history_index])
        return "break"
        
    def on_down_arrow(self, event):
        """Handle down arrow - next command in history"""
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.replace_current_line(self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self.replace_current_line("")
        return "break"
        
    def on_tab(self, event):
        """Handle tab - autocomplete (basic implementation)"""
        # Basic autocomplete for common commands
        common_commands = ["ls", "cd", "pwd", "whoami", "ps", "top", "df", "du", "cat", "vim", "nano"]
        
        current_line = self.terminal_text.index(tk.INSERT).split('.')[0]
        line_start = f"{current_line}.0"
        line_end = f"{current_line}.end"
        line_content = self.terminal_text.get(line_start, line_end)
        command = line_content.replace(self.current_prompt, "").strip()
        
        if command:
            for cmd in common_commands:
                if cmd.startswith(command):
                    self.replace_current_line(cmd)
                    break
                    
        return "break"
        
    def on_copy(self, event):
        """Handle Ctrl+C - copy selected text"""
        try:
            selected_text = self.terminal_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selected_text)
        except tk.TclError:
            pass
        return "break"
        
    def on_paste(self, event):
        """Handle Ctrl+V - paste text"""
        try:
            clipboard_text = self.clipboard_get()
            self.terminal_text.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            pass
        return "break"
        
    def on_clear(self, event):
        """Handle Ctrl+L - clear screen"""
        self.terminal_text.delete(1.0, tk.END)
        self.write_prompt()
        return "break"
        
    def replace_current_line(self, new_command: str):
        """Replace the current line with new command"""
        current_line = self.terminal_text.index(tk.INSERT).split('.')[0]
        line_start = f"{current_line}.0"
        line_end = f"{current_line}.end"
        
        self.terminal_text.delete(line_start, line_end)
        self.terminal_text.insert(line_start, self.current_prompt + new_command)
        self.terminal_text.mark_set(tk.INSERT, tk.END)
        
    def get_last_prompt_line(self) -> int:
        """Get the line number of the last prompt"""
        content = self.terminal_text.get(1.0, tk.END)
        lines = content.split('\n')
        
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].endswith(self.current_prompt):
                return i + 1
        return 1
        
    def execute_command(self, command: str):
        """Execute a command"""
        if not self.current_connection:
            self.write_output("\nError: No connection selected\n", "red")
            self.write_prompt()
            return
            
        # Add command to queue for processing
        self.command_queue.put(command)
        
    def process_commands(self):
        """Process commands in background thread"""
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.1)
                self.execute_ssh_command(command)
            except queue.Empty:
                continue
                
    def execute_ssh_command(self, command: str):
        """Execute SSH command and update terminal"""
        try:
            # Show command being executed
            self.write_output(f"\n$ {command}\n", "green")
            
            # Execute command
            result = self.on_ssh_command(command)
            
            # Show result
            if result:
                self.write_output(result + "\n")
                
        except Exception as e:
            self.write_output(f"Error: {str(e)}\n", "red")
            
        finally:
            # Add new prompt
            self.write_prompt()
            
    def set_connection(self, connection: Dict[str, Any]):
        """Set the current connection"""
        self.current_connection = connection
        if connection:
            self.connection_info.config(
                text=f"Connected to: {connection['name']} ({connection['host']}:{connection['port']})",
                foreground="green"
            )
            self.current_prompt = f"{connection['username']}@{connection['host']}:~$ "
            self.write_output(f"Connected to {connection['name']} ({connection['host']}:{connection['port']})\n", "green")
        else:
            self.connection_info.config(text="No connection selected", foreground="gray")
            self.current_prompt = "$ "
            
    def clear_terminal(self):
        """Clear the terminal"""
        self.terminal_text.delete(1.0, tk.END)
        self.write_prompt()
        
    def save_output(self, filename: str):
        """Save terminal output to file"""
        try:
            with open(filename, 'w') as f:
                f.write(self.terminal_text.get(1.0, tk.END))
        except Exception as e:
            self.write_output(f"Error saving output: {str(e)}\n", "red")
            
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if hasattr(self, 'command_thread'):
            self.command_thread.join(timeout=1) 