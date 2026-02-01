"""
Deep Link Abuse Detection v2
Detects state-changing, auth-bypass, and callback abuse in deep links

PHILOSOPHY: "Deep links are entry points - validate them like API endpoints"
- Detect state-changing deep links
- Identify auth-bypass deep links
- Find callback abuse
- Generate attack narratives
"""

import re
from typing import List, Dict, Any, Set
from pathlib import Path
import xml.etree.ElementTree as ET


class DeepLinkAnalyzer:
    """Advanced deep link security analysis"""
    
    # State-changing action keywords
    STATE_CHANGING_KEYWORDS = [
        'delete', 'remove', 'update', 'modify', 'edit', 'change',
        'transfer', 'send', 'payment', 'purchase', 'buy', 'order',
        'confirm', 'approve', 'accept', 'verify', 'activate',
        'deactivate', 'disable', 'enable', 'reset', 'cancel'
    ]
    
    # Auth-bypass indicators
    AUTH_BYPASS_KEYWORDS = [
        'reset', 'password', 'verify', 'confirm', 'activate',
        'token', 'code', 'otp', 'callback', 'oauth', 'login'
    ]
    
    # Sensitive callback patterns
    CALLBACK_PATTERNS = [
        r'reset[-_]?password',
        r'verify[-_]?email',
        r'confirm[-_]?account',
        r'oauth[-_]?callback',
        r'payment[-_]?callback',
        r'activate[-_]?account'
    ]
    
    def __init__(self, config):
        self.config = config
        self.deep_links: List[Dict[str, Any]] = []
    
    def analyze(self, manifest_path: Path, decompiled_dir: Path) -> List[Dict[str, Any]]:
        """
        Analyze deep links for security vulnerabilities
        
        REASONING: Deep links are often overlooked attack vectors.
        They can bypass authentication, trigger state changes,
        or abuse callback mechanisms.
        
        Args:
            manifest_path: Path to AndroidManifest.xml
            decompiled_dir: Path to decompiled Java code
            
        Returns:
            List of deep link vulnerability findings
        """
        findings = []
        
        # Step 1: Extract deep links from manifest
        self._extract_deep_links(manifest_path)
        
        if self.config.verbose:
            print(f"[DeepLink] Found {len(self.deep_links)} deep link handlers")
        
        # Step 2: Analyze each deep link
        for deep_link in self.deep_links:
            # Check for state-changing deep links
            if self._is_state_changing(deep_link):
                finding = self._analyze_state_changing_link(deep_link, decompiled_dir)
                if finding:
                    findings.append(finding)
            
            # Check for auth-bypass deep links
            if self._is_auth_bypass(deep_link):
                finding = self._analyze_auth_bypass_link(deep_link, decompiled_dir)
                if finding:
                    findings.append(finding)
            
            # Check for callback abuse
            if self._is_callback(deep_link):
                finding = self._analyze_callback_link(deep_link, decompiled_dir)
                if finding:
                    findings.append(finding)
        
        if self.config.verbose:
            print(f"[DeepLink] Found {len(findings)} deep link vulnerabilities")
        
        return findings
    
    def _extract_deep_links(self, manifest_path: Path):
        """Extract deep link definitions from AndroidManifest.xml"""
        
        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()
            
            # Find all intent-filters with data elements
            for activity in root.findall('.//activity'):
                activity_name = activity.get('{http://schemas.android.com/apk/res/android}name', '')
                exported = activity.get('{http://schemas.android.com/apk/res/android}exported', 'false')
                
                for intent_filter in activity.findall('.//intent-filter'):
                    # Check if this is a deep link (has VIEW action and BROWSABLE category)
                    has_view = any(
                        action.get('{http://schemas.android.com/apk/res/android}name') == 'android.intent.action.VIEW'
                        for action in intent_filter.findall('.//action')
                    )
                    
                    has_browsable = any(
                        category.get('{http://schemas.android.com/apk/res/android}name') == 'android.intent.category.BROWSABLE'
                        for category in intent_filter.findall('.//category')
                    )
                    
                    if has_view and has_browsable:
                        # Extract data elements
                        for data in intent_filter.findall('.//data'):
                            scheme = data.get('{http://schemas.android.com/apk/res/android}scheme', '')
                            host = data.get('{http://schemas.android.com/apk/res/android}host', '')
                            path = data.get('{http://schemas.android.com/apk/res/android}path', '')
                            pathPrefix = data.get('{http://schemas.android.com/apk/res/android}pathPrefix', '')
                            pathPattern = data.get('{http://schemas.android.com/apk/res/android}pathPattern', '')
                            
                            deep_link_url = f"{scheme}://{host}{path or pathPrefix or pathPattern}"
                            
                            self.deep_links.append({
                                'url': deep_link_url,
                                'activity': activity_name,
                                'exported': exported == 'true',
                                'scheme': scheme,
                                'host': host,
                                'path': path or pathPrefix or pathPattern
                            })
        
        except Exception as e:
            if self.config.verbose:
                print(f"[DeepLink] Error parsing manifest: {str(e)}")
    
    def _is_state_changing(self, deep_link: Dict[str, Any]) -> bool:
        """Check if deep link appears to change state"""
        url = deep_link['url'].lower()
        return any(keyword in url for keyword in self.STATE_CHANGING_KEYWORDS)
    
    def _is_auth_bypass(self, deep_link: Dict[str, Any]) -> bool:
        """Check if deep link might bypass authentication"""
        url = deep_link['url'].lower()
        return any(keyword in url for keyword in self.AUTH_BYPASS_KEYWORDS)
    
    def _is_callback(self, deep_link: Dict[str, Any]) -> bool:
        """Check if deep link is a callback handler"""
        url = deep_link['url'].lower()
        return any(re.search(pattern, url) for pattern in self.CALLBACK_PATTERNS)
    
    def _analyze_state_changing_link(
        self,
        deep_link: Dict[str, Any],
        decompiled_dir: Path
    ) -> Dict[str, Any]:
        """
        Analyze state-changing deep link for vulnerabilities
        
        REASONING: State-changing operations (delete, transfer, payment)
        should require authentication and CSRF protection.
        Deep links that trigger these without validation are critical.
        """
        activity_name = deep_link['activity']
        
        # Find the Activity file
        activity_file = self._find_activity_file(activity_name, decompiled_dir)
        
        if not activity_file:
            return None
        
        # Check for authentication checks
        has_auth_check = self._check_for_auth(activity_file)
        
        # Check for CSRF protection
        has_csrf_protection = self._check_for_csrf(activity_file)
        
        if not has_auth_check or not has_csrf_protection:
            return self._create_state_changing_finding(
                deep_link, activity_file, has_auth_check, has_csrf_protection
            )
        
        return None
    
    def _analyze_auth_bypass_link(
        self,
        deep_link: Dict[str, Any],
        decompiled_dir: Path
    ) -> Dict[str, Any]:
        """
        Analyze auth-bypass deep link for vulnerabilities
        
        REASONING: Password reset, email verification, and activation links
        should validate tokens server-side and check user ownership.
        """
        activity_name = deep_link['activity']
        activity_file = self._find_activity_file(activity_name, decompiled_dir)
        
        if not activity_file:
            return None
        
        # Check for token validation
        has_token_validation = self._check_for_token_validation(activity_file)
        
        # Check for server-side validation
        has_server_validation = self._check_for_server_validation(activity_file)
        
        if not has_token_validation or not has_server_validation:
            return self._create_auth_bypass_finding(
                deep_link, activity_file, has_token_validation, has_server_validation
            )
        
        return None
    
    def _analyze_callback_link(
        self,
        deep_link: Dict[str, Any],
        decompiled_dir: Path
    ) -> Dict[str, Any]:
        """
        Analyze callback deep link for abuse potential
        
        REASONING: OAuth callbacks, payment callbacks, and verification
        callbacks can be abused if they don't validate state/nonce.
        """
        activity_name = deep_link['activity']
        activity_file = self._find_activity_file(activity_name, decompiled_dir)
        
        if not activity_file:
            return None
        
        # Check for state/nonce validation
        has_state_validation = self._check_for_state_validation(activity_file)
        
        if not has_state_validation:
            return self._create_callback_abuse_finding(deep_link, activity_file)
        
        return None
    
    def _find_activity_file(self, activity_name: str, decompiled_dir: Path) -> Path:
        """Find the Java file for an Activity"""
        
        # Convert activity name to file path
        # e.g., com.example.app.MainActivity -> com/example/app/MainActivity.java
        file_path = activity_name.replace('.', '/') + '.java'
        
        # Search in decompiled directory
        for java_file in decompiled_dir.rglob('*.java'):
            if str(java_file).endswith(file_path):
                return java_file
        
        return None
    
    def _check_for_auth(self, activity_file: Path) -> bool:
        """Check if Activity has authentication checks"""
        try:
            content = activity_file.read_text(encoding='utf-8', errors='ignore')
            
            auth_patterns = [
                r'isLoggedIn', r'isAuthenticated', r'checkAuth',
                r'session', r'token', r'requireAuth'
            ]
            
            return any(re.search(pattern, content, re.IGNORECASE) for pattern in auth_patterns)
        
        except:
            return False
    
    def _check_for_csrf(self, activity_file: Path) -> bool:
        """Check if Activity has CSRF protection"""
        try:
            content = activity_file.read_text(encoding='utf-8', errors='ignore')
            
            csrf_patterns = [
                r'csrf', r'csrfToken', r'validateToken',
                r'checkToken', r'verifyToken'
            ]
            
            return any(re.search(pattern, content, re.IGNORECASE) for pattern in csrf_patterns)
        
        except:
            return False
    
    def _check_for_token_validation(self, activity_file: Path) -> bool:
        """Check if Activity validates tokens"""
        try:
            content = activity_file.read_text(encoding='utf-8', errors='ignore')
            
            return 'validateToken' in content or 'verifyToken' in content or 'checkToken' in content
        
        except:
            return False
    
    def _check_for_server_validation(self, activity_file: Path) -> bool:
        """Check if Activity performs server-side validation"""
        try:
            content = activity_file.read_text(encoding='utf-8', errors='ignore')
            
            # Look for API calls
            return 'http' in content.lower() or 'api' in content.lower() or 'request' in content.lower()
        
        except:
            return False
    
    def _check_for_state_validation(self, activity_file: Path) -> bool:
        """Check if Activity validates state/nonce"""
        try:
            content = activity_file.read_text(encoding='utf-8', errors='ignore')
            
            return 'state' in content.lower() or 'nonce' in content.lower()
        
        except:
            return False
    
    def _create_state_changing_finding(
        self,
        deep_link: Dict[str, Any],
        activity_file: Path,
        has_auth: bool,
        has_csrf: bool
    ) -> Dict[str, Any]:
        """Create finding for state-changing deep link"""
        
        url = deep_link['url']
        activity = deep_link['activity']
        
        missing = []
        if not has_auth:
            missing.append('authentication check')
        if not has_csrf:
            missing.append('CSRF protection')
        
        return {
            'title': f'State-Changing Deep Link Without Protection: {url}',
            'severity': 'critical',
            'category': 'deep_link',
            'subcategory': 'state_changing',
            'cwe': 'CWE-352',
            'confidence': 0.85,
            'description': f'Deep link triggers state changes without {" and ".join(missing)}',
            'evidence': {
                'file': activity,
                'line': 0,
                'code_snippet': f'Deep Link: {url}',
                'value_preview': f'Missing: {", ".join(missing)}'
            },
            'deep_link': url,
            'activity': activity,
            'missing_protections': missing,
            'exploitation_steps': [
                f'1. Craft malicious deep link: {url}?param=malicious',
                f'2. Send link to victim (phishing, SMS, email)',
                f'3. Victim clicks link',
                f'4. State-changing action executes without consent'
            ],
            'attack_narrative': self._generate_state_changing_narrative(url, missing),
            'impact': 'Unauthorized state changes via CSRF-style attack through deep links',
            'business_impact': 'Attackers can trigger unauthorized actions (delete, transfer, payment) '
                              'by tricking users into clicking malicious deep links.',
            'remediation': 'Add authentication checks and CSRF tokens to all state-changing deep links',
            'reasoning': f'The deep link {url} triggers state changes but lacks {" and ".join(missing)}, '
                        f'allowing attackers to craft malicious links that execute actions without user consent.',
            'why_exploitable': 'Deep links can be triggered from any app or web browser. Without proper '
                              'validation, attackers can craft malicious links that execute sensitive actions.',
            'real_world_impact': {
                'users': 'Unauthorized actions performed without consent',
                'business': 'Fraud, data manipulation, financial loss',
                'security': 'CSRF-style attack via deep links'
            }
        }
    
    def _generate_state_changing_narrative(self, url: str, missing: List[str]) -> str:
        """Generate attack narrative for state-changing deep link"""
        
        return (
            f"An attacker can craft a malicious deep link ({url}) and send it to victims "
            f"via phishing, SMS, or email. When the victim clicks the link, the app processes "
            f"it without {' or '.join(missing)}, executing the state-changing action "
            f"(delete, transfer, payment, etc.) without the user's explicit consent. "
            f"This is a CSRF-style attack via deep links."
        )
    
    def _create_auth_bypass_finding(
        self,
        deep_link: Dict[str, Any],
        activity_file: Path,
        has_token: bool,
        has_server: bool
    ) -> Dict[str, Any]:
        """Create finding for auth-bypass deep link"""
        
        url = deep_link['url']
        activity = deep_link['activity']
        
        return {
            'title': f'Auth Bypass via Deep Link: {url}',
            'severity': 'critical',
            'category': 'deep_link',
            'subcategory': 'auth_bypass',
            'cwe': 'CWE-287',
            'confidence': 0.88,
            'description': 'Password reset/verification deep link lacks proper validation',
            'evidence': {
                'file': activity,
                'line': 0,
                'code_snippet': f'Deep Link: {url}',
                'value_preview': f'Token validation: {has_token}, Server validation: {has_server}'
            },
            'deep_link': url,
            'activity': activity,
            'has_token_validation': has_token,
            'has_server_validation': has_server,
            'exploitation_steps': [
                f'1. Obtain victim\'s user ID (from profile, enumeration)',
                f'2. Craft deep link: {url}?userId=VICTIM_ID&token=GUESSED',
                f'3. Brute-force token (if short/predictable)',
                f'4. App processes reset without proper validation',
                f'5. Complete account takeover'
            ],
            'attack_narrative': self._generate_auth_bypass_narrative(url, has_token, has_server),
            'impact': 'Account takeover via password reset/verification deep link abuse',
            'business_impact': 'Mass account takeover vulnerability affecting all users. '
                              'Attackers can take over accounts by brute-forcing reset tokens.',
            'remediation': 'Validate tokens server-side, use cryptographically secure tokens, '
                          'implement rate limiting, verify user ownership',
            'reasoning': f'The deep link {url} processes password reset/verification without '
                        f'proper server-side validation, allowing attackers to bypass authentication.',
            'why_exploitable': 'Tokens validated client-side can be bypassed. Short or predictable '
                              'tokens can be brute-forced. Missing server-side validation allows '
                              'attackers to craft malicious reset links.',
            'real_world_impact': {
                'users': 'Complete account takeover',
                'business': 'Mass data breach, regulatory penalties',
                'security': 'Authentication bypass - critical flaw'
            }
        }
    
    def _generate_auth_bypass_narrative(self, url: str, has_token: bool, has_server: bool) -> str:
        """Generate attack narrative for auth-bypass deep link"""
        
        if not has_token and not has_server:
            return (
                f"An unauthenticated attacker can craft a password reset deep link ({url}) "
                f"with a victim's user ID. The app processes the reset without validating "
                f"the token or checking server-side, allowing complete account takeover."
            )
        elif not has_server:
            return (
                f"An attacker can craft a password reset deep link ({url}) with a victim's "
                f"user ID and brute-force the token. The app validates tokens client-side only, "
                f"allowing attackers to bypass authentication and take over accounts."
            )
        else:
            return (
                f"The password reset deep link ({url}) has weak token validation, allowing "
                f"attackers to brute-force or predict tokens and take over accounts."
            )
    
    def _create_callback_abuse_finding(
        self,
        deep_link: Dict[str, Any],
        activity_file: Path
    ) -> Dict[str, Any]:
        """Create finding for callback abuse"""
        
        url = deep_link['url']
        activity = deep_link['activity']
        
        return {
            'title': f'Callback Abuse - Missing State Validation: {url}',
            'severity': 'high',
            'category': 'deep_link',
            'subcategory': 'callback_abuse',
            'cwe': 'CWE-352',
            'confidence': 0.75,
            'description': 'OAuth/payment callback lacks state/nonce validation',
            'evidence': {
                'file': activity,
                'line': 0,
                'code_snippet': f'Deep Link: {url}',
                'value_preview': 'Missing state validation'
            },
            'deep_link': url,
            'activity': activity,
            'exploitation_steps': [
                f'1. Initiate OAuth/payment flow as attacker',
                f'2. Capture callback URL with attacker\'s code/token',
                f'3. Send malicious callback to victim',
                f'4. Victim\'s account linked to attacker\'s OAuth/payment'
            ],
            'impact': 'Account linking abuse, OAuth token theft, payment fraud',
            'remediation': 'Implement state/nonce validation in all callback handlers',
            'reasoning': f'The callback handler {url} lacks state validation, allowing CSRF attacks'
        }
