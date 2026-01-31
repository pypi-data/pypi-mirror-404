#!/usr/bin/env python3
"""
GuardeScan Command Line Interface
The world's easiest smart contract security scanner
"""

import sys
import os
import io
import json
import time
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

from guardescan import __version__
from guardescan.core import GuardeScan, ScanResult, Severity, Grade
from guardescan.reports import generate_all_reports, generate_html_report, generate_sarif_report, generate_markdown_report
from guardescan.chains import MultiChainScanner, Chain, ChainScanResult
from guardescan.advanced import AdvancedScanner, DeFiAnalyzer, MLVulnerabilityDetector
from guardescan.chains_enhanced import EnhancedMultiChainScanner, Chain as EnhancedChain, Severity as ChainSeverity
from guardescan.benchmark import run_benchmark, compare_tools, GuardeScanBenchmark, REAL_WORLD_EXPLOITS
from guardescan.slither_engine import GuardeScanEngine, check_slither, ScanResult as SlitherScanResult


# ==============================================================================
# COLORS
# ==============================================================================

class Colors:
    """Terminal colors"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    @classmethod
    def disable(cls):
        """Disable all colors"""
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''
        cls.END = ''

# Enable colors on Windows
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        Colors.disable()


# ==============================================================================
# OUTPUT FORMATTING
# ==============================================================================

def print_banner():
    """Print the GuardeScan banner"""
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗
║   ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ███████╗███████╗ ██████╗ █████╗ ███╗   ██╗  ║
║  ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║  ║
║  ██║  ███╗██║   ██║███████║██████╔╝██║  ██║█████╗  ███████╗██║     ███████║██╔██╗ ██║  ║
║  ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║██╔══╝  ╚════██║██║     ██╔══██║██║╚██╗██║  ║
║  ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝███████╗███████║╚██████╗██║  ██║██║ ╚████║  ║
║   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ║
║                                                                  ║
║              The World's Easiest Smart Contract Scanner           ║
║                         Version {__version__}                              ║
╚══════════════════════════════════════════════════════════════════╝{Colors.END}
""")


def print_result(result: ScanResult, verbose: bool = False):
    """Print scan result to console"""
    
    grade_colors = {
        'A+': Colors.GREEN, 'A': Colors.GREEN,
        'B+': Colors.CYAN, 'B': Colors.CYAN,
        'C+': Colors.YELLOW, 'C': Colors.YELLOW,
        'D+': Colors.RED, 'D': Colors.RED,
        'F': Colors.RED
    }
    
    severity_colors = {
        Severity.CRITICAL: Colors.RED,
        Severity.HIGH: Colors.RED,
        Severity.MEDIUM: Colors.YELLOW,
        Severity.LOW: Colors.GREEN,
        Severity.INFO: Colors.BLUE
    }
    
    color = grade_colors.get(result.grade.value, Colors.END)
    
    print(f"""
{Colors.BOLD}{'='*60}{Colors.END}
{Colors.BOLD}SCAN RESULTS: {result.contract_name}{Colors.END}
{Colors.BOLD}{'='*60}{Colors.END}

{Colors.BOLD}GRADE:{Colors.END} {color}{result.grade.value}{Colors.END} ({result.score:.1f}/100)
{Colors.BOLD}RISK:{Colors.END} {result.risk_rating}
{Colors.BOLD}SOLIDITY:{Colors.END} {result.solidity_version or 'Unknown'}
{Colors.BOLD}SCAN TIME:{Colors.END} {result.scan_time:.2f}s
{Colors.BOLD}SCANNERS:{Colors.END} {', '.join(result.scanners_used)}

{Colors.BOLD}VULNERABILITIES ({len(result.vulnerabilities)}):{Colors.END}
""")
    
    if not result.vulnerabilities:
        print(f"  {Colors.GREEN}✓ No vulnerabilities detected!{Colors.END}")
    else:
        for i, v in enumerate(result.vulnerabilities, 1):
            sev_color = severity_colors.get(v.severity, Colors.END)
            print(f"  {i}. {sev_color}[{v.severity.value.upper()}]{Colors.END} {v.title}")
            print(f"     Confidence: {v.confidence:.0%} | Line: {v.line_number or 'N/A'}")
            print(f"     {Colors.CYAN}→ {v.recommendation}{Colors.END}")
            
            if verbose and v.code_snippet:
                print(f"     Code:")
                for line in v.code_snippet.split('\n')[:3]:
                    print(f"       {Colors.YELLOW}{line}{Colors.END}")
            print()
    
    if result.gas_issues:
        print(f"\n{Colors.BOLD}GAS OPTIMIZATION ({len(result.gas_issues)} issues):{Colors.END}")
        for g in result.gas_issues[:5]:
            print(f"  • {g.description} (Line {g.line_number or 'N/A'}, ~{g.savings_percent}% savings)")
    
    if result.errors:
        print(f"\n{Colors.RED}ERRORS:{Colors.END}")
        for err in result.errors:
            print(f"  • {err}")
    
    if result.warnings:
        print(f"\n{Colors.YELLOW}WARNINGS:{Colors.END}")
        for warn in result.warnings:
            print(f"  • {warn}")
    
    print(f"\n{'='*60}\n")


def print_summary(results: List[ScanResult]):
    """Print summary for multiple scan results"""
    total_vulns = sum(len(r.vulnerabilities) for r in results)
    critical = sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.CRITICAL)
    high = sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.HIGH)
    
    print(f"""
{Colors.BOLD}PROJECT SUMMARY{Colors.END}
{'─'*40}
Contracts scanned: {len(results)}
Total vulnerabilities: {total_vulns}
  Critical: {Colors.RED}{critical}{Colors.END}
  High: {Colors.YELLOW}{high}{Colors.END}
""")
    
    for r in results:
        grade_color = Colors.GREEN if r.grade.value.startswith('A') else Colors.YELLOW if r.grade.value.startswith(('B', 'C')) else Colors.RED
        print(f"  {r.contract_name}: {grade_color}{r.grade.value}{Colors.END} ({len(r.vulnerabilities)} issues)")


