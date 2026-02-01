"""
Quality Control Module
Ensures only high-quality, evidence-based findings are reported

PHILOSOPHY: "Evidence over speculation"
- Never report without proof
- Never use speculative language
- Ensure deterministic results
- Explain reasoning
"""

from typing import List, Dict, Any
import re


class QualityControl:
    """Quality control for vulnerability findings"""
    
    # Speculative language that indicates uncertainty
    SPECULATION_KEYWORDS = [
        'might', 'could', 'possibly', 'potentially',
        'may', 'perhaps', 'likely', 'probably',
        'seems', 'appears', 'suggests', 'indicates'
    ]
    
    def __init__(self, config):
        self.config = config
    
    def validate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate all findings and filter out low-quality ones
        
        REASONING: Only report findings that meet strict quality standards:
        1. Must have concrete evidence (file + line + code)
        2. Must have clear exploitation path
        3. Must not use speculative language
        4. Must be deterministic (same APK = same findings)
        
        Args:
            findings: List of vulnerability findings
            
        Returns:
            List of validated, high-quality findings
        """
        validated = []
        
        for finding in findings:
            # Run all validation checks
            if not self._has_evidence(finding):
                if self.config.verbose:
                    print(f"[QC] Rejected: {finding.get('title', 'Unknown')} - No evidence")
                continue
            
            if not self._has_exploitation_path(finding):
                if self.config.verbose:
                    print(f"[QC] Rejected: {finding.get('title', 'Unknown')} - No exploitation path")
                continue
            
            if self._is_speculative(finding):
                if self.config.verbose:
                    print(f"[QC] Rejected: {finding.get('title', 'Unknown')} - Speculative language")
                continue
            
            # Passed all checks
            validated.append(finding)
        
        # Ensure deterministic ordering
        validated = self._ensure_deterministic(validated)
        
        return validated
    
    def _has_evidence(self, finding: Dict[str, Any]) -> bool:
        """
        Check if finding has concrete evidence
        
        REASONING: Without evidence, a finding is just speculation.
        We require:
        - File path where issue was found
        - Line number for precise location
        - Code snippet showing the actual vulnerability
        
        Returns:
            True if finding has sufficient evidence
        """
        evidence = finding.get('evidence', {})
        
        # Must have evidence dictionary
        if not isinstance(evidence, dict):
            return False
        
        # Must have file path
        if not evidence.get('file'):
            return False
        
        # Must have line number (can be 0 for manifest issues)
        if 'line' not in evidence:
            return False
        
        # Must have code snippet or value preview
        if not evidence.get('code_snippet') and not evidence.get('value_preview'):
            return False
        
        return True
    
    def _has_exploitation_path(self, finding: Dict[str, Any]) -> bool:
        """
        Check if finding has clear exploitation steps
        
        REASONING: A vulnerability without exploitation steps is not actionable.
        Bug bounty programs require clear PoC or exploitation logic.
        
        Returns:
            True if finding has exploitation path
        """
        # Check for exploitation steps
        if finding.get('exploitation_steps'):
            return True
        
        # Check for PoC outline
        if finding.get('poc_outline'):
            return True
        
        # Check for steps in exploit chains
        if finding.get('steps'):
            return True
        
        # For some vulnerability types, impact description is sufficient
        # (e.g., hardcoded secrets - exploitation is obvious)
        if finding.get('category') in ['secret_exposure', 'configuration']:
            return True
        
        return False
    
    def _is_speculative(self, finding: Dict[str, Any]) -> bool:
        """
        Check if finding uses speculative language
        
        REASONING: Speculative language indicates uncertainty.
        We only report what we KNOW, not what we THINK.
        
        Examples of speculative language:
        - "This might allow an attacker to..."
        - "This could potentially lead to..."
        - "This appears to be vulnerable to..."
        
        Returns:
            True if finding uses speculative language
        """
        # Check all text fields for speculative keywords
        text_fields = [
            finding.get('title', ''),
            finding.get('description', ''),
            finding.get('impact', ''),
            finding.get('narrative', '')
        ]
        
        combined_text = ' '.join(text_fields).lower()
        
        # Check for speculation keywords
        for keyword in self.SPECULATION_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, combined_text):
                return True
        
        return False
    
    def _ensure_deterministic(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensure findings are deterministic (same APK = same results)
        
        REASONING: Deterministic results are essential for:
        1. Regression testing
        2. CI/CD integration
        3. Diff-based analysis (comparing versions)
        4. Reproducibility
        
        We achieve this by:
        1. Sorting by file, line, severity
        2. Removing duplicates
        3. Normalizing data structures
        
        Returns:
            Sorted, deduplicated findings
        """
        # Remove duplicates based on file + line + title
        seen = set()
        unique = []
        
        for finding in findings:
            # Create unique key
            evidence = finding.get('evidence', {})
            key = (
                evidence.get('file', ''),
                evidence.get('line', 0),
                finding.get('title', '')
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        
        # Sort for deterministic ordering
        # Primary: severity (critical > high > medium > low > info)
        # Secondary: file path
        # Tertiary: line number
        severity_order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3,
            'info': 4
        }
        
        unique.sort(key=lambda f: (
            severity_order.get(f.get('severity', 'info'), 99),
            f.get('evidence', {}).get('file', ''),
            f.get('evidence', {}).get('line', 0)
        ))
        
        return unique
    
    def add_reasoning_comment(self, finding: Dict[str, Any], reasoning: str) -> Dict[str, Any]:
        """
        Add reasoning comment to finding
        
        REASONING: Explaining WHY a vulnerability exists helps:
        1. Users understand the root cause
        2. Developers fix the issue properly
        3. Bug bounty triagers validate the finding
        
        Args:
            finding: Vulnerability finding
            reasoning: Explanation of why this is vulnerable
            
        Returns:
            Finding with reasoning added
        """
        finding['reasoning'] = reasoning
        return finding
    
    def calculate_confidence(self, finding: Dict[str, Any]) -> float:
        """
        Calculate confidence score for finding
        
        REASONING: Not all findings are equally reliable.
        Confidence helps prioritize manual verification.
        
        Factors:
        1. Evidence quality (40%)
        2. Exploitation feasibility (30%)
        3. Pattern reliability (30%)
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Evidence quality (0.0 to 1.0)
        evidence_quality = 0.7  # Default
        
        evidence = finding.get('evidence', {})
        if evidence.get('file') and evidence.get('line') and evidence.get('code_snippet'):
            evidence_quality = 1.0  # Perfect evidence
        elif evidence.get('file') and evidence.get('line'):
            evidence_quality = 0.8  # Good evidence
        elif evidence.get('file'):
            evidence_quality = 0.6  # Weak evidence
        
        # Exploitation feasibility (0.0 to 1.0)
        exploitation_feasibility = 0.7  # Default
        
        if finding.get('exploitation_steps') or finding.get('poc_outline'):
            exploitation_feasibility = 1.0  # Clear exploitation
        elif finding.get('steps'):
            exploitation_feasibility = 0.8  # Some guidance
        
        # Pattern reliability (0.0 to 1.0)
        pattern_reliability = finding.get('pattern_confidence', 0.7)
        
        # Calculate weighted confidence
        confidence = (
            evidence_quality * 0.4 +
            exploitation_feasibility * 0.3 +
            pattern_reliability * 0.3
        )
        
        return round(confidence, 2)
