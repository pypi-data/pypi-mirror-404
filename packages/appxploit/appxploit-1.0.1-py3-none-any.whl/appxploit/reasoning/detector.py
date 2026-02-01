"""
Vulnerability Detection Module
Intelligent detection of real vulnerabilities based on analysis results
"""

from typing import Dict, Any, List


class VulnerabilityDetector:
    """Detect vulnerabilities using intelligent reasoning"""
    
    def __init__(self, results: Dict[str, Any], config):
        self.results = results
        self.config = config
        self.vulnerabilities = []
    
    def detect(self) -> List[Dict[str, Any]]:
        """
        Detect all vulnerabilities
        
        Returns:
            List of detected vulnerabilities
        """
        # Security flag vulnerabilities
        self._detect_security_flags()
        
        # Component vulnerabilities
        self._detect_component_issues()
        
        # Permission issues
        self._detect_permission_issues()
        
        # Secret exposure
        self._detect_secret_exposure()
        
        # Endpoint security
        self._detect_endpoint_issues()
        
        return self.vulnerabilities
    
    def _detect_security_flags(self):
        """Detect security flag issues"""
        security_flags = self.results.get('security_flags', {})
        
        for issue in security_flags.get('issues', []):
            self.vulnerabilities.append({
                'title': f"Insecure Configuration: {issue['flag']}",
                'description': issue['description'],
                'severity': issue['severity'],
                'category': 'configuration',
                'cwe': 'CWE-16',  # Configuration
                'evidence': {
                    'flag': issue['flag'],
                    'value': issue['value']
                },
                'impact': self._get_flag_impact(issue['flag']),
                'remediation': self._get_flag_remediation(issue['flag'])
            })
    
    def _detect_component_issues(self):
        """Detect exported component vulnerabilities"""
        components = self.results.get('components', {})
        
        # Dangerous exports
        for dangerous in components.get('dangerous_exports', []):
            self.vulnerabilities.append({
                'title': f"Insecure Exported {dangerous['type'].title()}",
                'description': f"{dangerous['name']}: {dangerous['issue']}",
                'severity': dangerous['severity'],
                'category': 'component_security',
                'cwe': 'CWE-927',  # Improper Validation of Intent
                'evidence': dangerous,
                'impact': 'Exported components without proper protection can be accessed by malicious apps',
                'remediation': 'Add permission protection or set android:exported="false"'
            })
        
        # Deep link issues
        deeplinks = components.get('deeplinks', [])
        if deeplinks:
            self.vulnerabilities.append({
                'title': 'Deep Link Injection Risk',
                'description': f'Found {len(deeplinks)} deep link handlers that may be vulnerable to injection',
                'severity': 'medium',
                'category': 'deep_linking',
                'cwe': 'CWE-939',  # Improper URL Validation
                'evidence': {'deeplinks': deeplinks[:5]},  # Show first 5
                'impact': 'Attackers may craft malicious deep links to bypass authentication or access sensitive features',
                'remediation': 'Implement strict deep link validation and sanitization'
            })
    
    def _detect_permission_issues(self):
        """Detect permission-related issues"""
        permissions = self.results.get('permissions', {})
        
        if permissions.get('over_privileged'):
            self.vulnerabilities.append({
                'title': 'Over-Privileged Application',
                'description': f"App requests {len(permissions.get('dangerous_permissions', []))} dangerous permissions",
                'severity': 'low',
                'category': 'permissions',
                'cwe': 'CWE-250',  # Execution with Unnecessary Privileges
                'evidence': {'dangerous_permissions': permissions.get('dangerous_permissions', [])},
                'impact': 'Excessive permissions increase attack surface and privacy risks',
                'remediation': 'Review and remove unnecessary permissions'
            })
    
    def _detect_secret_exposure(self):
        """Detect exposed secrets"""
        secrets = self.results.get('secrets', [])
        
        # Group by severity
        critical_secrets = [s for s in secrets if s['severity'] == 'critical']
        high_secrets = [s for s in secrets if s['severity'] == 'high']
        
        if critical_secrets:
            for secret in critical_secrets:
                self.vulnerabilities.append({
                    'title': f"Critical Secret Exposure: {secret['type'].replace('_', ' ').title()}",
                    'description': f"Hardcoded {secret['type']} found in {secret['file']}",
                    'severity': 'critical',
                    'category': 'secret_exposure',
                    'cwe': 'CWE-798',  # Hard-coded Credentials
                    'evidence': {
                        'type': secret['type'],
                        'file': secret['file'],
                        'value_preview': secret['value'][:20] + '...' if len(secret['value']) > 20 else secret['value'],
                        'context': secret.get('context', 'unknown')
                    },
                    'impact': 'Exposed credentials can lead to unauthorized access to cloud services, APIs, or databases',
                    'remediation': 'Move secrets to secure storage (Android Keystore, environment variables, or secure backend)'
                })
        
        if high_secrets:
            self.vulnerabilities.append({
                'title': 'Multiple API Keys Exposed',
                'description': f"Found {len(high_secrets)} hardcoded API keys and tokens",
                'severity': 'high',
                'category': 'secret_exposure',
                'cwe': 'CWE-798',
                'evidence': {'secrets': [{'type': s['type'], 'file': s['file']} for s in high_secrets[:10]]},
                'impact': 'Exposed API keys can be extracted and abused by attackers',
                'remediation': 'Use secure credential storage and implement certificate pinning'
            })
    
    def _detect_endpoint_issues(self):
        """Detect API endpoint security issues"""
        endpoints = self.results.get('endpoints', [])
        
        # Admin endpoints
        admin_endpoints = [e for e in endpoints if e.get('is_admin')]
        if admin_endpoints:
            self.vulnerabilities.append({
                'title': 'Admin/Internal API Endpoints Exposed',
                'description': f"Found {len(admin_endpoints)} admin or internal endpoints",
                'severity': 'high',
                'category': 'api_security',
                'cwe': 'CWE-284',  # Improper Access Control
                'evidence': {'endpoints': [e['url'] for e in admin_endpoints[:10]]},
                'impact': 'Admin endpoints may provide elevated access or sensitive functionality',
                'remediation': 'Ensure proper authentication and authorization on admin endpoints'
            })
        
        # HTTP endpoints (cleartext)
        http_endpoints = [e for e in endpoints if e.get('scheme') == 'http']
        if http_endpoints:
            self.vulnerabilities.append({
                'title': 'Insecure HTTP Endpoints',
                'description': f"Found {len(http_endpoints)} HTTP (non-HTTPS) endpoints",
                'severity': 'medium',
                'category': 'transport_security',
                'cwe': 'CWE-319',  # Cleartext Transmission
                'evidence': {'endpoints': [e['url'] for e in http_endpoints[:10]]},
                'impact': 'HTTP traffic can be intercepted and modified (MITM attacks)',
                'remediation': 'Use HTTPS for all network communication'
            })
    
    def _get_flag_impact(self, flag: str) -> str:
        """Get impact description for security flag"""
        impacts = {
            'debuggable': 'Allows attackers to attach debuggers and manipulate app runtime behavior',
            'allowBackup': 'App data can be extracted via ADB backup, potentially exposing sensitive information',
            'usesCleartextTraffic': 'Network traffic can be intercepted and modified via man-in-the-middle attacks',
            'targetSdkVersion': 'Missing modern Android security features and protections'
        }
        return impacts.get(flag, 'Security misconfiguration')
    
    def _get_flag_remediation(self, flag: str) -> str:
        """Get remediation for security flag"""
        remediations = {
            'debuggable': 'Set android:debuggable="false" in AndroidManifest.xml for production builds',
            'allowBackup': 'Set android:allowBackup="false" or implement BackupAgent with encryption',
            'usesCleartextTraffic': 'Set android:usesCleartextTraffic="false" and use HTTPS only',
            'targetSdkVersion': 'Update targetSdkVersion to latest Android API level (33+)'
        }
        return remediations.get(flag, 'Fix security configuration')
