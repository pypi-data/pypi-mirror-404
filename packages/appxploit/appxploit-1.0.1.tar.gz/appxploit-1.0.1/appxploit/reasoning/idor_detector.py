"""
Advanced IDOR (Insecure Direct Object Reference) Detection Engine
Logic-based detection with identifier flow tracking

PHILOSOPHY: "Track the data flow, not just the pattern"
- Identify user identifiers
- Track identifier flow across components
- Detect missing ownership validation
- Classify IDOR types
"""

import re
from typing import List, Dict, Any, Set, Tuple
from pathlib import Path


class IDORDetector:
    """Advanced IDOR detection with flow tracking"""
    
    # User identifier patterns
    USER_ID_PATTERNS = [
        r'\b(user_?id|uid|account_?id|customer_?id|profile_?id|member_?id)\b',
        r'\b(userId|accountId|customerId|profileId|memberId)\b'
    ]
    
    # API endpoint patterns with user IDs
    ENDPOINT_PATTERNS = [
        r'["\']([^"\']*\{[^}]*(user_?id|uid|id)[^}]*\}[^"\']*)["\']',  # /api/user/{userId}
        r'["\']([^"\']*/(user|profile|account|customer)/\d+[^"\']*)["\']',  # /api/user/123
        r'["\']([^"\']*[?&](user_?id|uid|id)=[^"\']*)["\']'  # /api?userId=123
    ]
    
    # Ownership validation indicators (positive signals)
    VALIDATION_INDICATORS = [
        'checkOwnership', 'verifyOwner', 'validateAccess',
        'isOwner', 'hasAccess', 'canAccess',
        'session', 'token', 'auth'
    ]
    
    # Missing validation indicators (negative signals)
    MISSING_VALIDATION_INDICATORS = [
        'direct access', 'no check', 'bypass',
        'public', 'open', 'unrestricted'
    ]
    
    def __init__(self, config):
        self.config = config
        self.identifiers_found: Set[str] = set()
        self.identifier_flows: List[Dict[str, Any]] = []
    
    def detect(self, decompiled_dir: Path, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect IDOR vulnerabilities using logic-based flow tracking
        
        REASONING: Pattern-based IDOR detection has high false positives.
        Logic-based detection tracks identifier flow and validates
        ownership checks, resulting in higher confidence findings.
        
        Args:
            decompiled_dir: Path to decompiled Java code
            analysis_results: Results from static analysis
            
        Returns:
            List of IDOR vulnerability findings
        """
        findings = []
        
        java_files = list(decompiled_dir.rglob('*.java'))
        
        if self.config.verbose:
            print(f"[IDOR] Scanning {len(java_files)} files for IDOR vulnerabilities...")
        
        # Step 1: Discover user identifiers
        self._discover_identifiers(java_files)
        
        if self.config.verbose:
            print(f"[IDOR] Found {len(self.identifiers_found)} unique user identifiers")
        
        # Step 2: Track identifier flows
        self._track_identifier_flows(java_files)
        
        if self.config.verbose:
            print(f"[IDOR] Tracked {len(self.identifier_flows)} identifier flows")
        
        # Step 3: Analyze endpoints for IDOR
        findings.extend(self._analyze_endpoints(analysis_results))
        
        # Step 4: Analyze Intent extras for IDOR
        findings.extend(self._analyze_intent_extras(java_files))
        
        # Step 5: Classify IDOR types
        findings = self._classify_idor_types(findings)
        
        if self.config.verbose:
            print(f"[IDOR] Found {len(findings)} IDOR vulnerabilities")
        
        return findings
    
    def _discover_identifiers(self, java_files: List[Path]):
        """
        Discover user identifiers in code
        
        REASONING: First step is identifying what user identifiers exist.
        We look for common patterns and track their types.
        """
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                
                for pattern in self.USER_ID_PATTERNS:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        identifier = match.group(1) if match.lastindex else match.group(0)
                        self.identifiers_found.add(identifier.lower())
            
            except Exception as e:
                continue
    
    def _track_identifier_flows(self, java_files: List[Path]):
        """
        Track how identifiers flow through the application
        
        REASONING: Understanding data flow helps identify where
        identifiers come from (source) and where they're used (sink).
        
        Flow: API Response → SharedPreferences → Intent → API Request
        """
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    for identifier in self.identifiers_found:
                        if identifier in line.lower():
                            # Determine source and sink
                            source = self._determine_source(line, lines, i)
                            sink = self._determine_sink(line, lines, i)
                            
                            if source or sink:
                                self.identifier_flows.append({
                                    'identifier': identifier,
                                    'file': java_file,
                                    'line': i + 1,
                                    'source': source,
                                    'sink': sink,
                                    'code': line.strip()
                                })
            
            except Exception as e:
                continue
    
    def _determine_source(self, line: str, lines: List[str], line_num: int) -> str:
        """Determine where identifier comes from"""
        line_lower = line.lower()
        
        if 'getstring' in line_lower or 'getint' in line_lower:
            if 'sharedpreferences' in line_lower:
                return 'SharedPreferences'
            elif 'intent' in line_lower or 'getextras' in line_lower:
                return 'Intent'
        
        if 'json' in line_lower and ('get' in line_lower or 'parse' in line_lower):
            return 'API Response'
        
        if 'cursor' in line_lower or 'database' in line_lower:
            return 'Database'
        
        return ''
    
    def _determine_sink(self, line: str, lines: List[str], line_num: int) -> str:
        """Determine where identifier is used"""
        line_lower = line.lower()
        
        if 'http' in line_lower or 'url' in line_lower or 'request' in line_lower:
            return 'API Request'
        
        if 'putstring' in line_lower or 'putint' in line_lower:
            return 'SharedPreferences'
        
        if 'intent' in line_lower and 'put' in line_lower:
            return 'Intent'
        
        return ''
    
    def _analyze_endpoints(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze API endpoints for IDOR vulnerabilities
        
        REASONING: Endpoints with user IDs in URLs are prime IDOR candidates.
        We check for:
        1. Numeric/sequential IDs (high risk)
        2. UUIDs (lower risk but still possible)
        3. Missing ownership validation
        """
        findings = []
        endpoints = analysis_results.get('endpoints', [])
        
        for endpoint in endpoints:
            url = endpoint.get('url', '')
            
            # Check if URL contains user ID patterns
            has_user_id = False
            id_type = 'unknown'
            
            # Check for numeric IDs
            if re.search(r'/\{?\d+\}?', url) or re.search(r'[?&]id=\d+', url):
                has_user_id = True
                id_type = 'numeric'
            
            # Check for user ID parameters
            for identifier in self.identifiers_found:
                if identifier in url.lower():
                    has_user_id = True
                    if id_type == 'unknown':
                        id_type = 'parameter'
            
            # Check for UUID patterns
            if re.search(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', url, re.IGNORECASE):
                has_user_id = True
                id_type = 'uuid'
            
            if has_user_id:
                # Check for validation indicators
                has_validation = self._check_validation_indicators(endpoint)
                
                if not has_validation:
                    # Potential IDOR!
                    confidence = self._calculate_idor_confidence(id_type, endpoint)
                    
                    if confidence >= 0.5:  # Only report medium+ confidence
                        findings.append(self._create_idor_finding(
                            endpoint, id_type, confidence
                        ))
        
        return findings
    
    def _check_validation_indicators(self, endpoint: Dict[str, Any]) -> bool:
        """Check if endpoint has ownership validation indicators"""
        
        # Check if endpoint requires authentication
        if endpoint.get('auth_required'):
            return True
        
        # Check for validation keywords in context
        context = str(endpoint).lower()
        for indicator in self.VALIDATION_INDICATORS:
            if indicator.lower() in context:
                return True
        
        return False
    
    def _calculate_idor_confidence(self, id_type: str, endpoint: Dict[str, Any]) -> float:
        """
        Calculate confidence score for IDOR finding
        
        REASONING: Not all IDOR candidates are equally likely.
        Confidence based on:
        1. ID type (numeric > parameter > UUID)
        2. Missing validation indicators
        3. Endpoint sensitivity
        """
        confidence = 0.5  # Base confidence
        
        # ID type scoring
        if id_type == 'numeric':
            confidence += 0.3  # Sequential IDs are high risk
        elif id_type == 'parameter':
            confidence += 0.2  # Parameter-based IDs are medium risk
        elif id_type == 'uuid':
            confidence += 0.1  # UUIDs are lower risk but still possible
        
        # Missing validation indicators
        context = str(endpoint).lower()
        for indicator in self.MISSING_VALIDATION_INDICATORS:
            if indicator in context:
                confidence += 0.1
                break
        
        # Endpoint sensitivity
        url = endpoint.get('url', '').lower()
        sensitive_keywords = ['profile', 'account', 'user', 'private', 'personal', 'payment']
        if any(kw in url for kw in sensitive_keywords):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _create_idor_finding(
        self,
        endpoint: Dict[str, Any],
        id_type: str,
        confidence: float
    ) -> Dict[str, Any]:
        """Create IDOR finding"""
        
        url = endpoint.get('url', '')
        method = endpoint.get('method', 'GET')
        
        # Determine severity based on method and URL
        severity = 'medium'
        if method in ['POST', 'PUT', 'DELETE']:
            severity = 'high'  # State-changing operations
        if any(kw in url.lower() for kw in ['admin', 'delete', 'payment']):
            severity = 'critical'  # Sensitive operations
        
        return {
            'title': f'Horizontal IDOR - {url}',
            'severity': severity,
            'category': 'idor',
            'subcategory': 'horizontal',
            'cwe': 'CWE-639',
            'confidence': confidence,
            'description': f'Endpoint accepts user-controllable ID without ownership validation',
            'evidence': {
                'file': endpoint.get('file', 'API Endpoint'),
                'line': endpoint.get('line', 0),
                'code_snippet': f'{method} {url}',
                'value_preview': f'ID Type: {id_type}'
            },
            'endpoint': url,
            'method': method,
            'id_type': id_type,
            'exploitation_steps': self._generate_idor_exploitation_steps(url, method, id_type),
            'impact': self._generate_idor_impact(url, method),
            'business_impact': 'Mass data breach - attacker can enumerate and access other users\' data, '
                              'exposing PII, private information, and sensitive resources.',
            'remediation': 'Implement server-side ownership validation. Verify that the authenticated '
                          'user owns the requested resource before returning data.',
            'reasoning': f'The endpoint uses {id_type} identifiers which can be manipulated. '
                        f'No ownership validation detected in the code flow.',
            'why_exploitable': 'The server accepts user-provided IDs without verifying that the '
                              'authenticated user owns the requested resource. This allows horizontal '
                              'privilege escalation where users can access other users\' data.',
            'real_world_impact': {
                'users': 'Privacy violation - personal data exposed to unauthorized users',
                'business': 'Data breach, regulatory penalties (GDPR, CCPA)',
                'security': 'Broken access control - fundamental security flaw'
            }
        }
    
    def _generate_idor_exploitation_steps(self, url: str, method: str, id_type: str) -> List[str]:
        """Generate exploitation steps for IDOR"""
        
        if id_type == 'numeric':
            return [
                f'1. Authenticate and capture own ID from API response',
                f'2. Note the ID value (e.g., 12345)',
                f'3. Increment/decrement ID: 12346, 12347, 12344...',
                f'4. Send {method} request to {url} with modified ID',
                f'5. Observe access to other users\' data'
            ]
        elif id_type == 'uuid':
            return [
                f'1. Collect UUIDs from public sources (profiles, URLs)',
                f'2. Send {method} request to {url} with collected UUID',
                f'3. Observe if access is granted without ownership check'
            ]
        else:
            return [
                f'1. Identify user ID parameter in {url}',
                f'2. Modify parameter value to target another user',
                f'3. Send {method} request with modified ID',
                f'4. Verify unauthorized access'
            ]
    
    def _generate_idor_impact(self, url: str, method: str) -> str:
        """Generate impact description for IDOR"""
        
        if method in ['DELETE']:
            return 'Unauthorized deletion of other users\' resources'
        elif method in ['PUT', 'PATCH', 'POST']:
            return 'Unauthorized modification of other users\' data'
        else:
            return 'Unauthorized access to other users\' private information'
    
    def _analyze_intent_extras(self, java_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Analyze Intent extras for IDOR in deep links
        
        REASONING: User IDs passed via Intent extras can be manipulated
        if the receiving Activity doesn't validate ownership.
        """
        findings = []
        
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    # Look for Intent.getStringExtra or getIntExtra with user ID
                    for identifier in self.identifiers_found:
                        pattern = rf'getIntent\(\)\.get\w+Extra\(["\']({identifier})["\']'
                        match = re.search(pattern, line, re.IGNORECASE)
                        
                        if match:
                            # Check if this is in an exported Activity
                            # (simplified check - look for Activity class)
                            if 'extends Activity' in content or 'extends AppCompatActivity' in content:
                                # Check for validation
                                context_start = max(0, i - 20)
                                context_end = min(len(lines), i + 20)
                                context = '\n'.join(lines[context_start:context_end])
                                
                                has_validation = any(
                                    indicator in context
                                    for indicator in self.VALIDATION_INDICATORS
                                )
                                
                                if not has_validation:
                                    findings.append(self._create_intent_idor_finding(
                                        java_file, i + 1, identifier, line
                                    ))
            
            except Exception as e:
                continue
        
        return findings
    
    def _create_intent_idor_finding(
        self,
        file_path: Path,
        line_num: int,
        identifier: str,
        code_line: str
    ) -> Dict[str, Any]:
        """Create IDOR finding for Intent extras"""
        
        relative_path = str(file_path).replace('\\', '/')
        if '/sources/' in relative_path:
            package_path = relative_path.split('/sources/')[-1]
        else:
            package_path = file_path.name
        
        return {
            'title': f'IDOR via Intent Extra: {identifier}',
            'severity': 'high',
            'category': 'idor',
            'subcategory': 'intent_based',
            'cwe': 'CWE-639',
            'confidence': 0.75,
            'description': f'User ID from Intent extra used without ownership validation',
            'evidence': {
                'file': package_path,
                'line': line_num,
                'code_snippet': code_line.strip(),
                'value_preview': identifier
            },
            'exploitation_steps': [
                f'1. Craft Intent with target user\'s {identifier}',
                f'2. Launch Activity with malicious Intent',
                f'3. Access other user\'s data without authorization'
            ],
            'impact': 'Unauthorized access to other users\' data via Intent manipulation',
            'remediation': 'Validate that the user ID from Intent matches the authenticated user',
            'reasoning': f'The Activity accepts {identifier} from Intent extras without validating ownership'
        }
    
    def _classify_idor_types(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify IDOR types: Horizontal, Vertical, Contextual
        
        REASONING: Different IDOR types have different impacts and exploitation methods.
        Classification helps prioritize and understand the vulnerability.
        """
        for finding in findings:
            url = finding.get('endpoint', finding.get('evidence', {}).get('code_snippet', ''))
            
            # Horizontal IDOR (default) - same privilege level
            idor_type = 'horizontal'
            
            # Vertical IDOR - accessing higher privilege data
            if any(kw in url.lower() for kw in ['admin', 'moderator', 'manager', 'root']):
                idor_type = 'vertical'
                finding['severity'] = 'critical'  # Escalate severity
                finding['title'] = finding['title'].replace('Horizontal', 'Vertical')
                finding['subcategory'] = 'vertical'
            
            # Contextual IDOR - state-based access
            elif any(kw in url.lower() for kw in ['pending', 'draft', 'private', 'hidden']):
                idor_type = 'contextual'
                finding['subcategory'] = 'contextual'
            
            finding['idor_type'] = idor_type
        
        return findings
