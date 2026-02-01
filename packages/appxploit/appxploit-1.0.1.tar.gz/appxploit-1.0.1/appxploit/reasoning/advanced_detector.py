"""
Advanced Vulnerability Detection Module
Detects real-world Android security vulnerabilities using pattern matching and code analysis
"""

import re
from typing import List, Dict, Any
from pathlib import Path


class AdvancedDetector:
    """Advanced vulnerability detector for real-world Android security issues"""
    
    def __init__(self, config):
        self.config = config
        self.advanced_patterns = config.advanced_patterns
    
    def detect(self, decompiled_dir: Path, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect advanced vulnerabilities
        
        Args:
            decompiled_dir: Path to decompiled Java code
            analysis_results: Results from static analysis
            
        Returns:
            List of advanced vulnerability findings
        """
        vulnerabilities = []
        
        # Scan all Java files
        java_files = list(decompiled_dir.rglob('*.java'))
        
        if self.config.verbose:
            print(f"[*] Scanning {len(java_files)} Java files for advanced vulnerabilities...")
        
        # 1. Auth & Session Logic Vulnerabilities
        vulnerabilities.extend(self._detect_auth_issues(java_files))
        
        # 2. IDOR & Access Control Vulnerabilities
        vulnerabilities.extend(self._detect_idor_issues(java_files))
        
        # 3. Crypto & Data Protection Vulnerabilities
        vulnerabilities.extend(self._detect_crypto_issues(java_files))
        
        # 4. WebView Security Vulnerabilities
        vulnerabilities.extend(self._detect_webview_issues(java_files))
        
        # 5. Storage & Data Leak Vulnerabilities
        vulnerabilities.extend(self._detect_storage_issues(java_files))
        
        # 6. Component Abuse Vulnerabilities
        vulnerabilities.extend(self._detect_component_abuse(java_files, analysis_results))
        
        # 7. OTP & Verification Vulnerabilities
        vulnerabilities.extend(self._detect_otp_issues(java_files))
        
        # 8. Payment & Financial Vulnerabilities
        vulnerabilities.extend(self._detect_payment_issues(java_files))
        
        return vulnerabilities
    
    def _scan_files_for_patterns(self, java_files: List[Path], pattern_category: str) -> List[Dict[str, Any]]:
        """
        Scan files for specific pattern category
        
        REASONING: Centralized pattern scanning reduces code duplication
        """
        findings = []
        
        if pattern_category not in self.advanced_patterns:
            return findings
        
        patterns = self.advanced_patterns[pattern_category]
        
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                relative_path = str(java_file).replace('\\', '/')
                
                # Extract package-style path
                if '/sources/' in relative_path:
                    package_path = relative_path.split('/sources/')[-1]
                else:
                    package_path = java_file.name
                
                for pattern_name, pattern_data in patterns.items():
                    if isinstance(pattern_data, list):
                        pattern_list = pattern_data
                    else:
                        pattern_list = [pattern_data]
                    
                    for pattern_info in pattern_list:
                        pattern = pattern_info['pattern']
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        
                        for match in matches:
                            # Get line number
                            line_num = content[:match.start()].count('\n') + 1
                            
                            # Get context (surrounding lines)
                            lines = content.split('\n')
                            context_start = max(0, line_num - 2)
                            context_end = min(len(lines), line_num + 2)
                            context = '\n'.join(lines[context_start:context_end])
                            
                            findings.append({
                                'title': pattern_info['description'],
                                'severity': pattern_info['severity'],
                                'cwe': pattern_info.get('cwe', 'CWE-Unknown'),
                                'category': pattern_category,
                                'description': pattern_info['description'],
                                'file': package_path,
                                'line': line_num,
                                'matched_text': match.group(0),
                                'context': context,
                                'pattern_confidence': pattern_info.get('confidence', 0.7),
                                'evidence': {
                                    'file': package_path,
                                    'line': line_num,
                                    'value_preview': match.group(0)[:100]
                                }
                            })
            
            except Exception as e:
                if self.config.verbose:
                    print(f"[!] Error scanning {java_file}: {str(e)}")
                continue
        
        return findings
    
    def _detect_auth_issues(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect authentication and session logic vulnerabilities
        
        REASONING: Client-side auth checks can be bypassed by modifying the APK
        """
        findings = self._scan_files_for_patterns(java_files, 'auth_bypass')
        
        # Add impact and remediation
        for finding in findings:
            finding['impact'] = "Authentication can be bypassed by modifying client-side checks, allowing unauthorized access"
            finding['remediation'] = "Move all authentication and authorization logic to the server-side. Never trust client-side checks."
        
        return findings
    
    def _detect_idor_issues(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect IDOR and access control vulnerabilities
        
        REASONING: User-controlled IDs in URLs/APIs can lead to unauthorized data access
        """
        findings = self._scan_files_for_patterns(java_files, 'idor_patterns')
        
        for finding in findings:
            finding['impact'] = "Insecure Direct Object References allow accessing other users' data by manipulating IDs"
            finding['remediation'] = "Implement server-side authorization checks for all object access. Use indirect references or UUIDs."
        
        return findings
    
    def _detect_crypto_issues(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect cryptography and data protection vulnerabilities
        
        REASONING: Weak crypto algorithms and hardcoded keys compromise data security
        """
        findings = self._scan_files_for_patterns(java_files, 'crypto_weak')
        
        for finding in findings:
            if 'MD5' in finding['matched_text'] or 'SHA1' in finding['matched_text'] or 'SHA-1' in finding['matched_text']:
                finding['impact'] = "Weak hash algorithms are vulnerable to collision attacks and should not be used for security purposes"
                finding['remediation'] = "Use SHA-256 or SHA-3 for hashing. For passwords, use bcrypt, scrypt, or Argon2."
            elif 'ECB' in finding['matched_text'] or 'DES' in finding['matched_text']:
                finding['impact'] = "Weak encryption algorithms/modes can be broken, exposing sensitive data"
                finding['remediation'] = "Use AES with GCM or CBC mode. Never use ECB mode or DES."
            elif 'Key' in finding['title'] or 'key' in finding['matched_text'].lower():
                finding['impact'] = "Hardcoded encryption keys can be extracted from the APK, compromising all encrypted data"
                finding['remediation'] = "Use Android Keystore for key storage. Generate keys at runtime, never hardcode them."
            else:
                finding['impact'] = "Cryptographic weakness compromises data confidentiality and integrity"
                finding['remediation'] = "Use industry-standard cryptographic libraries and follow best practices"
        
        return findings
    
    def _detect_webview_issues(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect WebView security vulnerabilities
        
        REASONING: WebView misconfigurations can lead to XSS, RCE, and data leakage
        """
        findings = self._scan_files_for_patterns(java_files, 'webview_risks')
        
        for finding in findings:
            if 'JavaScript' in finding['title']:
                finding['impact'] = "JavaScript-enabled WebViews are vulnerable to XSS attacks if loading untrusted content"
                finding['remediation'] = "Disable JavaScript if not needed. If required, validate all loaded URLs and implement CSP."
            elif 'addJavascriptInterface' in finding['matched_text']:
                finding['impact'] = "JavaScript interfaces can lead to Remote Code Execution on Android < 4.2 or if improperly used"
                finding['remediation'] = "Avoid addJavascriptInterface. If required, use @JavascriptInterface annotation and validate all inputs."
            elif 'File' in finding['title']:
                finding['impact'] = "File access in WebViews can expose local files to JavaScript code"
                finding['remediation'] = "Disable file access unless absolutely necessary. Use content:// URIs instead of file:// URIs."
            else:
                finding['impact'] = "WebView misconfiguration creates attack surface for web-based exploits"
                finding['remediation'] = "Follow WebView security best practices: disable unnecessary features, validate URLs, implement CSP"
        
        return findings
    
    def _detect_storage_issues(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect storage and data leak vulnerabilities
        
        REASONING: Sensitive data in insecure storage can be extracted via backup or rooted devices
        """
        findings = self._scan_files_for_patterns(java_files, 'storage_leaks')
        
        for finding in findings:
            if 'SharedPreferences' in finding['matched_text']:
                finding['impact'] = "Sensitive data in SharedPreferences can be extracted via ADB backup or on rooted devices"
                finding['remediation'] = "Use EncryptedSharedPreferences for sensitive data. Never store passwords or tokens in plain text."
            elif 'Log' in finding['matched_text']:
                finding['impact'] = "Sensitive data in logs can be accessed by other apps with READ_LOGS permission or via ADB"
                finding['remediation'] = "Remove all logging of sensitive data in production builds. Use ProGuard to strip debug logs."
            elif 'WORLD_READABLE' in finding['matched_text']:
                finding['impact'] = "World-readable files can be accessed by any app on the device, exposing sensitive data"
                finding['remediation'] = "Never use MODE_WORLD_READABLE (deprecated). Use MODE_PRIVATE for all files."
            else:
                finding['impact'] = "Insecure data storage exposes sensitive information to attackers"
                finding['remediation'] = "Encrypt sensitive data at rest. Use Android Keystore and EncryptedSharedPreferences."
        
        return findings
    
    def _detect_component_abuse(self, java_files: List[Path], analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect advanced component abuse vulnerabilities
        
        REASONING: Exported components with dangerous operations can be abused by malicious apps
        """
        findings = self._scan_files_for_patterns(java_files, 'component_abuse')
        
        for finding in findings:
            if 'PendingIntent' in finding['matched_text']:
                finding['impact'] = "Mutable PendingIntents can be hijacked by malicious apps to perform unauthorized actions"
                finding['remediation'] = "Use FLAG_IMMUTABLE for PendingIntents on Android 12+. Validate all intent extras."
            else:
                finding['impact'] = "Exported components performing state-changing operations can be abused by malicious apps"
                finding['remediation'] = "Add permission protection to exported components. Validate all inputs and check caller identity."
        
        return findings
    
    def _detect_otp_issues(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect OTP and verification vulnerabilities
        
        REASONING: Client-side OTP validation can be bypassed
        """
        findings = self._scan_files_for_patterns(java_files, 'otp_client_side')
        
        for finding in findings:
            finding['impact'] = "Client-side OTP/PIN validation can be bypassed by modifying the APK or using a debugger"
            finding['remediation'] = "Always validate OTP/PIN on the server-side. Client-side validation is only for UX."
        
        return findings
    
    def _detect_payment_issues(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect payment and financial vulnerabilities
        
        REASONING: Client-side price calculations can be manipulated
        """
        findings = self._scan_files_for_patterns(java_files, 'payment_risks')
        
        for finding in findings:
            finding['impact'] = "Client-side payment logic can be manipulated to bypass payments or alter prices"
            finding['remediation'] = "All payment calculations and verifications must be done server-side. Never trust client-side values."
        
        return findings