# ==============================================================================
# COMMANDS
# ==============================================================================

def cmd_scan(args):
    """Handle scan command - Slither + Enhanced patterns"""
    
    target = args.target
    
    print(f"\n{Colors.BOLD}GuardeScan Security Analysis{Colors.END}")
    print(f"Powered by Slither + Enhanced Detection")
    print(f"{'='*60}\n")
    
    # Check Slither status
    slither_status = check_slither()
    if slither_status['installed']:
        print(f"{Colors.GREEN}✓ Slither: {slither_status['version']}{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠ Slither not installed - using pattern matching only{Colors.END}")
        print(f"  Install: {slither_status['install_command']}")
    
    print(f"\nScanning: {target}")
    print(f"{'─'*60}\n")
    
    # Use new Slither-powered engine
    engine = GuardeScanEngine()
    
    try:
        result = engine.scan(target)
    except Exception as e:
        print(f"{Colors.RED}Error scanning {target}: {e}{Colors.END}")
        return 1
    
    # JSON output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0
    
    # Grade colors
    grade_colors = {
        'A+': Colors.GREEN, 'A': Colors.GREEN, 'A-': Colors.GREEN,
        'B+': Colors.CYAN, 'B': Colors.CYAN, 'B-': Colors.CYAN,
        'C+': Colors.YELLOW, 'C': Colors.YELLOW, 'C-': Colors.YELLOW,
        'D': Colors.RED, 'F': Colors.RED
    }
    grade_color = grade_colors.get(result.grade, Colors.END)
    
    # Print summary
    print(f"{Colors.BOLD}SCAN RESULTS{Colors.END}")
    print(f"{'─'*40}")
    print(f"  Contract: {result.contract_name}")
    print(f"  Grade: {grade_color}{result.grade}{Colors.END}")
    print(f"  Score: {result.score:.1f}/100")
    print(f"  Lines: {result.lines_of_code}")
    print(f"  Time: {result.scan_time:.2f}s")
    
    # Findings by source
    print(f"\n{Colors.BOLD}FINDINGS BY SOURCE{Colors.END}")
    print(f"{'─'*40}")
    print(f"  {Colors.BLUE}Slither (Core):{Colors.END}     {len(result.slither_findings)}")
    print(f"  {Colors.CYAN}Enhanced Patterns:{Colors.END}  {len(result.enhanced_findings)}")
    print(f"  {Colors.YELLOW}DeFi Analysis:{Colors.END}      {len(result.defi_findings)}")
    print(f"  {Colors.GREEN}Gas Optimizations:{Colors.END}  {len(result.gas_findings)}")
    print(f"  {'─'*20}")
    print(f"  {Colors.BOLD}TOTAL:{Colors.END}              {len(result.all_vulnerabilities)}")
    
    # Severity breakdown
    print(f"\n{Colors.BOLD}SEVERITY BREAKDOWN{Colors.END}")
    print(f"{'─'*40}")
    
    sev_icons = {
        'critical': ('🔴', Colors.RED),
        'high': ('🟠', Colors.RED),
        'medium': ('🟡', Colors.YELLOW),
        'low': ('🟢', Colors.GREEN),
        'info': ('⚪', Colors.HEADER),
        'optimization': ('⚡', Colors.CYAN),
    }
    
    sev_counts = {}
    for v in result.all_vulnerabilities:
        sev = v.severity.value
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
    
    for sev in ['critical', 'high', 'medium', 'low', 'info', 'optimization']:
        count = sev_counts.get(sev, 0)
        icon, color = sev_icons.get(sev, ('•', Colors.END))
        print(f"  {icon} {color}{sev.upper():12}{Colors.END}: {count}")
    
    # Detailed findings
    if result.all_vulnerabilities:
        print(f"\n{Colors.BOLD}VULNERABILITIES{Colors.END}")
        print(f"{'─'*40}")
        
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4, 'optimization': 5}
        sorted_vulns = sorted(result.all_vulnerabilities, 
                             key=lambda v: severity_order.get(v.severity.value, 5))
        
        for i, v in enumerate(sorted_vulns[:15], 1):
            icon, color = sev_icons.get(v.severity.value, ('•', Colors.END))
            
            print(f"\n  {i}. {color}[{v.severity.value.upper()}]{Colors.END} {v.title}")
            print(f"     {Colors.HEADER}Source:{Colors.END} {v.source}")
            if v.contract:
                print(f"     {Colors.HEADER}Contract:{Colors.END} {v.contract}")
            if v.line_number:
                print(f"     {Colors.HEADER}Line:{Colors.END} {v.line_number}")
            if v.description:
                desc = v.description[:100] + "..." if len(v.description) > 100 else v.description
                print(f"     {desc}")
            if v.recommendation:
                rec = v.recommendation[:70] + "..." if len(v.recommendation) > 70 else v.recommendation
                print(f"     {Colors.CYAN}→ {rec}{Colors.END}")
        
        if len(result.all_vulnerabilities) > 15:
            print(f"\n  {Colors.HEADER}... and {len(result.all_vulnerabilities) - 15} more{Colors.END}")
    else:
        print(f"\n{Colors.GREEN}✓ No significant vulnerabilities found!{Colors.END}")
    
    # Errors and warnings
    if result.errors:
        print(f"\n{Colors.RED}ERRORS:{Colors.END}")
        for err in result.errors[:3]:
            print(f"  • {err[:80]}")
    
    if result.warnings:
        print(f"\n{Colors.YELLOW}WARNINGS:{Colors.END}")
        for warn in result.warnings[:3]:
            print(f"  • {warn[:80]}")
    
    # Generate reports
    if args.all_reports:
        base = Path(target).stem
        print(f"\n{Colors.BOLD}Generating reports...{Colors.END}")
        # Use legacy scanner for reports
        legacy = GuardeScan()
        legacy_result = legacy.scan(target)
        generate_all_reports(legacy_result, base)
    else:
        if hasattr(args, 'html') and args.html:
            legacy = GuardeScan()
            legacy_result = legacy.scan(target)
            generate_html_report(legacy_result, args.html)
            print(f"HTML report: {args.html}")
        if hasattr(args, 'sarif') and args.sarif:
            legacy = GuardeScan()
            legacy_result = legacy.scan(target)
            generate_sarif_report(legacy_result, args.sarif)
            print(f"SARIF report: {args.sarif}")
    
    print(f"\n{'='*60}\n")
    
    # Exit code
    if result.critical_count > 0:
        return 2
    elif result.high_count > 0:
        return 1
    return 0


