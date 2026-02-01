"""
Task orchestration engine
Coordinates the entire analysis pipeline
"""

import os
from pathlib import Path
from typing import Dict, Any
from colorama import Fore, Style

from appxploit.core.config import Config
from appxploit.core.utils import Utils
from appxploit.intelligence.fingerprint import APKFingerprint
from appxploit.intelligence.classifier import AppClassifier
from appxploit.intelligence.risk_estimator import RiskEstimator
from appxploit.analysis.manifest import ManifestAnalyzer
from appxploit.analysis.components import ComponentAnalyzer
from appxploit.analysis.permissions import PermissionAnalyzer
from appxploit.analysis.security_flags import SecurityFlagsAnalyzer
from appxploit.analysis.deeplink_analyzer import DeepLinkAnalyzer
from appxploit.discovery.secrets import SecretsDiscovery
from appxploit.discovery.endpoints import EndpointExtractor
from appxploit.reasoning.detector import VulnerabilityDetector
from appxploit.reasoning.advanced_detector import AdvancedDetector
from appxploit.reasoning.business_logic import BusinessLogicDetector
from appxploit.reasoning.idor_detector import IDORDetector
from appxploit.reasoning.crypto_analyzer import CryptoAnalyzer
from appxploit.reasoning.scorer import VulnerabilityScorer
from appxploit.reasoning.exploits import ExploitChainer
from appxploit.reasoning.path_ranker import ExploitPathRanker
from appxploit.filtering.filter import NoiseFilter
from appxploit.filtering.quality_control import QualityControl
from appxploit.reporting.generator import ReportGenerator


