"""
Cross-platform utility functions
Handles OS detection, path management, and external tool execution
"""

import os
import sys
import platform
import subprocess
import shutil
import requests
from pathlib import Path
from typing import Optional, Tuple
from colorama import Fore, Style


class Utils:
    """Cross-platform utility functions"""
    
    @staticmethod
    def get_os() -> str:
        """
        Detect operating system
        Returns: 'windows', 'linux', or 'darwin'
        """
        return platform.system().lower()
    
    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows"""
        return Utils.get_os() == 'windows'
    
    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux"""
        return Utils.get_os() == 'linux'
    
    @staticmethod
    def get_appxploit_dir() -> Path:
        """
        Get AppXploit home directory
        Returns: ~/.appxploit/
        """
        home = Path.home()
        appxploit_dir = home / '.appxploit'
        appxploit_dir.mkdir(exist_ok=True)
        return appxploit_dir
    
    @staticmethod
    def get_tools_dir() -> Path:
        """
        Get tools directory
        Returns: ~/.appxploit/tools/
        """
        tools_dir = Utils.get_appxploit_dir() / 'tools'
        tools_dir.mkdir(exist_ok=True)
        return tools_dir
    
    @staticmethod
    def get_temp_dir() -> Path:
        """
        Get temporary working directory
        Returns: ~/.appxploit/temp/
        """
        temp_dir = Utils.get_appxploit_dir() / 'temp'
        temp_dir.mkdir(exist_ok=True)
        return temp_dir
    
    @staticmethod
    def run_command(cmd: list, cwd: Optional[Path] = None, verbose: bool = False) -> Tuple[int, str, str]:
        """
        Execute external command
        
        Args:
            cmd: Command as list of strings
            cwd: Working directory
            verbose: Print command output
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            if verbose:
                print(f"{Fore.CYAN}[*] Running: {' '.join(cmd)}{Style.RESET_ALL}")
            
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if verbose and result.stdout:
                print(result.stdout)
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return 1, "", "Command timeout"
        except Exception as e:
            return 1, "", str(e)
    
    @staticmethod
    def check_java() -> bool:
        """Check if Java is installed"""
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def download_file(url: str, dest: Path, verbose: bool = False) -> bool:
        """
        Download file from URL
        
        Args:
            url: Download URL
            dest: Destination path
            verbose: Show progress
            
        Returns:
            True if successful
        """
        try:
            if verbose:
                print(f"{Fore.CYAN}[*] Downloading: {url}{Style.RESET_ALL}")
            
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if verbose:
                print(f"{Fore.GREEN}[✓] Downloaded: {dest.name}{Style.RESET_ALL}")
            
            return True
            
        except Exception as e:
            if verbose:
                print(f"{Fore.RED}[!] Download failed: {str(e)}{Style.RESET_ALL}")
            return False
    
    @staticmethod
    def extract_zip(zip_path: Path, dest_dir: Path, verbose: bool = False) -> bool:
        """
        Extract ZIP archive
        
        Args:
            zip_path: Path to ZIP file
            dest_dir: Extraction destination
            verbose: Show progress
            
        Returns:
            True if successful
        """
        try:
            import zipfile
            
            if verbose:
                print(f"{Fore.CYAN}[*] Extracting: {zip_path.name}{Style.RESET_ALL}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)
            
            if verbose:
                print(f"{Fore.GREEN}[✓] Extracted to: {dest_dir}{Style.RESET_ALL}")
            
            return True
            
        except Exception as e:
            if verbose:
                print(f"{Fore.RED}[!] Extraction failed: {str(e)}{Style.RESET_ALL}")
            return False
    
    @staticmethod
    def cleanup_temp(verbose: bool = False):
        """Clean up temporary files"""
        try:
            temp_dir = Utils.get_temp_dir()
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                temp_dir.mkdir(exist_ok=True)
                if verbose:
                    print(f"{Fore.GREEN}[✓] Cleaned up temporary files{Style.RESET_ALL}")
        except Exception as e:
            if verbose:
                print(f"{Fore.YELLOW}[!] Cleanup warning: {str(e)}{Style.RESET_ALL}")
    
    @staticmethod
    def find_executable(name: str) -> Optional[Path]:
        """
        Find executable in PATH or tools directory
        
        Args:
            name: Executable name
            
        Returns:
            Path to executable or None
        """
        # Check system PATH
        system_path = shutil.which(name)
        if system_path:
            return Path(system_path)
        
        # Check tools directory
        tools_dir = Utils.get_tools_dir()
        
        # Windows executable
        if Utils.is_windows():
            exe_path = tools_dir / f"{name}.exe"
            if exe_path.exists():
                return exe_path
        
        # Unix executable
        exe_path = tools_dir / name
        if exe_path.exists() and os.access(exe_path, os.X_OK):
            return exe_path
        
        return None
    
    @staticmethod
    def make_executable(path: Path):
        """Make file executable (Unix only)"""
        if not Utils.is_windows():
            os.chmod(path, 0o755)
