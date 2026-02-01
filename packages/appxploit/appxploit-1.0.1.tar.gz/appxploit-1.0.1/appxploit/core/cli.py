"""
AppXploit CLI Interface
Professional Android APK Security Analysis Tool
Author: LAKSHMIKANTHAN K (letchupkt)
"""

import click
import sys
import requests
from pathlib import Path
from colorama import init, Fore, Style

from appxploit import __version__, __author__
from appxploit.core.orchestrator import Orchestrator
from appxploit.core.config import Config

# Initialize colorama for cross-platform color support
init(autoreset=True)


def display_banner():
    """Display the AppXploit ASCII banner"""
    banner = f"""
{Fore.RED}          ___               _  __       __      _ __ 
{Fore.RED}         /   |  ____  ____ | |/ /____  / /___  (_) /_
{Fore.YELLOW}        / /| | / __ \/ __ \|   // __ \/ / __ \/ / __/
{Fore.YELLOW}       / ___ |/ /_/ / /_/ /   |/ /_/ / / /_/ / / /_  
{Fore.GREEN}      /_/  |_/ .___/ .___/_/|_/ .___/_/\____/_/\__/  
{Fore.GREEN}            /_/   /_/        /_/                     
{Style.RESET_ALL}
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
{Fore.CYAN}║  {Fore.WHITE}Professional Android APK Bug Hunting Tool{Fore.CYAN}                ║
{Fore.CYAN}║  {Fore.YELLOW}Version: {__version__}{Fore.CYAN}                                           ║
{Fore.CYAN}║  {Fore.GREEN}Author: {__author__}{Fore.CYAN}                     ║
{Fore.CYAN}╚═══════════════════════════════════════════════════════════╝
{Style.RESET_ALL}"""
    print(banner)


def check_for_updates():
    """Check PyPI for latest version and notify user if update available"""
    try:
        response = requests.get('https://pypi.org/pypi/appxploit/json', timeout=2)
        if response.status_code == 200:
            latest_version = response.json()['info']['version']
            if latest_version != __version__:
                print(f"{Fore.YELLOW}📦 Update available: {__version__} → {latest_version}")
                print(f"   Run: {Fore.CYAN}pip install --upgrade appxploit{Style.RESET_ALL}\n")
    except:
        # Silent fail - don't interrupt analysis for version check
        pass


@click.command()
@click.argument('apk_file', type=click.Path(exists=True))
@click.option('--output', '-o', default=None, help='Output report file path (default: <apk_name>_report.md)')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json']), default='markdown', help='Report format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--quick', '-q', is_flag=True, help='Quick scan (skip deep analysis)')
@click.option('--no-banner', is_flag=True, help='Suppress banner display')
def main(apk_file, output, format, verbose, quick, no_banner):
    """
    AppXploit - Professional Android APK Security Analysis Tool
    
    Analyzes Android APK files for security vulnerabilities, secrets, and API endpoints.
    Generates professional bug bounty reports with exploit chains.
    
    Example:
        appxploit target.apk
        appxploit target.apk -o report.md -v
        appxploit target.apk --quick
    """
    try:
        # Display banner
        if not no_banner:
            display_banner()
        
        # Convert APK file to Path object
        apk_path = Path(apk_file).resolve()
        
        # Validate APK file
        if not apk_path.suffix.lower() == '.apk':
            click.echo(f"{Fore.RED}[!] Error: File must be an APK file{Style.RESET_ALL}")
            sys.exit(1)
        
        # Determine output file (use current directory by default)
        if output is None:
            # Use current working directory instead of APK directory
            output_path = Path.cwd() / f"{apk_path.stem}_report.{format if format == 'json' else 'md'}"
        else:
            output_path = Path(output).resolve()
        
        # Display scan info
        click.echo(f"\n{Fore.CYAN}[*] Target APK:{Style.RESET_ALL} {apk_path.name}")
        click.echo(f"{Fore.CYAN}[*] Output:{Style.RESET_ALL} {output_path}")
        click.echo(f"{Fore.CYAN}[*] Mode:{Style.RESET_ALL} {'Quick Scan' if quick else 'Deep Analysis'}")
        click.echo(f"{Fore.CYAN}[*] Verbose:{Style.RESET_ALL} {'Enabled' if verbose else 'Disabled'}\n")
        
        # Check for updates (non-blocking)
        if not no_banner:
            check_for_updates()
        
        # Initialize configuration
        config = Config(verbose=verbose, quick=quick, output_format=format)
        
        # Initialize orchestrator
        orchestrator = Orchestrator(apk_path, output_path, config)
        
        # Run analysis
        click.echo(f"{Fore.YELLOW}[*] Starting analysis...{Style.RESET_ALL}\n")
        result = orchestrator.run()
        
        if result:
            click.echo(f"\n{Fore.GREEN}[✓] Analysis complete!{Style.RESET_ALL}")
            click.echo(f"{Fore.GREEN}[✓] Report saved to: {output_path}{Style.RESET_ALL}\n")
        else:
            click.echo(f"\n{Fore.RED}[!] Analysis failed. Check logs for details.{Style.RESET_ALL}\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo(f"\n\n{Fore.YELLOW}[!] Analysis interrupted by user{Style.RESET_ALL}")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n{Fore.RED}[!] Fatal error: {str(e)}{Style.RESET_ALL}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
