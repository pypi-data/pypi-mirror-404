"""
Report Generation Module
Generates professional bug bounty reports in Markdown format
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json


class ReportGenerator:
    """Generate professional security reports"""
    
    def __init__(self, config):
        self.config = config
    
    def generate(self, results: Dict[str, Any], output_path: Path) -> bool:
        """
        Generate report
        
        Args:
            results: Analysis results
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            # Save raw data for manual testing
            self._save_raw_data(results, output_path)
            
            if self.config.output_format == 'json':
                return self._generate_json(results, output_path)
            else:
                return self._generate_markdown(results, output_path)
        except Exception as e:
            print(f"Report generation error: {str(e)}")
            return False
            
    def _save_raw_data(self, results: Dict[str, Any], output_path: Path):
        """Save raw endpoints and secrets for manual testing"""
        try:
            base_path = output_path.parent / output_path.stem
            
            # Save endpoints
            endpoints = results.get('endpoints', [])
            if endpoints:
                ep_path = output_path.parent / f"{output_path.stem}_endpoints.txt"
                with open(ep_path, 'w', encoding='utf-8') as f:
                    for ep in endpoints:
                        f.write(f"{ep['url']}\n")
                # print(f"    Saved {len(endpoints)} endpoints to {ep_path.name}")
                
            # Save secrets
            secrets = results.get('secrets', [])
            if secrets:
                sec_path = output_path.parent / f"{output_path.stem}_secrets.txt"
                with open(sec_path, 'w', encoding='utf-8') as f:
                    for sec in secrets:
                        f.write(f"[{sec['type']}] {sec['value']} (File: {sec['file']})\n")
        except Exception as e:
            # Don't fail report generation if aux files fail
            pass
    
    def _generate_json(self, results: Dict[str, Any], output_path: Path) -> bool:
        """Generate JSON report"""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        return True
    
    
    def _generate_markdown(self, results: Dict[str, Any], output_path: Path) -> bool:
        """Generate Markdown report"""
        
        # Build report content
        report = self._build_markdown_report(results, output_path)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return True
    
    def _build_markdown_report(self, results: Dict[str, Any], output_path: Path) -> str:
        """Build markdown report content"""
        
        fingerprint = results.get('fingerprint', {})
        classification = results.get('classification', {})
        filtered_findings = results.get('filtered_findings', [])
        ranked_findings = results.get('ranked_findings', {})
        
        # Count findings by type
        exploit_chains = [f for f in filtered_findings if f['type'] == 'exploit_chain']
        vulnerabilities = [f for f in filtered_findings if f['type'] == 'vulnerability']
        
        # Count by severity
        critical = len([v for v in vulnerabilities if v['data'].get('final_severity') == 'critical'])
        high = len([v for v in vulnerabilities if v['data'].get('final_severity') == 'high'])
        medium = len([v for v in vulnerabilities if v['data'].get('final_severity') == 'medium'])
        
        report = f"""# AppXploit Security Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Analyzed by:** LAKSHMIKANTHAN K (letchupkt)  
**Tool:** AppXploit v1.0.0 - Elite Vulnerability Discovery Framework

---

## Executive Summary

This report presents the security analysis findings for the Android application **{fingerprint.get('package_name', 'Unknown')}**.

### Application Information

| Property | Value |
|----------|-------|
| **Package Name** | {fingerprint.get('package_name', 'N/A')} |
| **Version** | {fingerprint.get('version_name', 'N/A')} ({fingerprint.get('version_code', 'N/A')}) |
| **Target SDK** | {fingerprint.get('target_sdk', 'N/A')} |
| **Min SDK** | {fingerprint.get('min_sdk', 'N/A')} |
| **App Type** | {classification.get('app_type', 'Unknown').replace('_', ' ').title()} |
| **Framework** | {fingerprint.get('framework', 'native').replace('_', ' ').title()} |
| **Obfuscated** | {'Yes' if fingerprint.get('obfuscated') else 'No'} |

### Findings Summary

| Severity | Count |
|----------|-------|
| **🔴 Critical** | {critical} |
| **🟠 High** | {high} |
| **🟡 Medium** | {medium} |
| **Exploit Chains** | {len(exploit_chains)} |

---

{self._format_top_3_ranked(ranked_findings)}

---

## 🎯 Exploit Chains

{self._format_exploit_chains(exploit_chains)}

---

## 🔍 Vulnerability Findings

{self._format_vulnerabilities(vulnerabilities)}

---

## 📊 API Endpoints Discovered

{self._format_endpoints(results.get('endpoints', []))}

---

## 🔑 Secrets Exposure Summary

{self._format_secrets(results.get('secrets', []))}

---

## 📋 Recommendations

### Immediate Actions (Critical/High)

1. **Remove hardcoded secrets** - Move all API keys, tokens, and credentials to secure storage
2. **Disable debuggable flag** - Set `android:debuggable="false"` for production builds
3. **Protect exported components** - Add permission protection or set `android:exported="false"`
4. **Implement certificate pinning** - Prevent man-in-the-middle attacks
5. **Validate deep links** - Implement strict validation for all deep link handlers

### Long-term Improvements

1. Update target SDK to latest Android version (API 33+)
2. Implement proper backup encryption or disable backups
3. Use HTTPS for all network communication
4. Implement runtime application self-protection (RASP)
5. Regular security audits and penetration testing

---

---

## 📂 Raw Data Attachments

Complete datasets have been exported to separate files for manual testing:
- **API Endpoints:** `{Path(str(output_path)).parent / (Path(str(output_path)).stem + "_endpoints.txt")}`
- **Secrets:** `{Path(str(output_path)).parent / (Path(str(output_path)).stem + "_secrets.txt")}`

---

## 📝 Methodology

This analysis was performed using **AppXploit Elite Framework**, an automated Android APK security analysis tool. The methodology includes:

1. **APK Extraction** - Decompiling APK using apktool and jadx
2. **Static Analysis** - Analyzing AndroidManifest.xml, components, and permissions
3. **Secrets Discovery** - Scanning decompiled code for hardcoded credentials
4. **API Extraction** - Identifying all API endpoints and URLs
5. **Business Logic Intelligence** - Detecting payment bypass, premium unlocks, price manipulation
6. **Advanced IDOR Detection** - Logic-based IDOR detection with identifier flow tracking
7. **Deep Link Abuse Analysis** - State-changing, auth-bypass, and callback abuse detection
8. **Crypto Misuse Intelligence** - Context-aware cryptography analysis
9. **Exploit Path Ranking** - Ranking findings by business impact, ease, and bug bounty acceptance
10. **Quality Control** - Evidence-based reporting with no speculation

---

## 👤 Report Author

**Name:** LAKSHMIKANTHAN K  
**GitHub:** letchupkt  
**Tool:** AppXploit - Professional Android APK Bug Hunting Tool

---

*This report is intended for authorized security testing only. Unauthorized testing or exploitation of vulnerabilities is illegal and unethical.*
"""
        
        return report
    
    def _format_top_3_ranked(self, ranked_findings: Dict[str, Any]) -> str:
        """Format TOP 3 most dangerous attack paths"""
        if not ranked_findings or not ranked_findings.get('top_3'):
            return ""
        
        top_3 = ranked_findings['top_3']
        medals = ['🥇', '🥈', '🥉']
        
        output = """## 🏆 TOP 3 MOST DANGEROUS ATTACK PATHS

> **ELITE FRAMEWORK**: These are the highest-value findings ranked by business impact, ease of exploitation, and bug bounty acceptance.

"""
        
        for i, finding in enumerate(top_3):
            medal = medals[i] if i < len(medals) else f'#{i+1}'
            rank_score = finding.get('rank_score', 0)
            breakdown = finding.get('rank_breakdown', {})
            
            output += f"""### {medal} RANK #{i+1} - Score: {rank_score}/10

**{finding['title']}**

**Severity:** {finding.get('severity', 'N/A').upper()}  
**Category:** {finding.get('category', 'N/A').replace('_', ' ').title()}  
**Confidence:** {finding.get('confidence', 0) * 100:.0f}%

#### Ranking Breakdown

- **Business Impact:** {breakdown.get('business_impact', 0)}/10
- **Ease of Exploitation:** {breakdown.get('ease_of_exploitation', 0)}/10
- **Bug Bounty Acceptance:** {breakdown.get('bug_bounty_acceptance', 0)}/10

#### Why This Is Exploitable

{finding.get('why_exploitable', finding.get('reasoning', 'No detailed explanation available.'))}

#### Real-World Impact

"""
            
            real_world = finding.get('real_world_impact', {})
            if real_world:
                output += f"""- **Users:** {real_world.get('users', 'N/A')}
- **Business:** {real_world.get('business', 'N/A')}
- **Security:** {real_world.get('security', 'N/A')}

"""
            
            output += "#### Exploitation Steps\n\n"
            
            exploitation_steps = finding.get('exploitation_steps', [])
            if exploitation_steps:
                for step in exploitation_steps:
                    output += f"{step}\n"
            else:
                output += "*No exploitation steps provided.*\n"
            
            output += "\n#### Remediation\n\n"
            output += f"{finding.get('remediation', 'No remediation provided.')}\n\n"
            
            if i < len(top_3) - 1:
                output += "---\n\n"
        
        return output
    
    def _format_exploit_chains(self, chains: list) -> str:
        """Format exploit chains section"""
        if not chains:
            return "*No exploit chains identified.*\n"
        
        output = ""
        for i, finding in enumerate(chains, 1):
            chain = finding['data']
            output += f"""### {i}. {chain['title']}

**Severity:** {chain['severity'].upper()}  
**CVSS Score:** {chain.get('cvss', 'N/A')}

#### Attack Path

"""
            for step in chain['steps']:
                output += f"- {step}\n"
            
            output += f"""
#### Impact

{chain['impact']}

#### Proof of Concept Outline

"""
            for poc_step in chain.get('poc_outline', []):
                output += f"{poc_step}\n"
            
            output += "\n---\n\n"
        
        return output
    
    def _format_vulnerabilities(self, vulnerabilities: list) -> str:
        """Format vulnerabilities section"""
        if not vulnerabilities:
            return "*No vulnerabilities identified.*\n"
        
        # Group by severity
        by_severity = {}
        for finding in vulnerabilities:
            vuln = finding['data']
            severity = vuln.get('final_severity', vuln.get('severity', 'medium'))
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(vuln)
        
        output = ""
        
        # Output in severity order
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity not in by_severity:
                continue
            
            vulns = by_severity[severity]
            output += f"### {severity.upper()} Severity ({len(vulns)})\n\n"
            
            for vuln in vulns:
                output += f"""#### {vuln['title']}

**CWE:** {vuln.get('cwe', 'N/A')}  
**Category:** {vuln.get('category', 'N/A').replace('_', ' ').title()}  
**Score:** {vuln.get('score', 0)}/100

**Description:**  
{vuln['description']}

**Impact:**  
{vuln['impact']}

**Remediation:**  
{vuln['remediation']}

"""
                if vuln.get('evidence'):
                    output += f"**Evidence:**\n```\n{json.dumps(vuln['evidence'], indent=2)}\n```\n"
                
                output += "\n---\n\n"
        
        return output
    
    def _format_endpoints(self, endpoints: list) -> str:
        """Format endpoints section"""
        if not endpoints:
            return "*No API endpoints discovered.*\n"
        
        # Group by category
        by_category = {}
        for endpoint in endpoints:
            category = endpoint.get('category', 'unknown')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(endpoint)
        
        output = f"**Total Endpoints:** {len(endpoints)}\n\n"
        
        for category, eps in by_category.items():
            output += f"### {category.replace('_', ' ').title()} ({len(eps)})\n\n"
            for ep in eps[:20]:  # Limit to 20 per category
                admin_flag = " 🔴 **ADMIN**" if ep.get('is_admin') else ""
                output += f"- `{ep['url']}`{admin_flag}\n"
            
            if len(eps) > 20:
                output += f"\n*...and {len(eps) - 20} more*\n"
            
            output += "\n"
        
        return output
    
    def _format_secrets(self, secrets: list) -> str:
        """Format secrets section"""
        if not secrets:
            return "*No secrets discovered.*\n"
        
        # Group by severity
        by_severity = {}
        for secret in secrets:
            severity = secret.get('severity', 'medium')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(secret)
        
        output = f"**Total Secrets:** {len(secrets)}\n\n"
        
        for severity in ['critical', 'high', 'medium']:
            if severity not in by_severity:
                continue
            
            secs = by_severity[severity]
            output += f"### {severity.upper()} ({len(secs)})\n\n"
            
            for secret in secs[:10]:  # Limit to 10 per severity
                output += f"- **{secret['type'].replace('_', ' ').title()}** in `{secret['file']}`\n"
            
            if len(secs) > 10:
                output += f"\n*...and {len(secs) - 10} more*\n"
            
            output += "\n"
        
        return output
