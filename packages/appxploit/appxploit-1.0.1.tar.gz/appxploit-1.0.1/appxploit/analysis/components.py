"""Component Analysis - Identifies dangerous exported components"""

from typing import Dict, Any, List


class ComponentAnalyzer:
    """Analyze Android components for security issues"""
    
    def __init__(self, manifest_data: Dict[str, Any], config):
        self.manifest = manifest_data
        self.config = config
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze components for security issues"""
        return {
            'exported_activities': self._find_exported_activities(),
            'exported_services': self._find_exported_services(),
            'exported_receivers': self._find_exported_receivers(),
            'exported_providers': self._find_exported_providers(),
            'deeplinks': self._find_deeplinks(),
            'dangerous_exports': self._find_dangerous_exports()
        }
    
    def _is_exported(self, component: Dict[str, Any]) -> bool:
        """Check if component is exported"""
        exported = component.get('exported')
        has_intent_filters = len(component.get('intent_filters', [])) > 0
        
        # If exported is explicitly set, use that
        if exported is not None:
            return exported == 'true'
        
        # If has intent filters and no explicit exported, it's exported by default
        return has_intent_filters
    
    def _find_exported_activities(self) -> List[Dict[str, Any]]:
        """Find exported activities"""
        exported = []
        for activity in self.manifest.get('activities', []):
            if self._is_exported(activity):
                exported.append(activity)
        return exported
    
    def _find_exported_services(self) -> List[Dict[str, Any]]:
        """Find exported services"""
        exported = []
        for service in self.manifest.get('services', []):
            if self._is_exported(service):
                exported.append(service)
        return exported
    
    def _find_exported_receivers(self) -> List[Dict[str, Any]]:
        """Find exported receivers"""
        exported = []
        for receiver in self.manifest.get('receivers', []):
            if self._is_exported(receiver):
                exported.append(receiver)
        return exported
    
    def _find_exported_providers(self) -> List[Dict[str, Any]]:
        """Find exported content providers"""
        exported = []
        for provider in self.manifest.get('providers', []):
            if self._is_exported(provider):
                exported.append(provider)
        return exported
    
    def _find_deeplinks(self) -> List[Dict[str, Any]]:
        """Find deep link configurations"""
        deeplinks = []
        
        for activity in self.manifest.get('activities', []):
            for intent_filter in activity.get('intent_filters', []):
                # Check for VIEW action with http/https schemes
                has_view = 'android.intent.action.VIEW' in intent_filter.get('actions', [])
                
                if has_view:
                    for data in intent_filter.get('data', []):
                        scheme = data.get('scheme')
                        if scheme in ['http', 'https'] or scheme:
                            deeplinks.append({
                                'activity': activity.get('name'),
                                'scheme': scheme,
                                'host': data.get('host'),
                                'path': data.get('path') or data.get('pathPrefix') or data.get('pathPattern')
                            })
        
        return deeplinks
    
    def _find_dangerous_exports(self) -> List[Dict[str, Any]]:
        """Find potentially dangerous exported components"""
        dangerous = []
        
        # Exported providers without permissions
        for provider in self.manifest.get('providers', []):
            if self._is_exported(provider):
                if not provider.get('permission') and not provider.get('readPermission'):
                    dangerous.append({
                        'type': 'provider',
                        'name': provider.get('name'),
                        'issue': 'Exported without permission protection',
                        'severity': 'high'
                    })
        
        # Exported activities with deep links but no validation
        for activity in self.manifest.get('activities', []):
            if self._is_exported(activity):
                for intent_filter in activity.get('intent_filters', []):
                    if intent_filter.get('data'):
                        dangerous.append({
                            'type': 'activity',
                            'name': activity.get('name'),
                            'issue': 'Deep link without validation (potential)',
                            'severity': 'medium'
                        })
        
        return dangerous
