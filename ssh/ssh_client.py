import paramiko
import time
from typing import Optional, Dict, Any
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSHClient:
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connected = False
        self.hostname = None
        self.port = None
        self.username = None
        
    def connect(self, connection_data: Dict[str, Any]):
        """Connect to SSH server using connection data"""
        try:
            hostname = connection_data['host']
            port = connection_data.get('port', 22)
            username = connection_data['username']
            password = connection_data.get('password')
            key_path = connection_data.get('key_path')
            
            logger.info(f"Connecting to {hostname}:{port} as {username}")
            
            # Try key-based authentication first
            if key_path and os.path.exists(key_path):
                try:
                    self.client.connect(
                        hostname=hostname,
                        port=port,
                        username=username,
                        key_filename=key_path
                    )
                    self.connected = True
                    logger.info("SSH connection established successfully")
                    return
                except Exception as e:
                    logger.warning(f"Key-based authentication failed: {e}")
                    
            # Fall back to password authentication
            if password:
                self.client.connect(
                    hostname=hostname,
                    port=port,
                    username=username,
                    password=password
                )
                self.connected = True
                logger.info("SSH connection established successfully")
            else:
                raise Exception("No password or valid key provided")
                
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.connected = False
            raise
            
    def execute_command(self, command: str) -> str:
        """Execute a command and return the output"""
        if not self.connected:
            raise Exception("Not connected to SSH server")
            
        try:
            logger.info(f"Executing command: {command}")
            stdin, stdout, stderr = self.client.exec_command(command)
            
            # Get output
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_status = stdout.channel.recv_exit_status()
            
            logger.info(f"Command completed with exit status: {exit_status}")
            
            # Combine output and error
            result = output
            if error:
                result += f"\nError: {error}"
                
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise
            
    def execute_interactive_command(self, command: str) -> str:
        """Execute an interactive command"""
        if not self.connected:
            raise Exception("Not connected to any server")
            
        try:
            logger.info(f"Executing interactive command: {command}")
            
            # Get shell channel
            channel = self.client.invoke_shell()
            
            # Send command
            channel.send((command + '\n').encode('utf-8'))
            
            # Wait for output
            time.sleep(1)
            
            # Get output
            output = ""
            while channel.recv_ready():
                output += channel.recv(1024).decode('utf-8')
                
            channel.close()
            return output
            
        except Exception as e:
            logger.error(f"Interactive command error: {e}")
            raise Exception(f"Interactive command error: {e}")
            
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to the remote server"""
        if not self.connected:
            raise Exception("Not connected to SSH server")
            
        try:
            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            logger.info(f"File uploaded: {local_path} -> {remote_path}")
            return True
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise
            
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from the remote server"""
        if not self.connected:
            raise Exception("Not connected to SSH server")
            
        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            logger.info(f"File downloaded: {remote_path} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"File download failed: {e}")
            raise
            
    def list_directory(self, remote_path: str = ".") -> list:
        """List directory contents"""
        if not self.connected:
            raise Exception("Not connected to SSH server")
            
        try:
            sftp = self.client.open_sftp()
            files = sftp.listdir_attr(remote_path)
            sftp.close()
            
            result = []
            for file_attr in files:
                result.append({
                    'name': file_attr.filename,
                    'size': file_attr.st_size,
                    'permissions': oct(file_attr.st_mode)[-3:],
                    'is_directory': file_attr.st_mode & 0o40000 != 0
                })
                
            return result
        except Exception as e:
            logger.error(f"Directory listing failed: {e}")
            raise
            
    def is_connected(self) -> bool:
        """Check if connected to SSH server"""
        return self.connected
        
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        if not self.connected:
            return {}
            
        return {
            'hostname': self.hostname,
            'port': self.port,
            'username': self.username,
            'connected': self.is_connected()
        }
        
    def close(self):
        """Close the SSH connection"""
        if self.connected:
            self.client.close()
            self.connected = False
            logger.info("SSH connection closed")
            
    def disconnect(self):
        """Alias for close method"""
        self.close()
        
    def __del__(self):
        """Cleanup on object destruction"""
        self.disconnect() 