def cmd_watch(args):
    """Handle watch command"""
    import hashlib
    
    scanner = GuardeScan()
    target = args.target or '.'
    
    print(f"{Colors.CYAN}Watching {target} for changes...{Colors.END}")
    print("Press Ctrl+C to stop.\n")
    
    last_hash = {}
    
    try:
        while True:
            for sol_file in Path(target).glob('**/*.sol'):
                if 'node_modules' in str(sol_file) or 'lib' in str(sol_file):
                    continue
                
                file_path = str(sol_file)
                
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                except:
                    continue
                
                if file_path not in last_hash or last_hash[file_path] != file_hash:
                    print(f"\n{Colors.YELLOW}Change detected: {sol_file.name}{Colors.END}")
                    
                    try:
                        result = scanner.scan(file_path, use_cache=False)
                        print(f"  Grade: {result.grade.value} | Vulns: {len(result.vulnerabilities)}")
                        
                        for v in result.vulnerabilities[:3]:
                            color = Colors.RED if v.severity in [Severity.CRITICAL, Severity.HIGH] else Colors.YELLOW
                            print(f"    {color}[{v.severity.value.upper()}]{Colors.END} {v.title}")
                    except Exception as e:
                        print(f"  {Colors.RED}Error: {e}{Colors.END}")
                    
                    last_hash[file_path] = file_hash
            
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}Watch stopped.{Colors.END}")
    
    return 0


def cmd_project(args):
    """Handle project command"""
    scanner = GuardeScan()
    
    print("Scanning project...")
    results = scanner.scan_directory('.', exclude=['node_modules', 'lib', 'test', '.git'])
    
    if args.json:
        output = {
            'project': os.path.basename(os.getcwd()),
            'contracts': [r.to_dict() for r in results],
            'summary': {
                'total_contracts': len(results),
                'total_vulnerabilities': sum(len(r.vulnerabilities) for r in results),
                'average_score': sum(r.score for r in results) / len(results) if results else 0
            }
        }
        print(json.dumps(output, indent=2))
    else:
        print_summary(results)
    
    return 0


def cmd_fix(args):
    """Handle fix command (generate auto-fixed version)"""
    from guardescan.fixer import generate_fix
    
    input_file = args.input
    output_file = args.output or input_file.replace('.sol', '_fixed.sol')
    
    fixed_code, fixes = generate_fix(input_file)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_code)
    
    print(f"{Colors.GREEN}Fixed contract saved to: {output_file}{Colors.END}")
    
    if fixes:
        print(f"\nFixes applied:")
        for fix in fixes:
            print(f"  • {fix}")
    else:
        print(f"\n{Colors.YELLOW}No auto-fixes available for detected issues.{Colors.END}")
    
    return 0


def cmd_diff(args):
    """Handle diff command (compare two contracts)"""
    scanner = GuardeScan()
    
    result1 = scanner.scan(args.file1)
    result2 = scanner.scan(args.file2)
    
    vulns1 = {v.vuln_id for v in result1.vulnerabilities}
    vulns2 = {v.vuln_id for v in result2.vulnerabilities}
    
    fixed = vulns1 - vulns2
    new = vulns2 - vulns1
    common = vulns1 & vulns2
    
    if args.json:
        output = {
            'file1': {'path': args.file1, 'grade': result1.grade.value, 'vulnerabilities': len(result1.vulnerabilities)},
            'file2': {'path': args.file2, 'grade': result2.grade.value, 'vulnerabilities': len(result2.vulnerabilities)},
            'fixed': list(fixed),
            'new': list(new),
            'common': list(common),
            'improved': result2.score > result1.score
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"""
{Colors.BOLD}Contract Comparison{Colors.END}
{'─'*40}
{args.file1}: {result1.grade.value} ({len(result1.vulnerabilities)} vulnerabilities)
{args.file2}: {result2.grade.value} ({len(result2.vulnerabilities)} vulnerabilities)

Fixed vulnerabilities: {', '.join(fixed) if fixed else 'None'}
New vulnerabilities: {', '.join(new) if new else 'None'}

Security improved: {Colors.GREEN}Yes{Colors.END if result2.score > result1.score else f'{Colors.RED}No{Colors.END}'}
""")
    
    return 0


def cmd_setup(args):
    """Handle setup command"""
    import shutil
    
    print(f"\n{Colors.BOLD}GuardeScan Setup{Colors.END}\n")
    print("Checking dependencies...\n")
    
    checks = [
        ("Python 3.8+", lambda: sys.version_info >= (3, 8), "Required"),
        ("Slither", lambda: shutil.which('slither') is not None, "pip install slither-analyzer"),
        ("solc", lambda: shutil.which('solc') is not None or shutil.which('solc-select') is not None, "pip install solc-select"),
    ]
    
    all_ok = True
    for name, check, fix in checks:
        try:
            ok = check()
        except:
            ok = False
        
        status = f"{Colors.GREEN}✓ OK{Colors.END}" if ok else f"{Colors.RED}✗ MISSING{Colors.END}"
        print(f"  {name}: {status}")
        
        if not ok:
            print(f"    Install: {Colors.YELLOW}{fix}{Colors.END}")
            all_ok = False
    
    print()
    
    if all_ok:
        print(f"{Colors.GREEN}All dependencies installed! GuardeScan is ready.{Colors.END}")
    else:
        print(f"""
{Colors.YELLOW}Some optional dependencies are missing.{Colors.END}
GuardeScan will still work, but with reduced functionality.

Quick install:
  pip install slither-analyzer
  pip install solc-select && solc-select install 0.8.20 && solc-select use 0.8.20
""")
    
    return 0 if all_ok else 1


