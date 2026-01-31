"""
Scorpius Scanner - The World's Most Powerful Smart Contract Security Scanner

Slither-powered core with DeFi attack detection, multi-chain support, and gas optimization.

Supports multiple blockchains:
- Ethereum/EVM (Solidity, Vyper) - Slither-powered
- Solana (Rust/Anchor)
- Move (Aptos/Sui)
- Cairo (StarkNet)
- CosmWasm (Cosmos)

Usage:
    from guardescan import GuardeScanEngine
    
    # Full scan with Slither + DeFi + Gas analysis
    engine = GuardeScanEngine()
    result = engine.scan("MyContract.sol")
    print(f"Score: {result.score}/100, Grade: {result.grade}")
    
    # Access all findings
    for vuln in result.all_vulnerabilities:
        print(f"[{vuln.severity}] {vuln.title}")
    
    # Multi-chain scan
    from guardescan import scan_multichain
    result = scan_multichain("program.rs")  # Auto-detects Solana
"""

__version__ = "5.0.0"
__author__ = "Scorpius Security"
__email__ = "security@scorpius.io"

from guardescan.core import (
    GuardeScan,
    ScanResult,
    Vulnerability,
    GasIssue,
    Severity,
    Grade,
)

from guardescan.scanner import scan, scan_file, scan_directory

from guardescan.chains import (
    MultiChainScanner,
    ChainScanResult,
    ChainVulnerability,
    Chain,
    scan_multichain,
    detect_chain,
)

from guardescan.chains_enhanced import (
    EnhancedMultiChainScanner,
    EnhancedSolanaAnalyzer,
    EnhancedMoveAnalyzer,
    EnhancedCairoAnalyzer,
    EnhancedCosmWasmAnalyzer,
    enhanced_scan,
    get_vulnerability_database,
    Severity as ChainSeverity,
)

from guardescan.advanced import (
    AdvancedScanner,
    DeFiAnalyzer,
    MLVulnerabilityDetector,
    BytecodeAnalyzer,
    DeFiVulnerability,
    MLPrediction,
    DeFiAttackType,
    analyze_defi,
    ml_scan,
    full_analysis,
)

# Import Slither-powered engine
try:
    from guardescan.slither_engine import (
        GuardeScanEngine,
        SlitherEngine,
        EnhancedPatternDetector,
        ScanResult as EngineScanResult,
    )
except ImportError:
    GuardeScanEngine = None
    SlitherEngine = None
    EnhancedPatternDetector = None
    EngineScanResult = None

__all__ = [
    # Core
    "GuardeScan",
    "ScanResult", 
    "Vulnerability",
    "GasIssue",
    "Severity",
    "Grade",
    # Scanner functions
    "scan",
    "scan_file",
    "scan_directory",
    # Multi-chain
    "MultiChainScanner",
    "ChainScanResult",
    "ChainVulnerability",
    "Chain",
    "scan_multichain",
    "detect_chain",
    # Enhanced Multi-chain
    "EnhancedMultiChainScanner",
    "EnhancedSolanaAnalyzer",
    "EnhancedMoveAnalyzer",
    "EnhancedCairoAnalyzer",
    "EnhancedCosmWasmAnalyzer",
    "enhanced_scan",
    "get_vulnerability_database",
    "ChainSeverity",
    # Advanced
    "AdvancedScanner",
    "DeFiAnalyzer",
    "MLVulnerabilityDetector",
    "BytecodeAnalyzer",
    "DeFiVulnerability",
    "MLPrediction",
    "DeFiAttackType",
    "analyze_defi",
    "ml_scan",
    "full_analysis",
    # Slither-powered engine
    "GuardeScanEngine",
    "SlitherEngine",
    "EnhancedPatternDetector",
    "EngineScanResult",
    # Version
    "__version__",
]
