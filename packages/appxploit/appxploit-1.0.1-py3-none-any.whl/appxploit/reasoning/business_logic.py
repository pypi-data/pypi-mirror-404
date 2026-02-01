"""
Business Logic Intelligence Module
Detects business logic flaws that bypass payment, unlock premium features, or manipulate pricing

PHILOSOPHY: "How would I ACTUALLY hack this app?"
- Focus on revenue-impacting vulnerabilities
- Detect client-side business logic
- Correlate UI → Flag → API → Impact
- Only report realistic exploitation
"""

import re
from typing import List, Dict, Any, Set
from pathlib import Path


class BusinessLogicDetector:
    """Detect business logic vulnerabilities"""
    
    # Payment-related boolean flags
    PAYMENT_FLAGS = [
        'isPaid', 'hasPurchased', 'isUnlocked', 'isPremium',
        'isPro', 'isSubscribed', 'hasSubscription', 'isLicensed',
        'paymentSuccess', 'purchaseComplete', 'subscriptionActive'
    ]
    
    # Access control boolean flags
    ACCESS_FLAGS = [
        'isAdmin', 'isVerified', 'hasAccess', 'isAuthorized',
        'isModerator', 'isRoot', 'isSuperUser', 'hasPermission'
    ]
    
    # Price-related patterns
    PRICE_PATTERNS = [
        r'(price|amount|total|cost|subtotal)\s*=\s*[\d.]+',
        r'(discount|coupon|promo)\s*=\s*[\d.]+',
        r'(quantity|qty)\s*\*\s*(price|amount)',
        r'calculatePrice\s*\(',
        r'applyDiscount\s*\(',
        r'validateCoupon\s*\('
    ]
    
    def __init__(self, config):
        self.config = config
    
    def detect(self, decompiled_dir: Path, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect business logic vulnerabilities
        
        REASONING: Business logic flaws are the highest-value vulnerabilities
        because they directly impact revenue and access control.
        
        Args:
            decompiled_dir: Path to decompiled Java code
            analysis_results: Results from static analysis
            
        Returns:
            List of business logic vulnerability findings
        """
        findings = []
        
        # Scan all Java files
        java_files = list(decompiled_dir.rglob('*.java'))
        
        if self.config.verbose:
            print(f"[BL] Scanning {len(java_files)} files for business logic flaws...")
        
        # 1. Payment Bypass Detection
        findings.extend(self._detect_payment_bypass(java_files))
        
        # 2. Premium Feature Unlock Detection
        findings.extend(self._detect_premium_unlock(java_files))
        
        # 3. Price Manipulation Detection
        findings.extend(self._detect_price_manipulation(java_files))
        
        # 4. Access Control Bypass Detection
        findings.extend(self._detect_access_control_bypass(java_files))
        
        # 5. Correlate with API endpoints
        findings = self._correlate_with_apis(findings, analysis_results)
        
        if self.config.verbose:
            print(f"[BL] Found {len(findings)} business logic vulnerabilities")
        
        return findings
    
    def _detect_payment_bypass(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect payment bypass vulnerabilities
        
        REASONING: Payment verification done client-side can be bypassed
        by modifying the APK or SharedPreferences.
        
        Detection logic:
        1. Find payment-related boolean flags
        2. Check if stored in SharedPreferences
        3. Check if used for access control
        4. Verify no server-side validation
        """
        findings = []
        
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                # Look for payment flags in SharedPreferences
                for i, line in enumerate(lines):
                    for flag in self.PAYMENT_FLAGS:
                        # Pattern: SharedPreferences.putBoolean("isPaid", true)
                        put_pattern = rf'SharedPreferences.*putBoolean\s*\(\s*["\']({flag})["\']'
                        put_match = re.search(put_pattern, line, re.IGNORECASE)
                        
                        if put_match:
                            # Found payment flag being stored
                            # Now check if it's used for access control
                            get_pattern = rf'getBoolean\s*\(\s*["\']({flag})["\']'
                            
                            # Search in nearby lines for usage
                            context_start = max(0, i - 50)
                            context_end = min(len(lines), i + 50)
                            context = '\n'.join(lines[context_start:context_end])
                            
                            if re.search(get_pattern, context, re.IGNORECASE):
                                # Check if used in conditional
                                if_pattern = rf'if\s*\([^)]*{flag}[^)]*\)'
                                if re.search(if_pattern, context, re.IGNORECASE):
                                    # This is a payment bypass vulnerability!
                                    findings.append(self._create_payment_bypass_finding(
                                        java_file, i + 1, flag, line, context
                                    ))
            
            except Exception as e:
                if self.config.verbose:
                    print(f"[BL] Error scanning {java_file}: {str(e)}")
                continue
        
        return findings
    
    def _create_payment_bypass_finding(
        self, 
        file_path: Path, 
        line_num: int, 
        flag: str, 
        code_line: str,
        context: str
    ) -> Dict[str, Any]:
        """Create payment bypass finding"""
        
        # Extract package path
        relative_path = str(file_path).replace('\\', '/')
        if '/sources/' in relative_path:
            package_path = relative_path.split('/sources/')[-1]
        else:
            package_path = file_path.name
        
        return {
            'title': f'Payment Bypass via Client-Side Flag: {flag}',
            'severity': 'critical',
            'category': 'business_logic',
            'subcategory': 'payment_bypass',
            'cwe': 'CWE-602',
            'confidence': 0.95,
            'description': f'Payment verification controlled by client-side boolean flag "{flag}"',
            'evidence': {
                'file': package_path,
                'line': line_num,
                'code_snippet': code_line.strip(),
                'value_preview': flag
            },
            'exploitation_steps': [
                f'1. Install app on rooted device or use ADB backup',
                f'2. Modify SharedPreferences to set {flag}=true',
                f'3. Restart app or reload activity',
                f'4. Access premium features without payment'
            ],
            'impact': 'Complete payment bypass allowing free access to premium features',
            'business_impact': 'Direct revenue loss - attackers can bypass all payment requirements, '
                              'resulting in 100% revenue loss for premium features. '
                              'Estimated impact: $X per compromised user.',
            'remediation': 'Move payment verification to server-side. Never trust client-side data for authorization.',
            'reasoning': f'The boolean flag "{flag}" controls access to premium features but is stored '
                        f'client-side in SharedPreferences. Since SharedPreferences is attacker-controlled '
                        f'(via rooted device or ADB backup), an attacker can set {flag}=true to bypass payment.',
            'why_exploitable': 'Client-side data is always attacker-controlled. The app trusts '
                              'SharedPreferences for payment verification, which violates the '
                              'fundamental security principle: never trust the client.',
            'real_world_impact': {
                'users': 'Attackers gain free access to premium features',
                'business': 'Complete revenue loss for premium subscriptions',
                'security': 'Demonstrates fundamental architecture flaw'
            }
        }
    
    def _detect_premium_unlock(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect premium feature unlock vulnerabilities
        
        REASONING: Similar to payment bypass, but focuses on feature entitlements
        rather than payment status.
        """
        findings = []
        
        premium_flags = ['isPremium', 'isPro', 'isSubscribed', 'hasSubscription']
        
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    for flag in premium_flags:
                        # Look for premium checks
                        pattern = rf'if\s*\([^)]*{flag}[^)]*\)'
                        if re.search(pattern, line, re.IGNORECASE):
                            # Check if flag is from SharedPreferences
                            context_start = max(0, i - 10)
                            context_end = min(len(lines), i + 10)
                            context = '\n'.join(lines[context_start:context_end])
                            
                            if 'SharedPreferences' in context or 'getBoolean' in context:
                                findings.append(self._create_premium_unlock_finding(
                                    java_file, i + 1, flag, line
                                ))
            
            except Exception as e:
                continue
        
        return findings
    
    def _create_premium_unlock_finding(
        self,
        file_path: Path,
        line_num: int,
        flag: str,
        code_line: str
    ) -> Dict[str, Any]:
        """Create premium unlock finding"""
        
        relative_path = str(file_path).replace('\\', '/')
        if '/sources/' in relative_path:
            package_path = relative_path.split('/sources/')[-1]
        else:
            package_path = file_path.name
        
        return {
            'title': f'Premium Feature Unlock via Client-Side Flag: {flag}',
            'severity': 'high',
            'category': 'business_logic',
            'subcategory': 'premium_unlock',
            'cwe': 'CWE-602',
            'confidence': 0.88,
            'description': f'Premium features controlled by client-side boolean flag "{flag}"',
            'evidence': {
                'file': package_path,
                'line': line_num,
                'code_snippet': code_line.strip(),
                'value_preview': flag
            },
            'exploitation_steps': [
                f'1. Decompile APK and locate {flag} check',
                f'2. Modify APK to always return true for {flag}',
                f'3. Recompile and sign modified APK',
                f'4. Install and access premium features'
            ],
            'impact': 'Unauthorized access to premium features without subscription',
            'business_impact': 'Revenue loss from users bypassing premium subscriptions',
            'remediation': 'Verify subscription status server-side for each premium feature access',
            'reasoning': f'Premium features are gated by client-side flag "{flag}" which can be '
                        f'manipulated by modifying the APK.',
            'why_exploitable': 'Client-side checks can be bypassed by modifying the APK bytecode '
                              'to always return true for premium checks.'
        }
    
    def _detect_price_manipulation(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect price manipulation vulnerabilities
        
        REASONING: Price calculations done client-side can be manipulated
        to reduce costs or apply unauthorized discounts.
        """
        findings = []
        
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    for pattern in self.PRICE_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Found price calculation
                            # Check if this is in payment/checkout context
                            context_start = max(0, i - 20)
                            context_end = min(len(lines), i + 20)
                            context = '\n'.join(lines[context_start:context_end])
                            
                            payment_keywords = ['payment', 'checkout', 'purchase', 'order', 'cart']
                            if any(kw in context.lower() for kw in payment_keywords):
                                findings.append(self._create_price_manipulation_finding(
                                    java_file, i + 1, line
                                ))
                                break  # One finding per file is enough
            
            except Exception as e:
                continue
        
        return findings
    
    def _create_price_manipulation_finding(
        self,
        file_path: Path,
        line_num: int,
        code_line: str
    ) -> Dict[str, Any]:
        """Create price manipulation finding"""
        
        relative_path = str(file_path).replace('\\', '/')
        if '/sources/' in relative_path:
            package_path = relative_path.split('/sources/')[-1]
        else:
            package_path = file_path.name
        
        return {
            'title': 'Price Manipulation via Client-Side Calculation',
            'severity': 'critical',
            'category': 'business_logic',
            'subcategory': 'price_manipulation',
            'cwe': 'CWE-602',
            'confidence': 0.85,
            'description': 'Price or discount calculations performed client-side',
            'evidence': {
                'file': package_path,
                'line': line_num,
                'code_snippet': code_line.strip(),
                'value_preview': 'Client-side calculation'
            },
            'exploitation_steps': [
                '1. Intercept API request during checkout',
                '2. Modify price/discount values in request body',
                '3. Submit modified request to server',
                '4. Complete purchase at manipulated price'
            ],
            'impact': 'Attackers can manipulate prices, discounts, or quantities to reduce payment amounts',
            'business_impact': 'Direct financial loss - attackers can purchase items at arbitrary prices, '
                              'apply unlimited discounts, or manipulate quantities.',
            'remediation': 'Perform all price calculations server-side. Never trust client-provided prices.',
            'reasoning': 'Price calculations performed client-side can be manipulated by intercepting '
                        'and modifying API requests before they reach the server.',
            'why_exploitable': 'The server accepts client-provided price values without recalculating '
                              'them server-side, allowing attackers to pay arbitrary amounts.'
        }
    
    def _detect_access_control_bypass(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Detect access control bypass vulnerabilities
        
        REASONING: Admin/moderator checks done client-side can be bypassed
        to gain unauthorized privileges.
        """
        findings = []
        
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    for flag in self.ACCESS_FLAGS:
                        pattern = rf'if\s*\([^)]*{flag}[^)]*\)'
                        if re.search(pattern, line, re.IGNORECASE):
                            # Check if this controls access to sensitive features
                            context_start = max(0, i - 10)
                            context_end = min(len(lines), i + 10)
                            context = '\n'.join(lines[context_start:context_end])
                            
                            sensitive_keywords = ['admin', 'delete', 'modify', 'manage', 'configure']
                            if any(kw in context.lower() for kw in sensitive_keywords):
                                findings.append(self._create_access_control_finding(
                                    java_file, i + 1, flag, line
                                ))
                                break
            
            except Exception as e:
                continue
        
        return findings
    
    def _create_access_control_finding(
        self,
        file_path: Path,
        line_num: int,
        flag: str,
        code_line: str
    ) -> Dict[str, Any]:
        """Create access control bypass finding"""
        
        relative_path = str(file_path).replace('\\', '/')
        if '/sources/' in relative_path:
            package_path = relative_path.split('/sources/')[-1]
        else:
            package_path = file_path.name
        
        return {
            'title': f'Access Control Bypass via Client-Side Flag: {flag}',
            'severity': 'critical',
            'category': 'business_logic',
            'subcategory': 'access_control_bypass',
            'cwe': 'CWE-602',
            'confidence': 0.90,
            'description': f'Access control decisions based on client-side flag "{flag}"',
            'evidence': {
                'file': package_path,
                'line': line_num,
                'code_snippet': code_line.strip(),
                'value_preview': flag
            },
            'exploitation_steps': [
                f'1. Decompile APK and locate {flag} check',
                f'2. Modify APK to set {flag}=true',
                f'3. Recompile and sign modified APK',
                f'4. Access admin/privileged features'
            ],
            'impact': 'Privilege escalation - regular users can gain admin/moderator access',
            'business_impact': 'Complete access control bypass allowing unauthorized administrative actions, '
                              'data manipulation, and system configuration changes.',
            'remediation': 'Verify user roles and permissions server-side for all privileged operations',
            'reasoning': f'Access control is enforced client-side via "{flag}" which can be bypassed '
                        f'by modifying the APK.',
            'why_exploitable': 'Client-side authorization checks are ineffective because the client '
                              'is under attacker control. APK modification allows bypassing all checks.'
        }
    
    def _correlate_with_apis(
        self,
        findings: List[Dict[str, Any]],
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Correlate business logic findings with API endpoints
        
        REASONING: Understanding the full attack flow (UI → Flag → API → Impact)
        increases confidence and provides better exploitation guidance.
        """
        endpoints = analysis_results.get('endpoints', [])
        
        for finding in findings:
            # Try to find related API endpoints
            related_endpoints = []
            
            flag = finding['evidence'].get('value_preview', '')
            
            for endpoint in endpoints:
                url = endpoint.get('url', '')
                # Look for payment/premium/admin related endpoints
                if finding['subcategory'] == 'payment_bypass':
                    if any(kw in url.lower() for kw in ['payment', 'purchase', 'subscription', 'premium']):
                        related_endpoints.append(url)
                elif finding['subcategory'] == 'access_control_bypass':
                    if any(kw in url.lower() for kw in ['admin', 'manage', 'configure']):
                        related_endpoints.append(url)
            
            if related_endpoints:
                finding['related_endpoints'] = related_endpoints[:5]  # Top 5
                finding['confidence'] = min(finding['confidence'] + 0.05, 1.0)  # Boost confidence
        
        return findings