class Orchestrator:
    """Main orchestration engine for AppXploit"""
    
    def __init__(self, apk_path: Path, output_path: Path, config: Config):
        self.apk_path = apk_path
        self.output_path = output_path
        self.config = config
        self.work_dir = config.get_work_dir(apk_path.stem)
        
        # Analysis results storage
        self.results: Dict[str, Any] = {
            'apk_info': {},
            'fingerprint': {},
            'classification': {},
            'risk_profile': {},
            'manifest': {},
            'components': {},
            'permissions': {},
            'security_flags': {},
            'deep_links': [],
            'secrets': [],
            'endpoints': [],
            'vulnerabilities': [],
            'exploit_chains': [],
            'filtered_findings': [],
            'ranked_findings': {}
        }
    
    def run(self) -> bool:
        """
        Execute the complete analysis pipeline
        
        Returns:
            True if successful
        """
        try:
            # Step 0: Check dependencies
            if not self._check_dependencies():
                return False
            
            # Step 1: Extract APK
            if not self._extract_apk():
                return False
            
            # Step 2: APK Intelligence
            if not self._run_intelligence():
                return False
            
            # Step 3: Static Analysis
            if not self._run_static_analysis():
                return False
            
            # Step 4: Secrets & API Discovery
            if not self._run_discovery():
                return False
            
            # Step 5: Vulnerability Reasoning
            if not self._run_vulnerability_reasoning():
                return False
            
            # Step 6: Exploit Path Correlation
            if not self._run_exploit_correlation():
                return False
            
            # Step 7: Noise Filtering
            if not self._run_noise_filtering():
                return False
            
            # Step 8: Generate Report
            if not self._generate_report():
                return False
            
            # Cleanup
            if not self.config.verbose:
                Utils.cleanup_temp(self.config.verbose)
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Orchestration error: {str(e)}{Style.RESET_ALL}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def _check_dependencies(self) -> bool:
        """Check all dependencies"""
        return self.config.check_dependencies()
    
    def _extract_apk(self) -> bool:
        """Extract APK using apktool"""
        print(f"{Fore.CYAN}[1/8] Extracting APK...{Style.RESET_ALL}")
        
        try:
            extract_dir = self.work_dir / 'extracted'
            
            # Run apktool
            cmd = [
                'java', '-jar', str(self.config.apktool_path),
                'd', str(self.apk_path),
                '-o', str(extract_dir),
                '-f'  # Force overwrite
            ]
            
            returncode, stdout, stderr = Utils.run_command(cmd, verbose=self.config.verbose)
            
            if returncode != 0:
                print(f"{Fore.RED}[!] APK extraction failed{Style.RESET_ALL}")
                if self.config.verbose:
                    print(stderr)
                return False
            
            self.results['apk_info']['extract_dir'] = extract_dir
            print(f"{Fore.GREEN}[✓] APK extracted{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Extraction error: {str(e)}{Style.RESET_ALL}")
            return False
    
    def _run_intelligence(self) -> bool:
        """Run APK intelligence analysis"""
        print(f"{Fore.CYAN}[2/8] Running APK intelligence...{Style.RESET_ALL}")
        
        try:
            extract_dir = self.results['apk_info']['extract_dir']
            
            # Fingerprinting
            fingerprint = APKFingerprint(extract_dir, self.config)
            self.results['fingerprint'] = fingerprint.analyze()
            
            # Classification
            classifier = AppClassifier(self.results['fingerprint'], self.config)
            self.results['classification'] = classifier.classify()
            
            # Risk estimation
            risk_estimator = RiskEstimator(self.results['fingerprint'], self.config)
            self.results['risk_profile'] = risk_estimator.estimate()
            
            print(f"{Fore.GREEN}[✓] Intelligence complete{Style.RESET_ALL}")
            if self.config.verbose:
                print(f"    App Type: {self.results['classification'].get('app_type', 'Unknown')}")
                print(f"    Risk Level: {self.results['risk_profile'].get('risk_level', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Intelligence error: {str(e)}{Style.RESET_ALL}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def _run_static_analysis(self) -> bool:
        """Run static analysis"""
        print(f"{Fore.CYAN}[3/8] Running static analysis...{Style.RESET_ALL}")
        
        try:
            extract_dir = self.results['apk_info']['extract_dir']
            
            # Manifest analysis
            manifest_analyzer = ManifestAnalyzer(extract_dir, self.config)
            self.results['manifest'] = manifest_analyzer.analyze()
            
            # Component analysis
            component_analyzer = ComponentAnalyzer(self.results['manifest'], self.config)
            self.results['components'] = component_analyzer.analyze()
            
            # Permission analysis
            permission_analyzer = PermissionAnalyzer(self.results['manifest'], self.config)
            self.results['permissions'] = permission_analyzer.analyze()
            
            # Security flags
            security_analyzer = SecurityFlagsAnalyzer(self.results['manifest'], extract_dir, self.config)
            self.results['security_flags'] = security_analyzer.analyze()
            
            print(f"{Fore.GREEN}[✓] Static analysis complete{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Static analysis error: {str(e)}{Style.RESET_ALL}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def _run_discovery(self) -> bool:
        """Run secrets and API discovery"""
        print(f"{Fore.CYAN}[4/8] Discovering secrets and APIs...{Style.RESET_ALL}")
        
        try:
            # Fix JAVA_HOME if invalid (common issue on Windows)
            java_home = os.environ.get('JAVA_HOME', '')
            if not java_home or not os.path.exists(java_home):
                if Utils.is_windows():
                    possible_roots = [
                        Path('C:/Program Files/Java'),
                        Path('C:/Program Files (x86)/Java'),
                        Path(os.environ.get('USERPROFILE', '')) / '.jdks'
                    ]
                    
                    for root in possible_roots:
                        if root.exists():
                            # Find subdirectories starting with jdk
                            jdks = list(root.glob('jdk*'))
                            if jdks:
                                jdks.sort(reverse=True)
                                new_home = str(jdks[0])
                                os.environ['JAVA_HOME'] = new_home
                                print(f"{Fore.YELLOW}  [*] Auto-corrected JAVA_HOME to: {new_home}{Style.RESET_ALL}")
                                break
            
            # Decompile with jadx first
            decompiled_dir = self.work_dir / 'decompiled'
            # Increase memory via environment variable (works for both Windows/Linux wrappers)
            os.environ['JAVA_TOOL_OPTIONS'] = '-Xmx4g'
            
            cmd = [
                str(self.config.jadx_path),
                str(self.apk_path),
                '-d', str(decompiled_dir),
                '--no-res',  # Skip resources for speed
                '--no-debug-info'
            ]
            
            print(f"{Fore.YELLOW}  [*] Decompiling with jadx...{Style.RESET_ALL}")
            returncode, stdout, stderr = Utils.run_command(cmd, verbose=self.config.verbose)
            
            if returncode != 0:
                print(f"{Fore.YELLOW}  [!] Decompilation had warnings (continuing anyway){Style.RESET_ALL}")
            
            # Secrets discovery
            secrets_discovery = SecretsDiscovery(decompiled_dir, self.config)
            self.results['secrets'] = secrets_discovery.discover()
            
            # Endpoint extraction
            endpoint_extractor = EndpointExtractor(decompiled_dir, self.config)
            self.results['endpoints'] = endpoint_extractor.extract()
            
            print(f"{Fore.GREEN}[✓] Discovery complete{Style.RESET_ALL}")
            if self.config.verbose:
                print(f"    Secrets found: {len(self.results['secrets'])}")
                print(f"    Endpoints found: {len(self.results['endpoints'])}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Discovery error: {str(e)}{Style.RESET_ALL}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def _run_vulnerability_reasoning(self) -> bool:
        """Run vulnerability detection and scoring"""
        print(f"{Fore.CYAN}[5/8] Analyzing vulnerabilities...{Style.RESET_ALL}")
        
        try:
            # Detect basic vulnerabilities
            detector = VulnerabilityDetector(self.results, self.config)
            vulnerabilities = detector.detect()
            
            # Detect advanced vulnerabilities (new)
            # REASONING: Advanced detector finds real-world issues like client-side auth,
            # IDOR, weak crypto, WebView issues, etc.
            decompiled_dir = self.work_dir / 'decompiled'
            extract_dir = self.results['apk_info']['extract_dir']
            manifest_path = extract_dir / 'AndroidManifest.xml'
            
            if decompiled_dir.exists():
                advanced_detector = AdvancedDetector(self.config)
                advanced_vulns = advanced_detector.detect(decompiled_dir, self.results)
                vulnerabilities.extend(advanced_vulns)
                
                if self.config.verbose and advanced_vulns:
                    print(f"{Fore.YELLOW}  [*] Advanced vulnerabilities found: {len(advanced_vulns)}{Style.RESET_ALL}")
                
                # ELITE FRAMEWORK - Business Logic Intelligence
                # REASONING: Highest-value vulnerabilities - payment bypass, premium unlocks
                business_logic_detector = BusinessLogicDetector(self.config)
                business_logic_vulns = business_logic_detector.detect(decompiled_dir, self.results)
                vulnerabilities.extend(business_logic_vulns)
                
                if self.config.verbose and business_logic_vulns:
                    print(f"{Fore.YELLOW}  [*] Business logic flaws: {len(business_logic_vulns)}{Style.RESET_ALL}")
                
                # ELITE FRAMEWORK - Advanced IDOR Detection
                # REASONING: Logic-based IDOR detection with flow tracking
                idor_detector = IDORDetector(self.config)
                idor_vulns = idor_detector.detect(decompiled_dir, self.results)
                vulnerabilities.extend(idor_vulns)
                
                if self.config.verbose and idor_vulns:
                    print(f"{Fore.YELLOW}  [*] IDOR vulnerabilities: {len(idor_vulns)}{Style.RESET_ALL}")
                
                # ELITE FRAMEWORK - Crypto Misuse Intelligence
                # REASONING: Context-aware crypto analysis - only exploitable issues
                crypto_analyzer = CryptoAnalyzer(self.config)
                crypto_vulns = crypto_analyzer.analyze(decompiled_dir)
                vulnerabilities.extend(crypto_vulns)
                
                if self.config.verbose and crypto_vulns:
                    print(f"{Fore.YELLOW}  [*] Crypto misuse: {len(crypto_vulns)}{Style.RESET_ALL}")
                
                # ELITE FRAMEWORK - Deep Link Abuse Detection
                # REASONING: State-changing, auth-bypass, and callback abuse
                if manifest_path.exists():
                    deeplink_analyzer = DeepLinkAnalyzer(self.config)
                    deeplink_vulns = deeplink_analyzer.analyze(manifest_path, decompiled_dir)
                    vulnerabilities.extend(deeplink_vulns)
                    self.results['deep_links'] = deeplink_vulns
                    
                    if self.config.verbose and deeplink_vulns:
                        print(f"{Fore.YELLOW}  [*] Deep link vulnerabilities: {len(deeplink_vulns)}{Style.RESET_ALL}")
            
            # ELITE FRAMEWORK - Quality Control
            # REASONING: Filter out speculative findings, ensure evidence-based reporting
            quality_control = QualityControl(self.config)
            vulnerabilities = quality_control.validate_findings(vulnerabilities)
            
            if self.config.verbose:
                print(f"{Fore.YELLOW}  [*] After quality control: {len(vulnerabilities)} findings{Style.RESET_ALL}")
            
            # Score all vulnerabilities (with new ContextConfidence factor)
            scorer = VulnerabilityScorer(self.config)
            scored_vulns = scorer.score_all(vulnerabilities)
            
            self.results['vulnerabilities'] = scored_vulns
            
            print(f"{Fore.GREEN}[✓] Vulnerability analysis complete{Style.RESET_ALL}")
            if self.config.verbose:
                print(f"    Vulnerabilities found: {len(scored_vulns)}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Vulnerability reasoning error: {str(e)}{Style.RESET_ALL}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def _run_exploit_correlation(self) -> bool:
        """Run exploit path correlation"""
        print(f"{Fore.CYAN}[6/8] Correlating exploit chains...{Style.RESET_ALL}")
        
        try:
            chainer = ExploitChainer(self.results, self.config)
            exploit_chains = chainer.chain()
            
            self.results['exploit_chains'] = exploit_chains
            
            # ELITE FRAMEWORK - Exploit Path Ranking
            # REASONING: Rank all findings (chains + individual) by business impact, ease, and acceptance
            # Highlight TOP 1-3 most dangerous paths
            all_findings = self.results['vulnerabilities'] + exploit_chains
            
            if all_findings:
                ranker = ExploitPathRanker(self.config)
                ranked_results = ranker.rank(all_findings)
                
                self.results['ranked_findings'] = ranked_results
                
                if self.config.verbose:
                    print(f"{Fore.YELLOW}  [*] Top 3 most dangerous paths identified{Style.RESET_ALL}")
                    # Print ranking summary
                    if ranked_results.get('summary'):
                        print(f"\n{ranked_results['summary']}\n")
            
            print(f"{Fore.GREEN}[✓] Exploit correlation complete{Style.RESET_ALL}")
            if self.config.verbose:
                print(f"    Exploit chains found: {len(exploit_chains)}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Exploit correlation error: {str(e)}{Style.RESET_ALL}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return False
        
    def _run_noise_filtering(self) -> bool:
        """Filter out noise and low-impact findings"""
        print(f"{Fore.CYAN}[7/8] Filtering noise...{Style.RESET_ALL}")
        
        try:
            noise_filter = NoiseFilter(self.config)
            filtered = noise_filter.filter(
                self.results['vulnerabilities'],
                self.results['exploit_chains']
            )
            
            self.results['filtered_findings'] = filtered
            
            print(f"{Fore.GREEN}[✓] Filtering complete{Style.RESET_ALL}")
            if self.config.verbose:
                print(f"    High-signal findings: {len(filtered)}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Filtering error: {str(e)}{Style.RESET_ALL}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def _generate_report(self) -> bool:
        """Generate final report"""
        print(f"{Fore.CYAN}[8/8] Generating report...{Style.RESET_ALL}")
        
        try:
            generator = ReportGenerator(self.config)
            success = generator.generate(self.results, self.output_path)
            
            if success:
                print(f"{Fore.GREEN}[✓] Report generated{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}[!] Report generation failed{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}[!] Report generation error: {str(e)}{Style.RESET_ALL}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return False