def cmd_multichain(args):
    """Handle multichain scan command"""
    scanner = MultiChainScanner()
    
    target = args.target
    chain = Chain(args.chain) if args.chain else None
    
    print(f"\n{Colors.BOLD}Multi-Chain Security Scanner{Colors.END}")
    print(f"{'─'*50}\n")
    
    result = scanner.scan(target, chain=chain)
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0
    
    # Print result
    chain_color = {
        Chain.ETHEREUM: Colors.BLUE,
        Chain.SOLANA: Colors.CYAN,
        Chain.APTOS: Colors.GREEN,
        Chain.STARKNET: Colors.YELLOW,
        Chain.COSMOS: Colors.HEADER
    }.get(result.chain, Colors.END)
    
    print(f"{Colors.BOLD}Chain:{Colors.END} {chain_color}{result.chain.value.upper()}{Colors.END}")
    print(f"{Colors.BOLD}Language:{Colors.END} {result.language}")
    print(f"{Colors.BOLD}Contract:{Colors.END} {result.contract_name}")
    print(f"{Colors.BOLD}Scan Time:{Colors.END} {result.scan_time:.2f}s")
    
    print(f"\n{Colors.BOLD}VULNERABILITIES ({len(result.vulnerabilities)}):{Colors.END}")
    
    if not result.vulnerabilities:
        print(f"  {Colors.GREEN}✓ No vulnerabilities detected!{Colors.END}")
    else:
        severity_colors = {
            'critical': Colors.RED,
            'high': Colors.RED,
            'medium': Colors.YELLOW,
            'low': Colors.GREEN,
        }
        
        for i, v in enumerate(result.vulnerabilities, 1):
            sev_color = severity_colors.get(v.severity, Colors.END)
            print(f"\n  {i}. {sev_color}[{v.severity.upper()}]{Colors.END} {v.title}")
            print(f"     {v.description[:80]}...")
            print(f"     {Colors.CYAN}→ {v.recommendation[:60]}...{Colors.END}")
            if v.line_number:
                print(f"     Line: {v.line_number}")
    
    if result.warnings:
        print(f"\n{Colors.YELLOW}Warnings:{Colors.END}")
        for w in result.warnings:
            print(f"  • {w}")
    
    print(f"\n{'─'*50}\n")
    
    return 1 if result.vulnerabilities else 0


def cmd_chains(args):
    """Show supported chains"""
    print(f"\n{Colors.BOLD}Supported Blockchains{Colors.END}")
    print(f"{'─'*50}\n")
    
    chains_info = [
        ("Ethereum/EVM", "Solidity, Vyper", ".sol, .vy", "ethereum"),
        ("Solana", "Rust (Anchor)", ".rs", "solana"),
        ("Aptos", "Move", ".move", "aptos"),
        ("Sui", "Move", ".move", "sui"),
        ("StarkNet", "Cairo", ".cairo", "starknet"),
        ("Cosmos", "Rust (CosmWasm)", ".rs", "cosmos"),
        ("Polkadot", "Rust (Ink!)", ".rs", "polkadot"),
        ("NEAR", "Rust", ".rs", "near"),
    ]
    
    print(f"{'Chain':<15} {'Language':<20} {'Extensions':<12} {'Flag':<10}")
    print(f"{'─'*15} {'─'*20} {'─'*12} {'─'*10}")
    
    for chain, lang, ext, flag in chains_info:
        print(f"{chain:<15} {lang:<20} {ext:<12} --chain {flag}")
    
    print(f"""
{Colors.BOLD}Usage:{Colors.END}
  guardescan multichain program.rs             # Auto-detect chain
  guardescan multichain contract.sol           # Ethereum
  guardescan multichain program.rs --chain solana
  guardescan multichain module.move --chain aptos
  guardescan multichain contract.cairo --chain starknet
""")
    
    return 0


def cmd_defi(args):
    """Handle DeFi analysis command"""
    from pathlib import Path
    
    target = args.target
    
    print(f"\n{Colors.BOLD}DeFi Security Analysis{Colors.END}")
    print(f"{'─'*50}\n")
    
    try:
        code = Path(target).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"{Colors.RED}Error reading file: {e}{Colors.END}")
        return 1
    
    analyzer = DeFiAnalyzer()
    vulnerabilities = analyzer.analyze(code, target)
    
    if args.json:
        print(json.dumps([v.to_dict() for v in vulnerabilities], indent=2))
        return 0
    
    print(f"{Colors.BOLD}File:{Colors.END} {target}")
    print(f"{Colors.BOLD}DeFi Vulnerabilities:{Colors.END} {len(vulnerabilities)}\n")
    
    if not vulnerabilities:
        print(f"  {Colors.GREEN}✓ No DeFi-specific vulnerabilities detected!{Colors.END}")
    else:
        attack_icons = {
            'flash_loan': '⚡',
            'oracle_manipulation': '🔮',
            'sandwich': '🥪',
            'governance': '🗳️',
            'mev': '🤖',
            'economic': '💰',
            'liquidation': '💥',
            'reentrancy': '🔄',
        }
        
        for i, v in enumerate(vulnerabilities, 1):
            icon = attack_icons.get(v.attack_type.value, '⚠️')
            sev_color = {
                'critical': Colors.RED,
                'high': Colors.RED,
                'medium': Colors.YELLOW,
                'low': Colors.GREEN
            }.get(v.severity, Colors.END)
            
            print(f"  {i}. {icon} {sev_color}[{v.severity.upper()}]{Colors.END} {v.title}")
            print(f"     {Colors.HEADER}Attack Type:{Colors.END} {v.attack_type.value}")
            print(f"     {v.description}")
            print(f"     {Colors.YELLOW}Impact:{Colors.END} {v.potential_impact}")
            print(f"     {Colors.CYAN}→ {v.recommendation}{Colors.END}")
            print(f"     {Colors.HEADER}Risk Score:{Colors.END} {v.estimated_risk:.0%}")
            print()
    
    print(f"{'─'*50}\n")
    
    return 1 if vulnerabilities else 0


