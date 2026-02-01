"""
Secrets Discovery Module
Scans decompiled code for hardcoded secrets, API keys, tokens, etc.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from colorama import Fore, Style


class SecretsDiscovery:
    """Discover hardcoded secrets in decompiled code"""
    
    # Comprehensive secret patterns
    PATTERNS = {
        'aws_access_key': r'AKIA[0-9A-Z]{16}',
        'aws_secret_key': r'aws_secret_access_key[\s]*=[\s]*["\']([A-Za-z0-9/+=]{40})["\']',
        'google_api_key': r'AIza[0-9A-Za-z\\-_]{35}',
        'firebase_url': r'https://[a-z0-9-]+\.firebaseio\.com',
        'firebase_api_key': r'firebase[_-]?api[_-]?key[\s]*[:=][\s]*["\']([A-Za-z0-9-_]{39})["\']',
        'stripe_key': r'(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}',
        'jwt_secret': r'jwt[_-]?secret[\s]*[:=][\s]*["\']([A-Za-z0-9-_]{16,})["\']',
        'oauth_secret': r'(client_secret|oauth_secret)[\s]*[:=][\s]*["\']([A-Za-z0-9-_]{16,})["\']',
        'api_key_generic': r'api[_-]?key[\s]*[:=][\s]*["\']([A-Za-z0-9-_]{16,64})["\']',
        'bearer_token': r'Bearer[\s]+([A-Za-z0-9\\-_\\.]+)',
        'password': r'password[\s]*[:=][\s]*["\']([^"\']{6,})["\']',
        'private_key': r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
        'slack_token': r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24,}',
        'github_token': r'ghp_[A-Za-z0-9]{36}',
        'database_url': r'(mongodb|mysql|postgresql)://[^\\s"\']+',
    }
    
    def __init__(self, decompiled_dir: Path, config):
        self.decompiled_dir = decompiled_dir
        self.config = config
        self.secrets_found = []
    
    def discover(self) -> List[Dict[str, Any]]:
        """
        Discover all secrets in decompiled code
        
        Returns:
            List of discovered secrets
        """
        if not self.decompiled_dir.exists():
            return []
        
        # Scan Java files
        java_files = list(self.decompiled_dir.rglob('*.java'))
        
        if self.config.verbose:
            print(f"{Fore.YELLOW}  [*] Scanning {len(java_files)} Java files for secrets...{Style.RESET_ALL}")
        
        for java_file in java_files:
            self._scan_file(java_file)
        
        # Deduplicate and classify
        self.secrets_found = self._deduplicate_secrets(self.secrets_found)
        self.secrets_found = self._classify_secrets(self.secrets_found)
        
        return self.secrets_found
    
    def _scan_file(self, file_path: Path):
        """Scan a single file for secrets"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            for secret_type, pattern in self.PATTERNS.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    secret_value = match.group(1) if match.groups() else match.group(0)
                    
                    # Skip common false positives
                    if self._is_false_positive(secret_value, secret_type):
                        continue
                    
                    self.secrets_found.append({
                        'type': secret_type,
                        'value': secret_value,
                        'file': str(file_path.relative_to(self.decompiled_dir)),
                        'pattern': pattern,
                        'severity': 'unknown'
                    })
                    
        except Exception as e:
            if self.config.verbose:
                print(f"{Fore.YELLOW}  [!] Error scanning {file_path.name}: {str(e)}{Style.RESET_ALL}")
    
    def _is_false_positive(self, value: str, secret_type: str) -> bool:
        """Filter out common false positives"""
        value_lower = value.lower()
        
        # Common placeholder values
        placeholders = [
            'your_api_key', 'your_key_here', 'api_key_here',
            'insert_key', 'replace_me', 'todo', 'fixme',
            'example', 'test', 'demo', 'sample', 'placeholder',
            'xxxxxxxx', '12345678', 'abcdefgh'
        ]
        
        if any(placeholder in value_lower for placeholder in placeholders):
            return True
        
        # Too short
        if len(value) < 8:
            return True
        
        # All same character
        if len(set(value)) == 1:
            return True
        
        return False
    
    def _deduplicate_secrets(self, secrets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate secrets"""
        seen = set()
        unique = []
        
        for secret in secrets:
            key = (secret['type'], secret['value'])
            if key not in seen:
                seen.add(key)
                unique.append(secret)
        
        return unique
    
    def _classify_secrets(self, secrets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify secrets by severity and context"""
        severity_map = {
            'aws_access_key': 'critical',
            'aws_secret_key': 'critical',
            'stripe_key': 'critical',
            'private_key': 'critical',
            'google_api_key': 'high',
            'firebase_url': 'high',
            'firebase_api_key': 'high',
            'jwt_secret': 'high',
            'oauth_secret': 'high',
            'bearer_token': 'high',
            'slack_token': 'high',
            'github_token': 'high',
            'database_url': 'high',
            'api_key_generic': 'medium',
            'password': 'medium'
        }
        
        for secret in secrets:
            secret['severity'] = severity_map.get(secret['type'], 'medium')
            
            # Check if it's a test/debug key
            if any(keyword in secret['file'].lower() for keyword in ['test', 'debug', 'sample', 'example']):
                secret['context'] = 'test'
                # Downgrade severity for test keys
                if secret['severity'] == 'critical':
                    secret['severity'] = 'high'
                elif secret['severity'] == 'high':
                    secret['severity'] = 'medium'
            else:
                secret['context'] = 'production'
        
        return secrets
