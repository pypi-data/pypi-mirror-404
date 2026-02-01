"""
Risk Estimation Module
Estimates attack surface and risk profile of the APK
"""

from typing import Dict, Any


class RiskEstimator:
    """Estimate risk profile and attack surface"""
    
    def __init__(self, fingerprint: Dict[str, Any], config):
        self.fingerprint = fingerprint
        self.config = config
    
    def estimate(self) -> Dict[str, Any]:
        """
        Estimate risk profile based on fingerprint
        
        Returns:
            Risk estimation data
        """
        result = {
            'risk_level': 'medium',
            'risk_score': 0,
            'attack_surface': 'medium',
            'priority': 'normal',
            'factors': []
        }
        
        score = 0
        factors = []
        
        # Check SDK version risks
        target_sdk = self.fingerprint.get('target_sdk')
        if target_sdk:
            try:
                sdk_int = int(target_sdk)
                if sdk_int < 23:  # Android 6.0
                    score += 30
                    factors.append('Very old target SDK (< 23) - high risk')
                elif sdk_int < 28:  # Android 9.0
                    score += 15
                    factors.append('Old target SDK (< 28) - medium risk')
                elif sdk_int < 30:  # Android 11
                    score += 5
                    factors.append('Slightly outdated target SDK')
            except:
                pass
        
        # Check obfuscation
        if not self.fingerprint.get('obfuscated', False):
            score += 10
            factors.append('No code obfuscation - easier to analyze')
        else:
            factors.append('Code is obfuscated')
        
        # Check framework
        framework = self.fingerprint.get('framework', 'native')
        if framework in ['react_native', 'cordova']:
            score += 15
            factors.append(f'{framework.title()} framework - hybrid app with web vulnerabilities')
        elif framework == 'flutter':
            score += 5
            factors.append('Flutter framework - modern but still analyzable')
        
        # Check libraries
        libraries = self.fingerprint.get('libraries', [])
        if 'Firebase' in libraries:
            score += 10
            factors.append('Firebase SDK detected - potential config exposure')
        
        if 'Facebook SDK' in libraries:
            score += 5
            factors.append('Facebook SDK - potential OAuth issues')
        
        # Determine risk level
        if score >= 50:
            result['risk_level'] = 'critical'
            result['priority'] = 'high'
        elif score >= 30:
            result['risk_level'] = 'high'
            result['priority'] = 'high'
        elif score >= 15:
            result['risk_level'] = 'medium'
            result['priority'] = 'normal'
        else:
            result['risk_level'] = 'low'
            result['priority'] = 'low'
        
        result['risk_score'] = score
        result['factors'] = factors
        
        # Estimate attack surface
        if score >= 40:
            result['attack_surface'] = 'large'
        elif score >= 20:
            result['attack_surface'] = 'medium'
        else:
            result['attack_surface'] = 'small'
        
        return result