def cmd_ai(args):
    """Handle AI/ML-enhanced analysis command"""
    from pathlib import Path
    
    target = args.target
    
    print(f"\n{Colors.BOLD}AI-Enhanced Security Analysis{Colors.END}")
    print(f"{'─'*50}\n")
    
    try:
        code = Path(target).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"{Colors.RED}Error reading file: {e}{Colors.END}")
        return 1
    
    detector = MLVulnerabilityDetector()
    predictions = detector.predict(code, target)
    
    if args.json:
        result = [
            {
                'type': p.vulnerability_type,
                'confidence': p.confidence,
                'severity': p.severity,
                'explanation': p.explanation
            }
            for p in predictions
        ]
        print(json.dumps(result, indent=2))
        return 0
    
    print(f"{Colors.BOLD}File:{Colors.END} {target}")
    print(f"{Colors.BOLD}ML Predictions:{Colors.END} {len(predictions)}\n")
    
    if not predictions:
        print(f"  {Colors.GREEN}✓ ML analysis found no significant vulnerabilities!{Colors.END}")
    else:
        for i, p in enumerate(predictions, 1):
            sev_color = {
                'critical': Colors.RED,
                'high': Colors.RED,
                'medium': Colors.YELLOW,
                'low': Colors.GREEN
            }.get(p.severity, Colors.END)
            
            conf_color = Colors.RED if p.confidence > 0.7 else Colors.YELLOW if p.confidence > 0.5 else Colors.GREEN
            
            print(f"  {i}. {sev_color}[{p.severity.upper()}]{Colors.END} {p.vulnerability_type.replace('_', ' ').title()}")
            print(f"     {Colors.HEADER}Confidence:{Colors.END} {conf_color}{p.confidence:.0%}{Colors.END}")
            print(f"     {p.explanation}")
            print()
    
    print(f"{'─'*50}\n")
    
    return 1 if predictions else 0


def cmd_full(args):
    """Handle full advanced analysis command"""
    from pathlib import Path
    
    target = args.target
    
    print(f"\n{Colors.BOLD}Complete Advanced Security Analysis{Colors.END}")
    print(f"{'─'*60}\n")
    
    # First run the standard scan
    scanner = GuardeScan()
    
    try:
        code = Path(target).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"{Colors.RED}Error reading file: {e}{Colors.END}")
        return 1
    
    # Standard scan
    result = scanner.scan(target)
    
    # DeFi analysis
    defi_analyzer = DeFiAnalyzer()
    defi_vulns = defi_analyzer.analyze(code, target)
    
    # ML analysis
    ml_detector = MLVulnerabilityDetector()
    ml_preds = ml_detector.predict(code, target)
    
    if args.json:
        output = {
            'standard_scan': result.to_dict(),
            'defi_vulnerabilities': [v.to_dict() for v in defi_vulns],
            'ml_predictions': [
                {'type': p.vulnerability_type, 'confidence': p.confidence, 'severity': p.severity}
                for p in ml_preds
            ]
        }
        print(json.dumps(output, indent=2))
        return 0
    
    # Print summary header
    print(f"{Colors.BOLD}Analysis Summary{Colors.END}")
    print(f"{'─'*40}")
    print(f"  File: {target}")
    print(f"  Grade: {_grade_color(result.grade)}{result.grade.value}{Colors.END}")
    print(f"  Score: {result.score}/100")
    print()
    
    # Standard vulnerabilities
    print(f"{Colors.BOLD}Standard Vulnerabilities:{Colors.END} {len(result.vulnerabilities)}")
    for v in result.vulnerabilities[:5]:
        print(f"  • [{v.severity.value}] {v.title}")
    if len(result.vulnerabilities) > 5:
        print(f"  ... and {len(result.vulnerabilities) - 5} more")
    print()
    
    # DeFi vulnerabilities
    print(f"{Colors.BOLD}DeFi Attack Vectors:{Colors.END} {len(defi_vulns)}")
    for v in defi_vulns[:5]:
        print(f"  • [{v.severity}] {v.title} ({v.attack_type.value})")
    if len(defi_vulns) > 5:
        print(f"  ... and {len(defi_vulns) - 5} more")
    print()
    
    # ML predictions
    high_conf = [p for p in ml_preds if p.confidence >= 0.6]
    print(f"{Colors.BOLD}ML Predictions (high confidence):{Colors.END} {len(high_conf)}")
    for p in high_conf[:5]:
        print(f"  • [{p.severity}] {p.vulnerability_type} ({p.confidence:.0%})")
    print()
    
    # Overall risk assessment
    total_critical = sum(1 for v in result.vulnerabilities if v.severity.value == 'critical')
    total_critical += sum(1 for v in defi_vulns if v.severity == 'critical')
    total_critical += sum(1 for p in ml_preds if p.severity == 'critical' and p.confidence >= 0.7)
    
    total_high = sum(1 for v in result.vulnerabilities if v.severity.value == 'high')
    total_high += sum(1 for v in defi_vulns if v.severity == 'high')
    
    print(f"{'─'*40}")
    if total_critical > 0:
        print(f"{Colors.RED}⚠️  CRITICAL RISK - {total_critical} critical issues found{Colors.END}")
    elif total_high > 0:
        print(f"{Colors.YELLOW}⚠️  HIGH RISK - {total_high} high severity issues found{Colors.END}")
    elif result.vulnerabilities or defi_vulns:
        print(f"{Colors.YELLOW}⚠️  MODERATE RISK - Review recommended{Colors.END}")
    else:
        print(f"{Colors.GREEN}✓ LOW RISK - Contract appears secure{Colors.END}")
    
    print(f"{'─'*60}\n")
    
    return 1 if (result.vulnerabilities or defi_vulns) else 0


