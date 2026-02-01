"""
Vulnerability Scoring Module
Scores vulnerabilities based on Reachability × Control × Impact × Exploitability
"""

from typing import Dict, Any, List


class VulnerabilityScorer:
    """Score vulnerabilities using intelligent formula"""
    
    def __init__(self, config):
        self.config = config
    
    def score_all(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score all vulnerabilities"""
        for vuln in vulnerabilities:
            vuln['score'] = self._calculate_score(vuln)
            vuln['final_severity'] = self._determine_severity(vuln['score'], vuln.get('severity', 'medium'))
        
        # Sort by score (highest first)
        vulnerabilities.sort(key=lambda x: x['score'], reverse=True)
        
        return vulnerabilities
    
    def _calculate_score(self, vuln: Dict[str, Any]) -> float:
        """
        Calculate vulnerability score
        
        ENHANCED FORMULA: Reachability × Control × Impact × Exploitability × ContextConfidence
        
        Each factor is 0.0 to 1.0
        
        REASONING: ContextConfidence reduces false positives by considering:
        - Evidence strength (direct code vs heuristic)
        - Usage frequency (used vs referenced)
        - Business logic relevance (core vs debug)
        - Supporting evidence (corroborating findings)
        """
        reachability = self._score_reachability(vuln)
        control = self._score_control(vuln)
        impact = self._score_impact(vuln)
        exploitability = self._score_exploitability(vuln)
        context_confidence = self._score_context_confidence(vuln)
        
        # Final score: 0-100
        # REASONING: Multiplying by confidence ensures low-confidence findings get lower scores
        score = reachability * control * impact * exploitability * context_confidence * 100
        
        return round(score, 2)
    
    def _score_reachability(self, vuln: Dict[str, Any]) -> float:
        """Can attacker reach this vulnerability?"""
        category = vuln.get('category', '')
        
        # Exported components are directly reachable
        if category == 'component_security':
            return 1.0
        
        # Deep links are reachable via URL
        if category == 'deep_linking':
            return 0.9
        
        # Secret exposure requires APK extraction (easy)
        if category == 'secret_exposure':
            return 0.8
        
        # API endpoints are reachable if app is used
        if category == 'api_security':
            return 0.7
        
        # Configuration issues are always present
        if category == 'configuration':
            return 0.9
        
        return 0.5
    
    def _score_control(self, vuln: Dict[str, Any]) -> float:
        """Can attacker control/manipulate input?"""
        category = vuln.get('category', '')
        
        # Exported components accept external input
        if category == 'component_security':
            return 0.9
        
        # Deep links are fully controllable
        if category == 'deep_linking':
            return 1.0
        
        # Secrets are static (no control needed)
        if category == 'secret_exposure':
            return 1.0
        
        # API endpoints may have input validation
        if category == 'api_security':
            return 0.6
        
        # Configuration is static
        if category == 'configuration':
            return 0.7
        
        return 0.5
    
    def _score_impact(self, vuln: Dict[str, Any]) -> float:
        """What's the business impact?"""
        severity = vuln.get('severity', 'medium')
        category = vuln.get('category', '')
        
        # Base impact from severity
        severity_map = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3,
            'info': 0.1
        }
        
        base_impact = severity_map.get(severity, 0.5)
        
        # Boost for certain categories
        if category == 'secret_exposure' and severity == 'critical':
            return 1.0  # AWS keys, etc.
        
        if category == 'component_security':
            return min(base_impact * 1.2, 1.0)
        
        return base_impact
    
    def _score_exploitability(self, vuln: Dict[str, Any]) -> float:
        """How easy is it to exploit?"""
        category = vuln.get('category', '')
        
        # Secrets just need extraction
        if category == 'secret_exposure':
            return 1.0
        
        # Configuration issues are trivial to verify
        if category == 'configuration':
            return 0.9
        
        # Deep links need crafting but easy
        if category == 'deep_linking':
            return 0.8
        
        # Exported components need understanding
        if category == 'component_security':
            return 0.7
        
        # API issues need testing
        if category == 'api_security':
            return 0.6
        
        return 0.5
    
    def _score_context_confidence(self, vuln: Dict[str, Any]) -> float:
        """
        Score context confidence to reduce false positives
        
        REASONING: Not all findings are equally reliable. This factor considers:
        1. Evidence Strength (40% weight) - How direct is the evidence?
        2. Usage Frequency (20% weight) - How often is it used?
        3. Business Logic Relevance (20% weight) - Is it core functionality?
        4. Supporting Evidence (20% weight) - Are there corroborating findings?
        
        Returns: 0.0 to 1.0 confidence score
        """
        # Get evidence and metadata
        evidence = vuln.get('evidence', {})
        category = vuln.get('category', '')
        pattern_confidence = vuln.get('pattern_confidence', 0.7)  # From pattern match
        
        # 1. Evidence Strength (0.4 weight)
        # REASONING: Direct code evidence is more reliable than heuristics
        evidence_strength = 0.7  # Default
        
        if isinstance(evidence, dict):
            # Direct code match with file and line
            if evidence.get('file') and evidence.get('value_preview'):
                evidence_strength = 1.0
            # Indirect indicators
            elif evidence.get('file'):
                evidence_strength = 0.7
            # Heuristic match only
            else:
                evidence_strength = 0.5
        elif isinstance(evidence, list) and len(evidence) > 0:
            # Multiple evidence points
            evidence_strength = 0.9
        
        # Use pattern confidence if available
        if pattern_confidence > 0:
            evidence_strength = max(evidence_strength, pattern_confidence)
        
        # 2. Usage Frequency (0.2 weight)
        # REASONING: Findings used in multiple places are more significant
        usage_frequency = 0.7  # Default
        
        if isinstance(evidence, list):
            # Multiple occurrences
            if len(evidence) >= 3:
                usage_frequency = 1.0
            elif len(evidence) == 2:
                usage_frequency = 0.8
            else:
                usage_frequency = 0.6
        
        # 3. Business Logic Relevance (0.2 weight)
        # REASONING: Core functionality issues are more critical than debug code
        business_relevance = 0.7  # Default
        
        if isinstance(evidence, dict) and evidence.get('file'):
            file_path = evidence['file'].lower()
            
            # Core functionality
            if any(x in file_path for x in ['auth', 'payment', 'api', 'crypto', 'security']):
                business_relevance = 1.0
            # Secondary features
            elif any(x in file_path for x in ['util', 'helper', 'manager']):
                business_relevance = 0.7
            # Debug/test code (lower relevance)
            elif any(x in file_path for x in ['test', 'debug', 'mock', 'sample']):
                business_relevance = 0.3
        
        # 4. Supporting Evidence (0.2 weight)
        # REASONING: Corroborating findings increase confidence
        supporting_evidence = 0.6  # Default
        
        # Check if there are related findings
        if category == 'secret_exposure':
            # Secrets with corresponding API endpoints
            supporting_evidence = 0.8
        elif category == 'component_security':
            # Exported components are verifiable
            supporting_evidence = 1.0
        elif category == 'configuration':
            # Configuration is directly observable
            supporting_evidence = 1.0
        
        # Calculate weighted confidence
        # WEIGHTS: Evidence(0.4) + Usage(0.2) + Business(0.2) + Supporting(0.2) = 1.0
        confidence = (
            evidence_strength * 0.4 +
            usage_frequency * 0.2 +
            business_relevance * 0.2 +
            supporting_evidence * 0.2
        )
        
        # Ensure minimum confidence threshold
        # REASONING: Never completely dismiss a finding, but heavily penalize low-confidence ones
        MIN_CONFIDENCE = 0.3
        confidence = max(confidence, MIN_CONFIDENCE)
        
        return round(confidence, 2)
    
    def _determine_severity(self, score: float, original_severity: str) -> str:
        """Determine final severity based on score"""
        # REASONING: Score thresholds based on real-world impact
        # 70+: Critical - Immediate exploitation, high impact
        # 50+: High - Exploitable with moderate effort
        # 30+: Medium - Requires specific conditions
        # 10+: Low - Limited impact or difficult to exploit
        # <10: Info - Informational only
        if score >= 70:
            return 'critical'
        elif score >= 50:
            return 'high'
        elif score >= 30:
            return 'medium'
        elif score >= 10:
            return 'low'
        else:
            return 'info'
