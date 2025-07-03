import paramiko
import time
from typing import Optional, Dict, Any
import logging

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
        
    def connect(self, hostname: str, port: int = 22, username: Optional[str] = None, 
                password: Optional[str] = None, key_path: Optional[str] = None, timeout: int = 10):
        """Connect to SSH server"""
        try:
            self.hostname = hostname
            self.port = port
            self.username = username
            
            # Prepare connection parameters
            connect_kwargs = {
                'hostname': hostname,
                'port': port,
                'timeout': timeout
            }
            
            if username:
                connect_kwargs['username'] = username
                
            # Authentication method
            if key_path:
                # Use private key authentication
                try:
                    private_key = paramiko.RSAKey.from_private_key_file(key_path)
                    connect_kwargs['pkey'] = private_key
                except Exception as e:
                    logger.error(f"Failed to load private key: {e}")
                    raise Exception(f"Failed to load private key: {e}")
            elif password:
                # Use password authentication
                connect_kwargs['password'] = password
            else:
                raise Exception("Either password or key_path must be provided")
                
            # Connect to server
            logger.info(f"Connecting to {hostname}:{port} as {username}")
            self.client.connect(**connect_kwargs)
            self.connected = True
            
            logger.info("SSH connection established successfully")
            
        except paramiko.AuthenticationException:
            logger.error("Authentication failed")
            raise Exception("Authentication failed. Check your credentials.")
        except paramiko.SSHException as e:
            logger.error(f"SSH error: {e}")
            raise Exception(f"SSH error: {e}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise Exception(f"Connection error: {e}")
            
    def execute_command(self, command: str, timeout: int = 30) -> str:
        """Execute a command on the remote server"""
        if not self.connected:
            raise Exception("Not connected to any server")
            
        try:
            logger.info(f"Executing command: {command}")
            
            # Execute command
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            # Get output
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            # Wait for command to complete
            exit_status = stdout.channel.recv_exit_status()
            
            # Combine output and error
            result = output
            if error:
                result += f"\nError: {error}"
                
            if exit_status != 0:
                result += f"\nExit status: {exit_status}"
                
            logger.info(f"Command completed with exit status: {exit_status}")
            return result
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise Exception(f"Command execution error: {e}")
            
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
            raise Exception("Not connected to any server")
            
        try:
            logger.info(f"Uploading {local_path} to {remote_path}")
            
            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            
            logger.info("File upload completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            raise Exception(f"File upload error: {e}")
            
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from the remote server"""
        if not self.connected:
            raise Exception("Not connected to any server")
            
        try:
            logger.info(f"Downloading {remote_path} to {local_path}")
            
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            
            logger.info("File download completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"File download error: {e}")
            raise Exception(f"File download error: {e}")
            
    def list_directory(self, remote_path: str = ".") -> list:
        """List directory contents on remote server"""
        if not self.connected:
            raise Exception("Not connected to any server")
            
        try:
            logger.info(f"Listing directory: {remote_path}")
            
            sftp = self.client.open_sftp()
            files = sftp.listdir_attr(remote_path)
            sftp.close()
            
            # Convert to list of dictionaries
            file_list = []
            for file_attr in files:
                if file_attr.st_mode is not None:
                    file_info = {
                        'name': file_attr.filename,
                        'size': file_attr.st_size,
                        'permissions': oct(file_attr.st_mode)[-3:],
                        'is_directory': file_attr.st_mode & 0o40000 != 0,
                        'modified_time': file_attr.st_mtime
                    }
                    file_list.append(file_info)
                
            logger.info(f"Found {len(file_list)} items in directory")
            return file_list
            
        except Exception as e:
            logger.error(f"Directory listing error: {e}")
            raise Exception(f"Directory listing error: {e}")
            
    def is_connected(self) -> bool:
        """Check if connected to server"""
        transport = self.client.get_transport()
        return self.connected and transport is not None and transport.is_active()
        
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
        
    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            try:
                self.client.close()
                logger.info("SSH connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self.connected = False
                self.hostname = None
                self.port = None
                self.username = None
                
    def __del__(self):
        """Cleanup on object destruction"""
        self.disconnect() 