def _grade_color(grade):
    """Get color for grade"""
    if grade.value in ['A+', 'A', 'A-']:
        return Colors.GREEN
    elif grade.value in ['B+', 'B', 'B-']:
        return Colors.CYAN
    elif grade.value in ['C+', 'C', 'C-']:
        return Colors.YELLOW
    return Colors.RED


def cmd_benchmark(args):
    """Run benchmark against real-world exploits"""
    print(f"\n{Colors.BOLD}GuardeScan Accuracy Benchmark{Colors.END}")
    print(f"Testing against {len(REAL_WORLD_EXPLOITS)} real-world exploits")
    print(f"{'='*60}\n")
    
    benchmark = GuardeScanBenchmark()
    suite = benchmark.run_exploit_benchmarks(verbose=True)
    
    # Generate report
    if args.output:
        report = benchmark.generate_report(suite, args.output)
        print(f"\n{Colors.GREEN}Report saved to: {args.output}{Colors.END}")
    
    if args.json:
        print(json.dumps(suite.to_dict(), indent=2))
    
    # Print summary
    print(f"\n{Colors.BOLD}BENCHMARK SUMMARY{Colors.END}")
    print(f"{'─'*40}")
    
    # Color code the scores
    def score_color(score):
        if score >= 0.85:
            return Colors.GREEN
        elif score >= 0.70:
            return Colors.YELLOW
        return Colors.RED
    
    print(f"  Precision: {score_color(suite.overall_precision)}{suite.overall_precision:.1%}{Colors.END}")
    print(f"  Recall: {score_color(suite.overall_recall)}{suite.overall_recall:.1%}{Colors.END}")
    print(f"  F1 Score: {score_color(suite.overall_f1)}{suite.overall_f1:.1%}{Colors.END}")
    
    print(f"\n{Colors.BOLD}INDUSTRY COMPARISON{Colors.END}")
    print(f"{'─'*40}")
    print(f"  {'Tool':<15} {'Precision':<12} {'Recall':<12}")
    print(f"  {'─'*15} {'─'*12} {'─'*12}")
    print(f"  {'GuardeScan':<15} {suite.overall_precision:.0%}{'':>8} {suite.overall_recall:.0%}")
    print(f"  {'Slither':<15} {'~85%':>8} {'~75%':>8}")
    print(f"  {'Mythril':<15} {'~90%':>8} {'~60%':>8}")
    print(f"  {'Securify2':<15} {'~80%':>8} {'~70%':>8}")
    
    print(f"\n{Colors.HEADER}Note: Benchmark uses simplified exploit reproductions.{Colors.END}")
    print(f"{Colors.HEADER}Real-world validation requires testing on actual contracts.{Colors.END}\n")
    
    return 0


def cmd_compare(args):
    """Compare GuardeScan with other tools"""
    print(f"\n{Colors.BOLD}Tool Comparison: GuardeScan vs Others{Colors.END}")
    print(f"{'='*60}\n")
    
    result = compare_tools(args.target)
    
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    
    # Print GuardeScan results
    gs = result['guardescan']
    print(f"{Colors.BOLD}GuardeScan Results:{Colors.END}")
    print(f"  Vulnerabilities: {gs['vulnerabilities']}")
    print(f"  Time: {gs['time']:.2f}s")
    print(f"  Findings: {', '.join(gs['findings'][:5])}...")
    
    # Print Slither results
    sl = result['slither']
    print(f"\n{Colors.BOLD}Slither Results:{Colors.END}")
    if 'error' in sl:
        print(f"  {Colors.YELLOW}{sl['error']}{Colors.END}")
    else:
        print(f"  Vulnerabilities: {sl['vulnerabilities']}")
        print(f"  Time: {sl['time']:.2f}s")
        print(f"  Findings: {', '.join(sl['findings'][:5])}...")
    
    # Print comparison
    if 'comparison' in result and result['comparison']:
        comp = result['comparison']
        print(f"\n{Colors.BOLD}Comparison:{Colors.END}")
        print(f"  {comp['speed_comparison']}")
        diff = comp['difference']
        if diff > 0:
            print(f"  GuardeScan found {diff} more issues")
        elif diff < 0:
            print(f"  Slither found {-diff} more issues")
        else:
            print(f"  Both found same number of issues")
    
    print()
    return 0


