"""
Noise Filtering Module
Filters out low-impact findings and prioritizes high-signal vulnerabilities
"""

from typing import List, Dict, Any


class NoiseFilter:
    """Filter noise and extract high-signal findings"""
    
    def __init__(self, config):
        self.config = config
    
    def filter(self, vulnerabilities: List[Dict[str, Any]], exploit_chains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter vulnerabilities and exploit chains
        
        Returns:
            High-signal findings only
        """
        filtered = []
        
        # Always include exploit chains (highest value)
        for chain in exploit_chains:
            filtered.append({
                'type': 'exploit_chain',
                'data': chain,
                'priority': 1,  # Highest priority
                'score': chain.get('cvss', 8.0) * 10
            })
        
        # Filter vulnerabilities
        for vuln in vulnerabilities:
            if self._should_include(vuln):
                filtered.append({
                    'type': 'vulnerability',
                    'data': vuln,
                    'priority': self._get_priority(vuln),
                    'score': vuln.get('score', 0)
                })
        
        # Sort by priority then score
        filtered.sort(key=lambda x: (x['priority'], -x['score']))
        
        return filtered
    
    def _should_include(self, vuln: Dict[str, Any]) -> bool:
        """Determine if vulnerability should be included"""
        severity = vuln.get('final_severity') or vuln.get('severity', 'info')
        score = vuln.get('score', 0)
        category = vuln.get('category', '')
        
        # Always include critical
        if severity == 'critical':
            return True
        
        # Always include high with good score
        if severity == 'high' and score >= 50:
            return True
        
        # Include medium if score is good
        if severity == 'medium' and score >= 30:
            return True
        
        # Include secret exposure regardless of score
        if category == 'secret_exposure' and severity in ['critical', 'high']:
            return True
        
        # Include component security issues
        if category == 'component_security' and severity in ['critical', 'high']:
            return True
        
        # Skip low and info unless in verbose mode
        if severity in ['low', 'info'] and not self.config.verbose:
            return False
        
        # Skip very low scores
        if score < 20 and not self.config.verbose:
            return False
        
        return True
    
    def _get_priority(self, vuln: Dict[str, Any]) -> int:
        """Get priority level (1 = highest, 5 = lowest)"""
        severity = vuln.get('final_severity') or vuln.get('severity', 'info')
        category = vuln.get('category', '')
        
        # Priority 1: Critical vulnerabilities
        if severity == 'critical':
            return 1
        
        # Priority 2: High severity with exploit potential
        if severity == 'high':
            if category in ['secret_exposure', 'component_security']:
                return 2
            return 3
        
        # Priority 3: Medium severity
        if severity == 'medium':
            return 3
        
        # Priority 4: Low severity
        if severity == 'low':
            return 4
        
        # Priority 5: Info
        return 5
