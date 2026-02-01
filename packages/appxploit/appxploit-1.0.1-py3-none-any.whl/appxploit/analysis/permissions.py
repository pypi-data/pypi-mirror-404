"""Permission Analysis"""

from typing import Dict, Any, List


class PermissionAnalyzer:
    """Analyze Android permissions"""
    
    # Dangerous permissions that require user approval
    DANGEROUS_PERMISSIONS = {
        'android.permission.READ_CONTACTS', 'android.permission.WRITE_CONTACTS',
        'android.permission.READ_CALENDAR', 'android.permission.WRITE_CALENDAR',
        'android.permission.CAMERA', 'android.permission.RECORD_AUDIO',
        'android.permission.ACCESS_FINE_LOCATION', 'android.permission.ACCESS_COARSE_LOCATION',
        'android.permission.READ_PHONE_STATE', 'android.permission.CALL_PHONE',
        'android.permission.READ_SMS', 'android.permission.SEND_SMS',
        'android.permission.READ_EXTERNAL_STORAGE', 'android.permission.WRITE_EXTERNAL_STORAGE',
        'android.permission.ACCESS_MEDIA_LOCATION'
    }
    
    def __init__(self, manifest_data: Dict[str, Any], config):
        self.manifest = manifest_data
        self.config = config
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze permissions"""
        permissions = self.manifest.get('permissions', [])
        
        dangerous = [p for p in permissions if p in self.DANGEROUS_PERMISSIONS]
        
        return {
            'all_permissions': permissions,
            'dangerous_permissions': dangerous,
            'permission_count': len(permissions),
            'risk_score': len(dangerous) * 10,
            'over_privileged': len(dangerous) > 5
        }