def cmd_enhanced(args):
    """Handle enhanced multi-chain scan command"""
    scanner = EnhancedMultiChainScanner()
    
    target = args.target
    chain = EnhancedChain(args.chain) if args.chain else None
    
    print(f"\n{Colors.BOLD}Enhanced Multi-Chain Security Scanner v2.0{Colors.END}")
    print(f"{'─'*60}\n")
    
    result = scanner.scan(target, chain=chain)
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0
    
    # Chain color mapping
    chain_colors = {
        EnhancedChain.ETHEREUM: Colors.BLUE,
        EnhancedChain.SOLANA: Colors.CYAN,
        EnhancedChain.APTOS: Colors.GREEN,
        EnhancedChain.SUI: Colors.GREEN,
        EnhancedChain.STARKNET: Colors.YELLOW,
        EnhancedChain.COSMOS: Colors.HEADER,
    }
    chain_color = chain_colors.get(result.chain, Colors.END)
    
    # Print header
    print(f"{Colors.BOLD}Scan Results{Colors.END}")
    print(f"{'─'*40}")
    print(f"  Chain: {chain_color}{result.chain.value.upper()}{Colors.END}")
    print(f"  Language: {result.language}")
    print(f"  Contract: {result.contract_name}")
    print(f"  Lines of Code: {result.lines_of_code}")
    print(f"  Functions: {result.functions_analyzed}")
    print(f"  Scan Time: {result.scan_time:.2f}s")
    print(f"  Risk Score: {100 - result.risk_score:.0f}/100")
    
    # Severity summary
    print(f"\n{Colors.BOLD}Severity Summary{Colors.END}")
    print(f"{'─'*40}")
    
    sev_counts = {}
    for v in result.vulnerabilities:
        sev = v.severity.value
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
    
    for sev in ['critical', 'high', 'medium', 'low', 'info']:
        count = sev_counts.get(sev, 0)
        if sev == 'critical':
            color = Colors.RED
            icon = '🔴'
        elif sev == 'high':
            color = Colors.RED
            icon = '🟠'
        elif sev == 'medium':
            color = Colors.YELLOW
            icon = '🟡'
        elif sev == 'low':
            color = Colors.GREEN
            icon = '🟢'
        else:
            color = Colors.HEADER
            icon = '⚪'
        
        print(f"  {icon} {color}{sev.upper()}: {count}{Colors.END}")
    
    # Detailed findings
    print(f"\n{Colors.BOLD}Vulnerabilities ({len(result.vulnerabilities)}){Colors.END}")
    print(f"{'─'*40}")
    
    if not result.vulnerabilities:
        print(f"  {Colors.GREEN}✓ No vulnerabilities detected!{Colors.END}")
    else:
        for i, v in enumerate(result.vulnerabilities, 1):
            sev_color = {
                ChainSeverity.CRITICAL: Colors.RED,
                ChainSeverity.HIGH: Colors.RED,
                ChainSeverity.MEDIUM: Colors.YELLOW,
                ChainSeverity.LOW: Colors.GREEN,
                ChainSeverity.INFO: Colors.HEADER,
            }.get(v.severity, Colors.END)
            
            print(f"\n  {i}. {sev_color}[{v.severity.value.upper()}]{Colors.END} {v.title}")
            print(f"     {Colors.HEADER}ID:{Colors.END} {v.vuln_id}")
            if v.cwe_id:
                print(f"     {Colors.HEADER}CWE:{Colors.END} {v.cwe_id}")
            print(f"     {v.description}")
            print(f"     {Colors.CYAN}→ {v.recommendation}{Colors.END}")
            if v.line_number:
                print(f"     {Colors.HEADER}Line:{Colors.END} {v.line_number}")
            print(f"     {Colors.HEADER}Confidence:{Colors.END} {v.confidence:.0%}")
            
            if v.code_snippet and args.verbose:
                print(f"\n     {Colors.HEADER}Code:{Colors.END}")
                for line in v.code_snippet.split('\n'):
                    print(f"       {line}")
    
    # Info messages
    if result.info:
        print(f"\n{Colors.BOLD}Analysis Info{Colors.END}")
        print(f"{'─'*40}")
        for info in result.info:
            print(f"  ℹ️  {info}")
    
    print(f"\n{'─'*60}\n")
    
    # Exit code based on critical/high findings
    if result.critical_count > 0:
        return 2
    elif result.high_count > 0:
        return 1
    return 0


def cmd_report(args):
    """Handle report command"""
    scanner = GuardeScan()
    result = scanner.scan(args.target)
    
    base = Path(args.target).stem
    print(f"Generating reports for {result.contract_name}...")
    generate_all_reports(result, base)
    
    return 0


def cmd_interactive(args):
    """Handle interactive mode"""
    print_banner()
    
    print(f"""
Commands:
  {Colors.GREEN}scan <file>{Colors.END}     Scan a contract
  {Colors.GREEN}project{Colors.END}         Scan current directory  
  {Colors.GREEN}watch <dir>{Colors.END}     Watch for changes
  {Colors.GREEN}fix <file>{Colors.END}      Generate fixed version
  {Colors.GREEN}diff <f1> <f2>{Colors.END}  Compare contracts
  {Colors.GREEN}report <file>{Colors.END}   Generate all reports
  {Colors.GREEN}setup{Colors.END}           Check dependencies
  {Colors.GREEN}help{Colors.END}            Show commands
  {Colors.GREEN}exit{Colors.END}            Exit

""")
    
    scanner = GuardeScan()
    
    while True:
        try:
            cmd = input(f"{Colors.CYAN}guardescan>{Colors.END} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not cmd:
            continue
        
        parts = cmd.split()
        action = parts[0].lower()
        cmd_args = parts[1:]
        
        try:
            if action in ('exit', 'quit', 'q'):
                print("Goodbye!")
                break
            
            elif action == 'help':
                print("Commands: scan, project, watch, fix, diff, report, setup, exit")
            
            elif action == 'setup':
                cmd_setup(argparse.Namespace())
            
            elif action == 'scan':
                if not cmd_args:
                    print(f"{Colors.RED}Usage: scan <file.sol>{Colors.END}")
                    continue
                result = scanner.scan(cmd_args[0])
                print_result(result)
            
            elif action == 'project':
                results = scanner.scan_directory('.')
                print_summary(results)
            
            elif action == 'watch':
                target = cmd_args[0] if cmd_args else '.'
                ns = argparse.Namespace(target=target)
                cmd_watch(ns)
            
            elif action == 'fix':
                if not cmd_args:
                    print(f"{Colors.RED}Usage: fix <file.sol>{Colors.END}")
                    continue
                output = cmd_args[1] if len(cmd_args) > 1 else None
                ns = argparse.Namespace(input=cmd_args[0], output=output)
                cmd_fix(ns)
            
            elif action == 'diff':
                if len(cmd_args) < 2:
                    print(f"{Colors.RED}Usage: diff <file1.sol> <file2.sol>{Colors.END}")
                    continue
                ns = argparse.Namespace(file1=cmd_args[0], file2=cmd_args[1], json=False)
                cmd_diff(ns)
            
            elif action == 'report':
                if not cmd_args:
                    print(f"{Colors.RED}Usage: report <file.sol>{Colors.END}")
                    continue
                ns = argparse.Namespace(target=cmd_args[0])
                cmd_report(ns)
            
            elif os.path.exists(action):
                # Treat as file path
                result = scanner.scan(action)
                print_result(result)
            
            else:
                print(f"{Colors.RED}Unknown command: {action}{Colors.END}")
                print("Type 'help' for available commands.")
        
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.END}")
            if os.environ.get('DEBUG'):
                traceback.print_exc()
    
    return 0


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        prog='guardescan',
        description='GuardeScan - The World\'s Easiest Smart Contract Security Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  guardescan scan contract.sol          Scan a contract
  guardescan scan ./contracts           Scan directory
  guardescan scan contract.sol --all    Generate all reports
  guardescan watch ./contracts          Watch for changes
  guardescan fix contract.sol           Generate fixed version
  guardescan diff v1.sol v2.sol         Compare contracts
  guardescan project                    Scan current project
  guardescan setup                      Check dependencies
  guardescan                            Interactive mode
