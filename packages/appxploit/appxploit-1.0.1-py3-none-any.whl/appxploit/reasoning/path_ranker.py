"""
Exploit Path Ranking System
Ranks exploit chains by business impact, ease of exploitation, and bug bounty acceptance

PHILOSOPHY: "Highlight the TOP 1-3 most dangerous paths"
- Rank by business impact (40%)
- Rank by ease of exploitation (30%)
- Rank by bug bounty acceptance (30%)
- Everything else becomes secondary
"""

from typing import List, Dict, Any


class ExploitPathRanker:
    """Rank exploit paths by real-world value"""
    
    # Business impact scores (0-10)
    IMPACT_SCORES = {
        'account_takeover': 10,
        'payment_bypass': 10,
        'data_exfiltration_pii': 9,
        'privilege_escalation': 8,
        'data_manipulation': 7,
        'payment_fraud': 10,
        'mass_data_breach': 9,
        'information_disclosure': 5,
        'configuration_issue': 3
    }
    
    # Ease of exploitation scores (0-10)
    EASE_SCORES = {
        'no_tools': 10,           # Just modify SharedPreferences
        'basic_tools': 8,         # ADB, Burp Suite
        'custom_script': 6,       # Need to write exploit code
        'reverse_engineering': 4, # Need to modify APK
        'complex_multi_step': 3   # Multiple prerequisites
    }
    
    # Bug bounty acceptance scores (0-10)
    ACCEPTANCE_SCORES = {
        'direct_exploitation': 10,      # Clear PoC, immediate impact
        'clear_poc': 9,                 # PoC possible with some effort
        'requires_conditions': 7,       # Needs specific app state
        'theoretical': 4,               # Hard to demonstrate
        'configuration': 3              # Low severity in most programs
    }
    
    def __init__(self, config):
        self.config = config
    
    def rank(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rank all findings and highlight TOP 3
        
        REASONING: Bug bounty hunters need to focus on the most valuable findings.
        Ranking helps prioritize manual verification and reporting efforts.
        
        Args:
            findings: All vulnerability findings (chains + individual)
            
        Returns:
            Dictionary with ranked findings and top 3 highlights
        """
        # Calculate rank score for each finding
        ranked = []
        for finding in findings:
            score = self._calculate_rank_score(finding)
            finding['rank_score'] = score
            finding['rank_breakdown'] = self._get_rank_breakdown(finding)
            ranked.append(finding)
        
        # Sort by rank score (descending)
        ranked.sort(key=lambda f: f['rank_score'], reverse=True)
        
        # Assign ranks
        for i, finding in enumerate(ranked):
            finding['rank'] = i + 1
        
        # Extract top 3
        top_3 = ranked[:3] if len(ranked) >= 3 else ranked
        
        # Generate ranking summary
        summary = self._generate_ranking_summary(top_3)
        
        return {
            'all_findings': ranked,
            'top_3': top_3,
            'summary': summary
        }
    
    def _calculate_rank_score(self, finding: Dict[str, Any]) -> float:
        """
        Calculate rank score (0-10)
        
        Formula: (Business Impact × 0.4) + (Ease × 0.3) + (Acceptance × 0.3)
        """
        # Determine business impact
        impact_type = finding.get('impact_type', '').lower().replace(' ', '_')
        business_impact = self.IMPACT_SCORES.get(impact_type, 5)
        
        # If not in predefined types, infer from severity and category
        if impact_type not in self.IMPACT_SCORES:
            business_impact = self._infer_business_impact(finding)
        
        # Determine ease of exploitation
        ease = self._determine_ease(finding)
        
        # Determine bug bounty acceptance likelihood
        acceptance = self._determine_acceptance(finding)
        
        # Calculate weighted score
        score = (business_impact * 0.4) + (ease * 0.3) + (acceptance * 0.3)
        
        return round(score, 1)
    
    def _infer_business_impact(self, finding: Dict[str, Any]) -> float:
        """Infer business impact from finding characteristics"""
        
        severity = finding.get('severity', 'medium')
        category = finding.get('category', '')
        subcategory = finding.get('subcategory', '')
        
        # Critical severity = high impact
        if severity == 'critical':
            return 9.0
        
        # Category-based inference
        if category == 'business_logic':
            if 'payment' in subcategory:
                return 10.0
            elif 'premium' in subcategory:
                return 9.0
            elif 'access_control' in subcategory:
                return 8.0
        
        elif category == 'idor':
            return 9.0  # IDOR is almost always high impact
        
        elif category == 'deep_link':
            if 'auth_bypass' in subcategory:
                return 10.0
            elif 'state_changing' in subcategory:
                return 9.0
        
        elif category == 'crypto':
            return 8.0
        
        # Default based on severity
        severity_scores = {
            'critical': 9.0,
            'high': 7.0,
            'medium': 5.0,
            'low': 3.0,
            'info': 2.0
        }
        
        return severity_scores.get(severity, 5.0)
    
    def _determine_ease(self, finding: Dict[str, Any]) -> float:
        """Determine ease of exploitation"""
        
        category = finding.get('category', '')
        subcategory = finding.get('subcategory', '')
        
        # Business logic flaws are usually trivial
        if category == 'business_logic':
            if 'payment' in subcategory or 'premium' in subcategory:
                return 10.0  # Just modify SharedPreferences
            else:
                return 8.0   # Might need APK modification
        
        # IDOR usually requires basic tools
        elif category == 'idor':
            return 8.0  # Burp Suite, parameter manipulation
        
        # Deep links can be triggered easily
        elif category == 'deep_link':
            return 9.0  # Just craft a URL
        
        # Crypto issues require data extraction
        elif category == 'crypto':
            return 6.0  # Need to extract encrypted data first
        
        # Default: basic tools
        return 7.0
    
    def _determine_acceptance(self, finding: Dict[str, Any]) -> float:
        """Determine bug bounty acceptance likelihood"""
        
        # Check if has clear exploitation steps
        if finding.get('exploitation_steps') and len(finding['exploitation_steps']) >= 3:
            return 9.0  # Clear PoC possible
        
        # Check confidence score
        confidence = finding.get('confidence', 0.7)
        if confidence >= 0.9:
            return 10.0  # High confidence = high acceptance
        elif confidence >= 0.7:
            return 8.0
        else:
            return 6.0
        
        # Check severity
        severity = finding.get('severity', 'medium')
        if severity == 'critical':
            return 9.0
        elif severity == 'high':
            return 8.0
        else:
            return 6.0
    
    def _get_rank_breakdown(self, finding: Dict[str, Any]) -> Dict[str, float]:
        """Get detailed breakdown of rank score"""
        
        impact_type = finding.get('impact_type', '').lower().replace(' ', '_')
        business_impact = self.IMPACT_SCORES.get(impact_type, self._infer_business_impact(finding))
        ease = self._determine_ease(finding)
        acceptance = self._determine_acceptance(finding)
        
        return {
            'business_impact': business_impact,
            'ease_of_exploitation': ease,
            'bug_bounty_acceptance': acceptance
        }
    
    def _generate_ranking_summary(self, top_3: List[Dict[str, Any]]) -> str:
        """Generate human-readable ranking summary"""
        
        medals = ['🥇', '🥈', '🥉']
        lines = []
        
        lines.append('═' * 63)
        lines.append('TOP 3 MOST DANGEROUS ATTACK PATHS')
        lines.append('═' * 63)
        lines.append('')
        
        for i, finding in enumerate(top_3):
            medal = medals[i] if i < len(medals) else f'#{i+1}'
            score = finding['rank_score']
            title = finding['title']
            breakdown = finding['rank_breakdown']
            
            lines.append(f'{medal} RANK #{i+1} - Score: {score}/10')
            lines.append(f'   {title}')
            lines.append('')
            lines.append(f'   Impact: {breakdown["business_impact"]}/10')
            lines.append(f'   Ease: {breakdown["ease_of_exploitation"]}/10')
            lines.append(f'   Acceptance: {breakdown["bug_bounty_acceptance"]}/10')
            lines.append('')
            lines.append(f'   Why This Is #{i+1}:')
            lines.append(f'   {self._generate_why_ranked(finding, i+1)}')
            
            if i < len(top_3) - 1:
                lines.append('')
                lines.append('─' * 63)
                lines.append('')
        
        lines.append('')
        lines.append('═' * 63)
        
        return '\n'.join(lines)
    
    def _generate_why_ranked(self, finding: Dict[str, Any], rank: int) -> str:
        """Generate explanation for why this finding is ranked where it is"""
        
        breakdown = finding['rank_breakdown']
        category = finding.get('category', '')
        
        reasons = []
        
        # Impact reasons
        if breakdown['business_impact'] >= 9:
            if category == 'business_logic' and 'payment' in finding.get('subcategory', ''):
                reasons.append('Direct revenue impact')
            elif category == 'idor':
                reasons.append('Mass data breach potential')
            elif 'account_takeover' in finding.get('impact_type', '').lower():
                reasons.append('Complete account takeover')
        
        # Ease reasons
        if breakdown['ease_of_exploitation'] >= 9:
            reasons.append('Trivial to exploit')
        elif breakdown['ease_of_exploitation'] >= 7:
            reasons.append('Simple exploitation with basic tools')
        
        # Acceptance reasons
        if breakdown['bug_bounty_acceptance'] >= 9:
            reasons.append('Guaranteed acceptance in bug bounty programs')
        elif breakdown['bug_bounty_acceptance'] >= 7:
            reasons.append('High acceptance rate')
        
        # Time to demonstrate
        if breakdown['ease_of_exploitation'] >= 9:
            reasons.append('Can be demonstrated in <5 minutes')
        
        return ', '.join(reasons) + '.'
