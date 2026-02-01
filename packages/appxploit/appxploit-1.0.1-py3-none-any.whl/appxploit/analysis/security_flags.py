"""Security Flags Analysis"""

from pathlib import Path
from typing import Dict, Any, List


class SecurityFlagsAnalyzer:
    """Analyze security configuration flags"""
    
    def __init__(self, manifest_data: Dict[str, Any], extract_dir: Path, config):
        self.manifest = manifest_data
        self.extract_dir = extract_dir
        self.config = config
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze security flags"""
        app_attrs = self.manifest.get('application', {})
        sdk_info = self.manifest.get('uses_sdk', {})
        
        issues = []
        
        # Check debuggable
        if app_attrs.get('debuggable') == 'true':
            issues.append({
                'flag': 'debuggable',
                'value': 'true',
                'severity': 'critical',
                'description': 'App is debuggable - allows runtime manipulation'
            })
        
        # Check allowBackup
        if app_attrs.get('allowBackup') != 'false':
            issues.append({
                'flag': 'allowBackup',
                'value': app_attrs.get('allowBackup', 'true (default)'),
                'severity': 'medium',
                'description': 'Backup allowed - data may be extracted via ADB'
            })
        
        # Check cleartext traffic
        if app_attrs.get('usesCleartextTraffic') == 'true':
            issues.append({
                'flag': 'usesCleartextTraffic',
                'value': 'true',
                'severity': 'high',
                'description': 'Cleartext HTTP traffic allowed - MITM risk'
            })
        
        # Check target SDK
        target_sdk = sdk_info.get('targetSdkVersion')
        if target_sdk:
            try:
                sdk_int = int(target_sdk)
                if sdk_int < 28:
                    issues.append({
                        'flag': 'targetSdkVersion',
                        'value': target_sdk,
                        'severity': 'medium',
                        'description': f'Old target SDK ({target_sdk}) - missing modern security features'
                    })
            except:
                pass
        
        return {
            'debuggable': app_attrs.get('debuggable') == 'true',
            'allow_backup': app_attrs.get('allowBackup') != 'false',
            'cleartext_traffic': app_attrs.get('usesCleartextTraffic') == 'true',
            'target_sdk': target_sdk,
            'issues': issues,
            'risk_score': sum(30 if i['severity'] == 'critical' else 20 if i['severity'] == 'high' else 10 for i in issues)
        }
