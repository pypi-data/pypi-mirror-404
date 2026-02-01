"""
API Endpoint Extraction Module
Extracts REST, GraphQL, WebSocket endpoints from decompiled code
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse


class EndpointExtractor:
    """Extract API endpoints from decompiled code"""
    
    # URL patterns
    URL_PATTERNS = [
        r'https?://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+',
        r'"(https?://[^"]+)"',
        r"'(https?://[^']+)'",
    ]
    
    # API path patterns
    API_PATTERNS = [
        r'"/api/[^"]*"',
        r"'/api/[^']*'",
        r'"/v[0-9]+/[^"]*"',
        r"'/v[0-9]+/[^']*'",
    ]
    
    def __init__(self, decompiled_dir: Path, config):
        self.decompiled_dir = decompiled_dir
        self.config = config
        self.endpoints = []
    
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract all API endpoints
        
        Returns:
            List of discovered endpoints
        """
        if not self.decompiled_dir.exists():
            return []
        
        # Scan Java files
        java_files = list(self.decompiled_dir.rglob('*.java'))
        
        for java_file in java_files:
            self._scan_file(java_file)
        
        # Deduplicate and classify
        self.endpoints = self._deduplicate_endpoints(self.endpoints)
        self.endpoints = self._classify_endpoints(self.endpoints)
        
        return self.endpoints
    
    def _scan_file(self, file_path: Path):
        """Scan file for endpoints"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Extract full URLs
            for pattern in self.URL_PATTERNS:
                matches = re.finditer(pattern, content)
                for match in matches:
                    url = match.group(1) if match.groups() else match.group(0)
                    url = url.strip('"\'')
                    
                    if self._is_valid_endpoint(url):
                        self.endpoints.append({
                            'url': url,
                            'file': str(file_path.relative_to(self.decompiled_dir)),
                            'type': 'full_url'
                        })
            
            # Extract API paths
            for pattern in self.API_PATTERNS:
                matches = re.finditer(pattern, content)
                for match in matches:
                    path = match.group(0).strip('"\'')
                    self.endpoints.append({
                        'url': path,
                        'file': str(file_path.relative_to(self.decompiled_dir)),
                        'type': 'api_path'
                    })
                    
        except Exception:
            pass
    
    def _is_valid_endpoint(self, url: str) -> bool:
        """Validate if URL is a real endpoint"""
        # Skip common false positives
        false_positives = [
            'http://www.w3.org',
            'http://schemas.android.com',
            'http://www.apache.org',
            'http://example.com',
            'http://localhost',
            'http://127.0.0.1',
            'https://www.google.com',
        ]
        
        if any(fp in url for fp in false_positives):
            return False
        
        # Must be a reasonable length
        if len(url) < 10 or len(url) > 500:
            return False
        
        return True
    
    def _deduplicate_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates"""
        seen = set()
        unique = []
        
        for endpoint in endpoints:
            if endpoint['url'] not in seen:
                seen.add(endpoint['url'])
                unique.append(endpoint)
        
        return unique
    
    def _classify_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify endpoints by type and risk"""
        for endpoint in endpoints:
            url = endpoint['url']
            url_lower = url.lower()
            
            # Determine endpoint category
            if 'graphql' in url_lower:
                endpoint['category'] = 'graphql'
            elif 'ws://' in url or 'wss://' in url:
                endpoint['category'] = 'websocket'
            elif '/api/' in url_lower or '/v1/' in url_lower or '/v2/' in url_lower:
                endpoint['category'] = 'rest_api'
            else:
                endpoint['category'] = 'web'
            
            # Detect admin/internal endpoints
            admin_keywords = ['admin', 'internal', 'debug', 'test', 'dev', 'staging']
            endpoint['is_admin'] = any(keyword in url_lower for keyword in admin_keywords)
            
            # Detect authentication indicators
            auth_keywords = ['auth', 'login', 'token', 'oauth', 'jwt']
            endpoint['requires_auth'] = any(keyword in url_lower for keyword in auth_keywords)
            
            # Parse domain
            if endpoint['type'] == 'full_url':
                try:
                    parsed = urlparse(url)
                    endpoint['domain'] = parsed.netloc
                    endpoint['scheme'] = parsed.scheme
                    endpoint['path'] = parsed.path
                except:
                    pass
        
        return endpoints
