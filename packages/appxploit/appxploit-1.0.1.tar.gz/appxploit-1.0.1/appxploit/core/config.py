"""
Configuration management for AppXploit
Handles settings, tool paths, and pattern loading
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from colorama import Fore, Style

from appxploit.core.utils import Utils


class Config:
    """Configuration manager"""
    
    def __init__(self, verbose: bool = False, quick: bool = False, output_format: str = 'markdown'):
        self.verbose = verbose
        self.quick = quick
        self.output_format = output_format
        
        # Paths
        self.appxploit_dir = Utils.get_appxploit_dir()
        self.tools_dir = Utils.get_tools_dir()
        self.temp_dir = Utils.get_temp_dir()
        
        # Tool paths (will be set during dependency check)
        self.apktool_path: Optional[Path] = None
        self.jadx_path: Optional[Path] = None
        
        # Patterns and rules (loaded from data files)
        self.secret_patterns: Dict[str, Any] = {}
        self.api_patterns: Dict[str, Any] = {}
        self.vuln_rules: Dict[str, Any] = {}
        self.advanced_patterns: Dict[str, Any] = {}  # Advanced vulnerability patterns
        
        # Cache directory for performance optimization
        self.cache_dir = self.appxploit_dir / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load patterns
        self._load_patterns()
    
    def _load_patterns(self):
        """Load patterns and rules from data files"""
        try:
            # Get package data directory
            package_dir = Path(__file__).parent.parent
            data_dir = package_dir / 'data'
            
            # Load secret patterns
            patterns_file = data_dir / 'patterns.yaml'
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    data = yaml.safe_load(f)
                    self.secret_patterns = data.get('secrets', {})
                    self.api_patterns = data.get('apis', {})
            
            # Load vulnerability rules
            vuln_file = data_dir / 'vuln_rules.yaml'
            if vuln_file.exists():
                with open(vuln_file, 'r') as f:
                    self.vuln_rules = yaml.safe_load(f)
            
            # Load advanced patterns
            advanced_file = data_dir / 'advanced_patterns.yaml'
            if advanced_file.exists():
                with open(advanced_file, 'r') as f:
                    self.advanced_patterns = yaml.safe_load(f)
                    
        except Exception as e:
            if self.verbose:
                print(f"{Fore.YELLOW}[!] Warning: Could not load patterns: {str(e)}{Style.RESET_ALL}")
    
    def check_dependencies(self) -> bool:
        """
        Check and setup required dependencies
        Returns True if all dependencies are ready
        """
        if self.verbose:
            print(f"{Fore.CYAN}[*] Checking dependencies...{Style.RESET_ALL}")
        
        # Check Java
        if not Utils.check_java():
            print(f"{Fore.RED}[!] Java is not installed. Please install Java 8 or higher.{Style.RESET_ALL}")
            return False
        
        if self.verbose:
            print(f"{Fore.GREEN}[✓] Java found{Style.RESET_ALL}")
        
        # Check/setup apktool
        self.apktool_path = self._setup_apktool()
        if not self.apktool_path:
            return False
        
        # Check/setup jadx
        self.jadx_path = self._setup_jadx()
        if not self.jadx_path:
            return False
        
        if self.verbose:
            print(f"{Fore.GREEN}[✓] All dependencies ready{Style.RESET_ALL}")
        
        return True
    
    def _setup_apktool(self) -> Optional[Path]:
        """Setup apktool (download if needed)"""
        # Check if apktool.jar exists
        apktool_jar = self.tools_dir / 'apktool.jar'
        
        if apktool_jar.exists():
            if self.verbose:
                print(f"{Fore.GREEN}[✓] apktool found{Style.RESET_ALL}")
            return apktool_jar
        
        # Download apktool
        print(f"{Fore.YELLOW}[*] Downloading apktool...{Style.RESET_ALL}")
        url = "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool"
        jar_url = "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar"
        
        # Download JAR
        if Utils.download_file(jar_url, apktool_jar, self.verbose):
            print(f"{Fore.GREEN}[✓] apktool ready{Style.RESET_ALL}")
            return apktool_jar
        else:
            print(f"{Fore.RED}[!] Failed to download apktool{Style.RESET_ALL}")
            return None
    
    def _setup_jadx(self) -> Optional[Path]:
        """Setup jadx (download if needed)"""
        # Check if jadx exists
        jadx_dir = self.tools_dir / 'jadx'
        jadx_bin = jadx_dir / 'bin' / ('jadx.bat' if Utils.is_windows() else 'jadx')
        
        if jadx_bin.exists():
            if self.verbose:
                print(f"{Fore.GREEN}[✓] jadx found{Style.RESET_ALL}")
            return jadx_bin
        
        # Download jadx
        print(f"{Fore.YELLOW}[*] Downloading jadx...{Style.RESET_ALL}")
        
        # Determine download URL based on OS
        version = "1.5.0"
        if Utils.is_windows():
            filename = f"jadx-{version}.zip"
        else:
            filename = f"jadx-{version}.zip"
        
        url = f"https://github.com/skylot/jadx/releases/download/v{version}/{filename}"
        zip_path = self.tools_dir / filename
        
        # Download and extract
        if Utils.download_file(url, zip_path, self.verbose):
            if Utils.extract_zip(zip_path, jadx_dir, self.verbose):
                # Make executable on Unix
                if not Utils.is_windows():
                    Utils.make_executable(jadx_bin)
                
                # Clean up zip
                zip_path.unlink()
                
                print(f"{Fore.GREEN}[✓] jadx ready{Style.RESET_ALL}")
                return jadx_bin
        
        print(f"{Fore.RED}[!] Failed to download jadx{Style.RESET_ALL}")
        return None
    
    def get_work_dir(self, apk_name: str) -> Path:
        """
        Get working directory for APK analysis
        
        Args:
            apk_name: APK filename (without extension)
            
        Returns:
            Path to working directory (in current folder)
        """
        # User requested local extraction folder
        work_dir = Path.cwd() / f"{apk_name}_analysis"
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir
