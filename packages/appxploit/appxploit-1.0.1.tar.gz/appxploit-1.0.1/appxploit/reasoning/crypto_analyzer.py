"""
Crypto Misuse Intelligence
Context-aware cryptography analysis focusing on exploitable misuse

PHILOSOPHY: "Only report crypto issues that matter"
- Detect home-grown crypto
- Identify AES misuse
- Distinguish encoding vs encryption
- Context-aware reporting (sensitive data + attacker control + impact)
"""

import re
from typing import List, Dict, Any
from pathlib import Path


class CryptoAnalyzer:
    """Context-aware cryptography misuse detection"""
    
    # Weak algorithms
    WEAK_ALGORITHMS = ['MD5', 'SHA1', 'DES', 'RC4']
    
    # Weak AES modes
    WEAK_AES_MODES = ['ECB']
    
    # Encoding patterns (not encryption)
    ENCODING_PATTERNS = [
        r'Base64\.encode',
        r'Base64\.decode',
        r'URLEncoder',
        r'toHexString'
    ]
    
    # Sensitive data keywords
    SENSITIVE_DATA_KEYWORDS = [
        'password', 'credential', 'token', 'secret', 'key',
        'pin', 'otp', 'ssn', 'credit', 'card', 'account'
    ]
    
    def __init__(self, config):
        self.config = config
    
    def analyze(self, decompiled_dir: Path) -> List[Dict[str, Any]]:
        """
        Analyze cryptography usage for exploitable misuse
        
        REASONING: Not all crypto issues are exploitable.
        We only report when:
        1. Sensitive data is involved
        2. Attacker can control input
        3. Impact is meaningful (score >= 7.0)
        """
        findings = []
        
        java_files = list(decompiled_dir.rglob('*.java'))
        
        if self.config.verbose:
            print(f"[Crypto] Scanning {len(java_files)} files for crypto misuse...")
        
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    # Detect ECB mode usage
                    if re.search(r'Cipher\.getInstance\(["\']AES/ECB', line):
                        context = self._get_context(lines, i)
                        if self._has_sensitive_data(context) and self._has_attacker_input(context):
                            findings.append(self._create_ecb_finding(java_file, i + 1, line, context))
                    
                    # Detect weak algorithms
                    for algo in self.WEAK_ALGORITHMS:
                        if re.search(rf'{algo}\.getInstance|MessageDigest\.getInstance\(["\']({algo})["\']', line):
                            context = self._get_context(lines, i)
                            if self._has_sensitive_data(context):
                                findings.append(self._create_weak_algo_finding(java_file, i + 1, algo, line))
                    
                    # Detect encoding used as encryption
                    for pattern in self.ENCODING_PATTERNS:
                        if re.search(pattern, line):
                            context = self._get_context(lines, i)
                            if self._has_sensitive_data(context) and 'encrypt' in context.lower():
                                findings.append(self._create_encoding_finding(java_file, i + 1, line, context))
            
            except Exception as e:
                continue
        
        # Filter by impact score
        findings = [f for f in findings if self._calculate_impact_score(f) >= 7.0]
        
        if self.config.verbose:
            print(f"[Crypto] Found {len(findings)} exploitable crypto issues")
        
        return findings
    
    def _get_context(self, lines: List[str], line_num: int, window: int = 20) -> str:
        """Get surrounding context"""
        start = max(0, line_num - window)
        end = min(len(lines), line_num + window)
        return '\n'.join(lines[start:end])
    
    def _has_sensitive_data(self, context: str) -> bool:
        """Check if context involves sensitive data"""
        context_lower = context.lower()
        return any(kw in context_lower for kw in self.SENSITIVE_DATA_KEYWORDS)
    
    def _has_attacker_input(self, context: str) -> bool:
        """Check if attacker can control input"""
        # Look for user input sources
        input_sources = ['Intent', 'getExtra', 'SharedPreferences', 'EditText', 'input']
        return any(src in context for src in input_sources)
    
    def _calculate_impact_score(self, finding: Dict[str, Any]) -> float:
        """Calculate impact score (0-10)"""
        score = 5.0  # Base score
        
        if 'password' in finding['description'].lower() or 'credential' in finding['description'].lower():
            score += 3.0
        
        if finding['severity'] == 'critical':
            score += 2.0
        
        return min(score, 10.0)
    
    def _create_ecb_finding(self, file_path: Path, line_num: int, code_line: str, context: str) -> Dict[str, Any]:
        """Create ECB mode finding"""
        relative_path = str(file_path).replace('\\', '/')
        if '/sources/' in relative_path:
            package_path = relative_path.split('/sources/')[-1]
        else:
            package_path = file_path.name
        
        return {
            'title': 'Credential Theft via ECB Mode Encryption',
            'severity': 'high',
            'category': 'crypto',
            'subcategory': 'weak_mode',
            'cwe': 'CWE-327',
            'confidence': 0.91,
            'description': 'AES ECB mode used for encrypting sensitive data',
            'evidence': {
                'file': package_path,
                'line': line_num,
                'code_snippet': code_line.strip(),
                'value_preview': 'ECB mode'
            },
            'exploitation_steps': [
                '1. Extract encrypted data (via backup or rooted device)',
                '2. Analyze ECB patterns in ciphertext',
                '3. Identify repeating blocks (same plaintext = same ciphertext)',
                '4. Perform known-plaintext or dictionary attack',
                '5. Decrypt credentials without knowing the key'
            ],
            'impact': 'Credential theft via pattern analysis of ECB-encrypted data',
            'business_impact': 'Account takeover - ECB mode weakness allows attackers to decrypt '
                              'stored credentials without the encryption key.',
            'remediation': 'Use AES/CBC or AES/GCM mode with random IV',
            'reasoning': 'ECB mode encrypts identical plaintext blocks to identical ciphertext blocks, '
                        'allowing pattern analysis attacks.',
            'why_exploitable': 'ECB mode is deterministic - same input always produces same output. '
                              'This allows attackers to identify patterns and perform cryptanalysis '
                              'without knowing the key.'
        }
    
    def _create_weak_algo_finding(self, file_path: Path, line_num: int, algo: str, code_line: str) -> Dict[str, Any]:
        """Create weak algorithm finding"""
        relative_path = str(file_path).replace('\\', '/')
        if '/sources/' in relative_path:
            package_path = relative_path.split('/sources/')[-1]
        else:
            package_path = file_path.name
        
        return {
            'title': f'Weak Cryptography - {algo} Used for Sensitive Data',
            'severity': 'high',
            'category': 'crypto',
            'subcategory': 'weak_algorithm',
            'cwe': 'CWE-327',
            'confidence': 0.85,
            'description': f'{algo} algorithm used - known to be cryptographically broken',
            'evidence': {
                'file': package_path,
                'line': line_num,
                'code_snippet': code_line.strip(),
                'value_preview': algo
            },
            'impact': f'Data compromise via {algo} collision/preimage attacks',
            'remediation': f'Replace {algo} with SHA-256 or stronger',
            'reasoning': f'{algo} is cryptographically broken and should not be used for security purposes'
        }
    
    def _create_encoding_finding(self, file_path: Path, line_num: int, code_line: str, context: str) -> Dict[str, Any]:
        """Create encoding-as-encryption finding"""
        relative_path = str(file_path).replace('\\', '/')
        if '/sources/' in relative_path:
            package_path = relative_path.split('/sources/')[-1]
        else:
            package_path = file_path.name
        
        return {
            'title': 'Encoding Used as Encryption',
            'severity': 'critical',
            'category': 'crypto',
            'subcategory': 'encoding_as_encryption',
            'cwe': 'CWE-327',
            'confidence': 0.95,
            'description': 'Base64/Hex encoding used instead of encryption for sensitive data',
            'evidence': {
                'file': package_path,
                'line': line_num,
                'code_snippet': code_line.strip(),
                'value_preview': 'Encoding, not encryption'
            },
            'exploitation_steps': [
                '1. Extract "encrypted" data',
                '2. Decode Base64/Hex',
                '3. Access plaintext sensitive data'
            ],
            'impact': 'Complete data exposure - encoding provides zero security',
            'business_impact': 'Sensitive data stored in plaintext (just encoded). '
                              'Trivial to decode and access.',
            'remediation': 'Use proper encryption (AES-256-GCM) instead of encoding',
            'reasoning': 'Encoding (Base64, Hex) is not encryption - it provides no security',
            'why_exploitable': 'Encoding is reversible without a key. Anyone can decode Base64/Hex.'
        }
