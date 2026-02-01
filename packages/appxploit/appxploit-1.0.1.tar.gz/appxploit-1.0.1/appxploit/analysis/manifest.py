"""
AndroidManifest.xml Analysis Module
Parses and extracts all data from AndroidManifest.xml
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List


class ManifestAnalyzer:
    """Analyze AndroidManifest.xml"""
    
    # Android namespace
    ANDROID_NS = '{http://schemas.android.com/apk/res/android}'
    
    def __init__(self, extract_dir: Path, config):
        self.extract_dir = extract_dir
        self.config = config
        self.manifest_path = extract_dir / 'AndroidManifest.xml'
    
    def analyze(self) -> Dict[str, Any]:
        """
        Complete manifest analysis
        
        Returns:
            Manifest data including components, permissions, etc.
        """
        if not self.manifest_path.exists():
            return {}
        
        try:
            tree = ET.parse(self.manifest_path)
            root = tree.getroot()
            
            result = {
                'package': root.get('package'),
                'permissions': self._extract_permissions(root),
                'activities': self._extract_activities(root),
                'services': self._extract_services(root),
                'receivers': self._extract_receivers(root),
                'providers': self._extract_providers(root),
                'application': self._extract_application_attrs(root),
                'uses_sdk': self._extract_sdk_info(root),
                'intent_filters': []
            }
            
            return result
            
        except Exception as e:
            if self.config.verbose:
                print(f"Manifest parse error: {str(e)}")
            return {}
    
    def _extract_permissions(self, root) -> List[str]:
        """Extract requested permissions"""
        permissions = []
        for perm in root.findall('uses-permission'):
            name = perm.get(f'{self.ANDROID_NS}name')
            if name:
                permissions.append(name)
        return permissions
    
    def _extract_activities(self, root) -> List[Dict[str, Any]]:
        """Extract activity components"""
        activities = []
        app = root.find('application')
        if app is None:
            return activities
        
        for activity in app.findall('activity'):
            act_data = {
                'name': activity.get(f'{self.ANDROID_NS}name'),
                'exported': activity.get(f'{self.ANDROID_NS}exported'),
                'permission': activity.get(f'{self.ANDROID_NS}permission'),
                'intent_filters': self._extract_intent_filters(activity)
            }
            activities.append(act_data)
        
        return activities
    
    def _extract_services(self, root) -> List[Dict[str, Any]]:
        """Extract service components"""
        services = []
        app = root.find('application')
        if app is None:
            return services
        
        for service in app.findall('service'):
            svc_data = {
                'name': service.get(f'{self.ANDROID_NS}name'),
                'exported': service.get(f'{self.ANDROID_NS}exported'),
                'permission': service.get(f'{self.ANDROID_NS}permission'),
                'intent_filters': self._extract_intent_filters(service)
            }
            services.append(svc_data)
        
        return services
    
    def _extract_receivers(self, root) -> List[Dict[str, Any]]:
        """Extract broadcast receiver components"""
        receivers = []
        app = root.find('application')
        if app is None:
            return receivers
        
        for receiver in app.findall('receiver'):
            rcv_data = {
                'name': receiver.get(f'{self.ANDROID_NS}name'),
                'exported': receiver.get(f'{self.ANDROID_NS}exported'),
                'permission': receiver.get(f'{self.ANDROID_NS}permission'),
                'intent_filters': self._extract_intent_filters(receiver)
            }
            receivers.append(rcv_data)
        
        return receivers
    
    def _extract_providers(self, root) -> List[Dict[str, Any]]:
        """Extract content provider components"""
        providers = []
        app = root.find('application')
        if app is None:
            return providers
        
        for provider in app.findall('provider'):
            prov_data = {
                'name': provider.get(f'{self.ANDROID_NS}name'),
                'authorities': provider.get(f'{self.ANDROID_NS}authorities'),
                'exported': provider.get(f'{self.ANDROID_NS}exported'),
                'permission': provider.get(f'{self.ANDROID_NS}permission'),
                'readPermission': provider.get(f'{self.ANDROID_NS}readPermission'),
                'writePermission': provider.get(f'{self.ANDROID_NS}writePermission'),
                'grantUriPermissions': provider.get(f'{self.ANDROID_NS}grantUriPermissions')
            }
            providers.append(prov_data)
        
        return providers
    
    def _extract_intent_filters(self, component) -> List[Dict[str, Any]]:
        """Extract intent filters from component"""
        filters = []
        
        for intent_filter in component.findall('intent-filter'):
            filter_data = {
                'actions': [],
                'categories': [],
                'data': []
            }
            
            # Actions
            for action in intent_filter.findall('action'):
                name = action.get(f'{self.ANDROID_NS}name')
                if name:
                    filter_data['actions'].append(name)
            
            # Categories
            for category in intent_filter.findall('category'):
                name = category.get(f'{self.ANDROID_NS}name')
                if name:
                    filter_data['categories'].append(name)
            
            # Data (schemes, hosts, paths)
            for data in intent_filter.findall('data'):
                data_info = {
                    'scheme': data.get(f'{self.ANDROID_NS}scheme'),
                    'host': data.get(f'{self.ANDROID_NS}host'),
                    'path': data.get(f'{self.ANDROID_NS}path'),
                    'pathPrefix': data.get(f'{self.ANDROID_NS}pathPrefix'),
                    'pathPattern': data.get(f'{self.ANDROID_NS}pathPattern'),
                }
                filter_data['data'].append(data_info)
            
            filters.append(filter_data)
        
        return filters
    
    def _extract_application_attrs(self, root) -> Dict[str, Any]:
        """Extract application-level attributes"""
        app = root.find('application')
        if app is None:
            return {}
        
        return {
            'debuggable': app.get(f'{self.ANDROID_NS}debuggable'),
            'allowBackup': app.get(f'{self.ANDROID_NS}allowBackup'),
            'usesCleartextTraffic': app.get(f'{self.ANDROID_NS}usesCleartextTraffic'),
            'networkSecurityConfig': app.get(f'{self.ANDROID_NS}networkSecurityConfig'),
            'label': app.get(f'{self.ANDROID_NS}label'),
            'icon': app.get(f'{self.ANDROID_NS}icon')
        }
    
    def _extract_sdk_info(self, root) -> Dict[str, Any]:
        """Extract SDK version information"""
        uses_sdk = root.find('uses-sdk')
        if uses_sdk is None:
            return {}
        
        return {
            'minSdkVersion': uses_sdk.get(f'{self.ANDROID_NS}minSdkVersion'),
            'targetSdkVersion': uses_sdk.get(f'{self.ANDROID_NS}targetSdkVersion'),
            'maxSdkVersion': uses_sdk.get(f'{self.ANDROID_NS}maxSdkVersion')
        }
