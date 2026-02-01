"""
APK Fingerprinting Module
Extracts metadata and identifies characteristics of the APK
"""

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional
from colorama import Fore, Style


class APKFingerprint:
    """APK fingerprinting and metadata extraction"""
    
    def __init__(self, extract_dir: Path, config):
        self.extract_dir = extract_dir
        self.config = config
        self.manifest_path = extract_dir / 'AndroidManifest.xml'
        self.apktool_yml = extract_dir / 'apktool.yml'
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete fingerprinting analysis
        
        Returns:
            Dictionary with fingerprint data
        """
        result = {
            'package_name': None,
            'version_name': None,
            'version_code': None,
            'min_sdk': None,
            'target_sdk': None,
            'compile_sdk': None,
            'sha256': None,
            'obfuscated': False,
            'framework': 'native',
            'libraries': []
        }
        
        try:
            # Parse manifest
            if self.manifest_path.exists():
                manifest_data = self._parse_manifest()
                result.update(manifest_data)
            
            # Parse apktool.yml
            if self.apktool_yml.exists():
                apktool_data = self._parse_apktool_yml()
                result.update(apktool_data)
            
            # Detect obfuscation
            result['obfuscated'] = self._detect_obfuscation()
            
            # Detect framework
            result['framework'] = self._detect_framework()
            
            # Detect libraries
            result['libraries'] = self._detect_libraries()
            
        except Exception as e:
            if self.config.verbose:
                print(f"{Fore.YELLOW}[!] Fingerprint warning: {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def _parse_manifest(self) -> Dict[str, Any]:
        """Parse AndroidManifest.xml for basic info"""
        try:
            tree = ET.parse(self.manifest_path)
            root = tree.getroot()
            
            # Get namespace
            ns = {'android': 'http://schemas.android.com/apk/res/android'}
            
            data = {}
            
            # Package name
            data['package_name'] = root.get('package')
            
            # Version info
            data['version_name'] = root.get('{http://schemas.android.com/apk/res/android}versionName')
            data['version_code'] = root.get('{http://schemas.android.com/apk/res/android}versionCode')
            
            # SDK versions
            uses_sdk = root.find('uses-sdk')
            if uses_sdk is not None:
                data['min_sdk'] = uses_sdk.get('{http://schemas.android.com/apk/res/android}minSdkVersion')
                data['target_sdk'] = uses_sdk.get('{http://schemas.android.com/apk/res/android}targetSdkVersion')
            
            return data
            
        except Exception as e:
            if self.config.verbose:
                print(f"{Fore.YELLOW}[!] Manifest parse warning: {str(e)}{Style.RESET_ALL}")
            return {}
    
    def _parse_apktool_yml(self) -> Dict[str, Any]:
        """Parse apktool.yml for additional info"""
        try:
            import yaml
            
            with open(self.apktool_yml, 'r') as f:
                data = yaml.safe_load(f)
            
            result = {}
            
            if 'sdkInfo' in data:
                sdk_info = data['sdkInfo']
                if 'minSdkVersion' in sdk_info:
                    result['min_sdk'] = str(sdk_info['minSdkVersion'])
                if 'targetSdkVersion' in sdk_info:
                    result['target_sdk'] = str(sdk_info['targetSdkVersion'])
            
            return result
            
        except Exception:
            return {}
    
    def _detect_obfuscation(self) -> bool:
        """
        Detect if APK is obfuscated (ProGuard/R8)
        Looks for short class names like 'a.b.c'
        """
        try:
            smali_dir = self.extract_dir / 'smali'
            if not smali_dir.exists():
                return False
            
            # Check for single-letter package names (common in obfuscation)
            for item in smali_dir.iterdir():
                if item.is_dir() and len(item.name) == 1:
                    return True
            
            # Check for classes with single-letter names
            smali_files = list(smali_dir.rglob('*.smali'))
            if len(smali_files) > 0:
                # Sample first 10 files
                sample = smali_files[:10]
                short_names = sum(1 for f in sample if len(f.stem) <= 2)
                if short_names >= 5:  # If half are short names
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _detect_framework(self) -> str:
        """
        Detect app framework (React Native, Flutter, Xamarin, etc.)
        """
        try:
            lib_dir = self.extract_dir / 'lib'
            assets_dir = self.extract_dir / 'assets'
            
            # React Native
            if assets_dir.exists():
                if (assets_dir / 'index.android.bundle').exists():
                    return 'react_native'
            
            # Flutter
            if lib_dir.exists():
                for arch_dir in lib_dir.iterdir():
                    if (arch_dir / 'libflutter.so').exists():
                        return 'flutter'
            
            # Xamarin
            if (self.extract_dir / 'assemblies').exists():
                return 'xamarin'
            
            # Cordova/PhoneGap
            if assets_dir.exists():
                if (assets_dir / 'www').exists():
                    return 'cordova'
            
            # Unity
            if lib_dir.exists():
                for arch_dir in lib_dir.iterdir():
                    if (arch_dir / 'libunity.so').exists():
                        return 'unity'
            
            return 'native'
            
        except Exception:
            return 'native'
    
    def _detect_libraries(self) -> list:
        """Detect common libraries and SDKs"""
        libraries = []
        
        try:
            lib_dir = self.extract_dir / 'lib'
            
            if lib_dir.exists():
                # Common security/networking libraries
                lib_patterns = {
                    'okhttp': 'OkHttp',
                    'retrofit': 'Retrofit',
                    'volley': 'Volley',
                    'firebase': 'Firebase',
                    'facebook': 'Facebook SDK',
                    'crashlytics': 'Crashlytics',
                    'sqlcipher': 'SQLCipher',
                }
                
                for arch_dir in lib_dir.iterdir():
                    if arch_dir.is_dir():
                        for so_file in arch_dir.glob('*.so'):
                            name_lower = so_file.name.lower()
                            for pattern, lib_name in lib_patterns.items():
                                if pattern in name_lower and lib_name not in libraries:
                                    libraries.append(lib_name)
            
        except Exception:
            pass
        
        return libraries