"""
    )
    
    parser.add_argument('--version', action='version', version=f'guardescan {__version__}')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a contract or directory')
    scan_parser.add_argument('target', help='Contract file or directory')
    scan_parser.add_argument('--json', action='store_true', help='Output as JSON')
    scan_parser.add_argument('--html', type=str, help='Generate HTML report')
    scan_parser.add_argument('--sarif', type=str, help='Generate SARIF report')
    scan_parser.add_argument('--markdown', type=str, help='Generate Markdown report')
    scan_parser.add_argument('--all-reports', '--all', action='store_true', help='Generate all reports')
    scan_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # watch command
    watch_parser = subparsers.add_parser('watch', help='Watch directory for changes')
    watch_parser.add_argument('target', nargs='?', default='.', help='Directory to watch')
    
    # project command
    project_parser = subparsers.add_parser('project', help='Scan entire project')
    project_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # fix command
    fix_parser = subparsers.add_parser('fix', help='Generate auto-fixed version')
    fix_parser.add_argument('input', help='Input contract')
    fix_parser.add_argument('output', nargs='?', help='Output file (default: input_fixed.sol)')
    
    # diff command
    diff_parser = subparsers.add_parser('diff', help='Compare two contracts')
    diff_parser.add_argument('file1', help='First contract')
    diff_parser.add_argument('file2', help='Second contract')
    diff_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # report command
    report_parser = subparsers.add_parser('report', help='Generate all reports')
    report_parser.add_argument('target', help='Contract file')
    
    # setup command
    setup_parser = subparsers.add_parser('setup', help='Check and setup dependencies')
    
    # multichain command
    multi_parser = subparsers.add_parser('multichain', aliases=['multi', 'mc'], 
                                         help='Scan contracts on any blockchain')
    multi_parser.add_argument('target', help='Contract file to scan')
    multi_parser.add_argument('--chain', type=str, choices=[
        'ethereum', 'solana', 'aptos', 'sui', 'starknet', 'cosmos', 'polkadot', 'near'
    ], help='Target blockchain (auto-detected if not specified)')
    multi_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # chains command
    chains_parser = subparsers.add_parser('chains', help='Show supported blockchains')
    
    # defi command
    defi_parser = subparsers.add_parser('defi', help='DeFi-specific vulnerability analysis')
    defi_parser.add_argument('target', help='Contract file to analyze')
    defi_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # ai command
    ai_parser = subparsers.add_parser('ai', aliases=['ml'], help='AI/ML-enhanced vulnerability detection')
    ai_parser.add_argument('target', help='Contract file to analyze')
    ai_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # full command
    full_parser = subparsers.add_parser('full', aliases=['complete', 'all'], 
                                        help='Complete analysis with all features')
    full_parser.add_argument('target', help='Contract file to analyze')
    full_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # enhanced command
    enhanced_parser = subparsers.add_parser('enhanced', aliases=['pro', 'e'], 
                                            help='Enhanced multi-chain scan (high accuracy)')
    enhanced_parser.add_argument('target', help='Contract file to scan')
    enhanced_parser.add_argument('--chain', type=str, choices=[
        'ethereum', 'solana', 'aptos', 'sui', 'starknet', 'cosmos', 'polkadot', 'near'
    ], help='Target blockchain (auto-detected if not specified)')
    enhanced_parser.add_argument('--json', action='store_true', help='Output as JSON')
    enhanced_parser.add_argument('-v', '--verbose', action='store_true', help='Show code snippets')
    
    # benchmark command
    bench_parser = subparsers.add_parser('benchmark', aliases=['bench'], 
                                         help='Run accuracy benchmark against real exploits')
    bench_parser.add_argument('--json', action='store_true', help='Output as JSON')
    bench_parser.add_argument('--output', '-o', type=str, help='Save report to file')
    
    # compare command
    compare_parser = subparsers.add_parser('compare', help='Compare with other tools (Slither, etc.)')
    compare_parser.add_argument('target', help='Contract file to compare')
    compare_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Disable colors if requested
    if args.no_color:
        Colors.disable()
    
    try:
        if args.command == 'scan':
            return cmd_scan(args)
        elif args.command == 'watch':
            return cmd_watch(args)
        elif args.command == 'project':
            return cmd_project(args)
        elif args.command == 'fix':
            return cmd_fix(args)
        elif args.command == 'diff':
            return cmd_diff(args)
        elif args.command == 'report':
            return cmd_report(args)
        elif args.command == 'setup':
            return cmd_setup(args)
        elif args.command in ('multichain', 'multi', 'mc'):
            return cmd_multichain(args)
        elif args.command == 'chains':
            return cmd_chains(args)
        elif args.command == 'defi':
            return cmd_defi(args)
        elif args.command in ('ai', 'ml'):
            return cmd_ai(args)
        elif args.command in ('full', 'complete', 'all'):
            return cmd_full(args)
        elif args.command in ('enhanced', 'pro', 'e'):
            return cmd_enhanced(args)
        elif args.command in ('benchmark', 'bench'):
            return cmd_benchmark(args)
        elif args.command == 'compare':
            return cmd_compare(args)
        else:
            # No command - interactive mode
            return cmd_interactive(args)
    
    except FileNotFoundError as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        return 1
    except KeyboardInterrupt:
        print("\nAborted.")
        return 1
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        if os.environ.get('DEBUG'):
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
