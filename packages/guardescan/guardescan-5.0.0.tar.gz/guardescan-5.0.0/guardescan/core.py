"""
GuardeScan Core Module
Data structures and main scanner class
"""

import sys
import os
import io
import re
import json
import time
import hashlib
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("guardescan")


# ==============================================================================
# ENUMS
# ==============================================================================

class Severity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    
    def __lt__(self, other):
        order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        return order[self] < order[other]


class Grade(Enum):
    """Security grade levels (A+ to F)"""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D_PLUS = "D+"
    D = "D"
    F = "F"


# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class Vulnerability:
    """Represents a detected vulnerability"""
    vuln_id: str
    title: str
    severity: Severity
    confidence: float
    description: str
    recommendation: str
    detected_by: List[str]
    line_number: Optional[int] = None
    end_line: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    auto_fix: Optional[str] = None
    cwe_id: Optional[str] = None
    swc_id: Optional[str] = None
    references: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'vuln_id': self.vuln_id,
            'title': self.title,
            'severity': self.severity.value,
            'confidence': self.confidence,
            'description': self.description,
            'recommendation': self.recommendation,
            'detected_by': self.detected_by,
            'line_number': self.line_number,
            'end_line': self.end_line,
            'column': self.column,
            'code_snippet': self.code_snippet,
            'auto_fix': self.auto_fix,
            'cwe_id': self.cwe_id,
            'swc_id': self.swc_id,
            'references': self.references
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Vulnerability':
        """Create from dictionary"""
        data = data.copy()
        data['severity'] = Severity(data['severity'])
        return cls(**data)


@dataclass
class GasIssue:
    """Represents a gas optimization opportunity"""
    issue_type: str
    description: str
    line_number: Optional[int]
    savings_percent: int
    recommendation: str
    auto_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScanResult:
    """Complete scan result"""
    contract_path: str
    contract_name: str
    scan_time: float
    vulnerabilities: List[Vulnerability]
    gas_issues: List[GasIssue]
    grade: Grade
    score: float
    risk_rating: str
    solidity_version: Optional[str] = None
    contract_size: Optional[int] = None
    function_count: Optional[int] = None
    scanners_used: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'contract_path': self.contract_path,
            'contract_name': self.contract_name,
            'scan_time': self.scan_time,
            'vulnerabilities': [v.to_dict() for v in self.vulnerabilities],
            'gas_issues': [g.to_dict() for g in self.gas_issues],
            'grade': self.grade.value,
            'score': self.score,
            'risk_rating': self.risk_rating,
            'solidity_version': self.solidity_version,
            'contract_size': self.contract_size,
            'function_count': self.function_count,
            'scanners_used': self.scanners_used,
            'errors': self.errors,
            'warnings': self.warnings,
            'generated_at': datetime.now().isoformat(),
            'version': '3.0.0'
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @property
    def is_safe(self) -> bool:
        """Check if contract is considered safe"""
        return len(self.vulnerabilities) == 0
    
    @property
    def has_critical(self) -> bool:
        """Check if any critical vulnerabilities exist"""
        return any(v.severity == Severity.CRITICAL for v in self.vulnerabilities)
    
    @property
    def has_high(self) -> bool:
        """Check if any high severity vulnerabilities exist"""
        return any(v.severity == Severity.HIGH for v in self.vulnerabilities)
    
    def get_by_severity(self, severity: Severity) -> List[Vulnerability]:
        """Get vulnerabilities filtered by severity"""
        return [v for v in self.vulnerabilities if v.severity == severity]
    
    def summary(self) -> str:
        """Get a brief summary"""
        return (
            f"{self.contract_name}: {self.grade.value} ({self.score:.1f}/100) - "
            f"{len(self.vulnerabilities)} vulnerabilities, {self.risk_rating} risk"
        )


# ==============================================================================
# VULNERABILITY DATABASE
# ==============================================================================

VULNERABILITY_DATABASE = {
    'reentrancy': {
        'title': 'Reentrancy Vulnerability',
        'severity': Severity.CRITICAL,
        'cwe': 'CWE-841',
        'swc': 'SWC-107',
        'description': 'The contract is vulnerable to reentrancy attacks where an external call can re-enter the contract before state changes are complete, potentially allowing attackers to drain funds.',
        'recommendation': 'Use the checks-effects-interactions pattern: update state variables before making external calls. Consider using OpenZeppelin\'s ReentrancyGuard modifier.',
        'references': [
            'https://swcregistry.io/docs/SWC-107',
            'https://consensys.github.io/smart-contract-best-practices/attacks/reentrancy/',
        ]
    },
    'access-control': {
        'title': 'Access Control Vulnerability',
        'severity': Severity.HIGH,
        'cwe': 'CWE-284',
        'swc': 'SWC-105',
        'description': 'Critical functions lack proper access control, allowing unauthorized users to execute privileged operations that should be restricted.',
        'recommendation': 'Implement proper access control using modifiers like onlyOwner or role-based access control (RBAC). Consider using OpenZeppelin\'s AccessControl or Ownable contracts.',
        'references': [
            'https://swcregistry.io/docs/SWC-105',
            'https://docs.openzeppelin.com/contracts/4.x/access-control'
        ]
    },
    'tx-origin': {
        'title': 'Dangerous tx.origin Usage',
        'severity': Severity.MEDIUM,
        'cwe': 'CWE-477',
        'swc': 'SWC-115',
        'description': 'Using tx.origin for authorization is dangerous as it can be exploited via phishing attacks where a malicious contract tricks a user into calling it.',
        'recommendation': 'Replace tx.origin with msg.sender for authentication checks. tx.origin should only be used for logging or when you specifically need the original transaction sender.',
        'references': ['https://swcregistry.io/docs/SWC-115']
    },
    'timestamp': {
        'title': 'Block Timestamp Dependence',
        'severity': Severity.LOW,
        'cwe': 'CWE-829',
        'swc': 'SWC-116',
        'description': 'The contract relies on block.timestamp which can be manipulated by miners within approximately a 15-second window.',
        'recommendation': 'Avoid using block.timestamp for critical logic like random number generation or time-sensitive conditions. If timestamp is needed, ensure the 15-second variance is acceptable for your use case.',
        'references': ['https://swcregistry.io/docs/SWC-116']
    },
    'selfdestruct': {
        'title': 'Unprotected Selfdestruct',
        'severity': Severity.CRITICAL,
        'cwe': 'CWE-284',
        'swc': 'SWC-106',
        'description': 'The contract contains a selfdestruct (or suicide) function that may be called by unauthorized users, destroying the contract and sending its balance to an attacker.',
        'recommendation': 'Remove selfdestruct if not absolutely needed. If required, protect it with strict access controls, consider a timelock, and require multiple signatures.',
        'references': ['https://swcregistry.io/docs/SWC-106']
    },
    'unchecked-call': {
        'title': 'Unchecked External Call',
        'severity': Severity.MEDIUM,
        'cwe': 'CWE-252',
        'swc': 'SWC-104',
        'description': 'The return value of a low-level call (call, delegatecall, staticcall) is not checked, which may lead to silent failures and unexpected behavior.',
        'recommendation': 'Always check the return value of low-level calls using require(success, "Call failed") or appropriate error handling.',
        'references': ['https://swcregistry.io/docs/SWC-104']
    },
    'delegatecall': {
        'title': 'Dangerous Delegatecall',
        'severity': Severity.HIGH,
        'cwe': 'CWE-829',
        'swc': 'SWC-112',
        'description': 'Using delegatecall with untrusted contracts can lead to storage corruption or complete contract takeover, as the called contract executes in the context of the calling contract.',
        'recommendation': 'Only use delegatecall with trusted, audited contracts. Consider using a well-tested proxy pattern with proper storage layout. Never delegatecall to user-supplied addresses.',
        'references': ['https://swcregistry.io/docs/SWC-112']
    },
    'integer-overflow': {
        'title': 'Integer Overflow/Underflow',
        'severity': Severity.HIGH,
        'cwe': 'CWE-190',
        'swc': 'SWC-101',
        'description': 'Arithmetic operations may overflow or underflow, leading to unexpected values that can be exploited.',
        'recommendation': 'Use Solidity 0.8.0+ which has built-in overflow checks, or use OpenZeppelin\'s SafeMath library for earlier versions.',
        'references': ['https://swcregistry.io/docs/SWC-101']
    },
    'uninitialized-storage': {
        'title': 'Uninitialized Storage Pointer',
        'severity': Severity.HIGH,
        'cwe': 'CWE-457',
        'swc': 'SWC-109',
        'description': 'Uninitialized storage pointers can point to unexpected storage locations, leading to state corruption.',
        'recommendation': 'Always initialize storage pointers explicitly. Use memory keyword for local variables that don\'t need to persist.',
        'references': ['https://swcregistry.io/docs/SWC-109']
    },
    'floating-pragma': {
        'title': 'Floating Pragma',
        'severity': Severity.INFO,
        'cwe': None,
        'swc': 'SWC-103',
        'description': 'Using a floating pragma (^) allows the contract to be compiled with different compiler versions, which may introduce bugs.',
        'recommendation': 'Lock the pragma to a specific version (e.g., pragma solidity 0.8.20;) for production deployments.',
        'references': ['https://swcregistry.io/docs/SWC-103']
    },
    'arbitrary-send': {
        'title': 'Arbitrary ETH Transfer',
        'severity': Severity.HIGH,
        'cwe': 'CWE-284',
        'swc': 'SWC-105',
        'description': 'The contract allows sending ETH to arbitrary addresses without proper validation, which could allow attackers to drain funds.',
        'recommendation': 'Validate destination addresses against a whitelist or implement proper access controls on fund transfer functions.',
        'references': ['https://swcregistry.io/docs/SWC-105']
    },
    'dos-gas': {
        'title': 'Denial of Service (Gas Limit)',
        'severity': Severity.MEDIUM,
        'cwe': 'CWE-400',
        'swc': 'SWC-128',
        'description': 'The function may run out of gas when processing large arrays or loops, making it unusable.',
        'recommendation': 'Implement pagination or batch processing for large data sets. Avoid unbounded loops that depend on storage arrays.',
        'references': ['https://swcregistry.io/docs/SWC-128']
    }
}


# ==============================================================================
# BASE SCANNER CLASS
# ==============================================================================

class BaseScanner(ABC):
    """Abstract base class for scanners"""
    
    name: str = "BaseScanner"
    version: str = "1.0.0"
    
    @abstractmethod
    def scan(self, contract_path: str, code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scan a contract and return findings.
        
        Args:
            contract_path: Path to the contract file
            code: Optional pre-loaded code
            
        Returns:
            List of finding dictionaries
        """
        pass
    
    def is_available(self) -> bool:
        """Check if scanner is available/installed"""
        return True


# ==============================================================================
# SCANNERS
# ==============================================================================

class SlitherScanner(BaseScanner):
    """Slither integration - industry standard static analysis"""
    
    name = "Slither"
    version = "0.10.0"
    
    def is_available(self) -> bool:
        """Check if Slither is installed"""
        try:
            result = subprocess.run(
                ['slither', '--version'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def scan(self, contract_path: str, code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Run Slither analysis"""
        findings = []
        
        if not self.is_available():
            logger.debug("Slither not available, skipping")
            return findings
        
        try:
            # Run Slither with JSON output
            result = subprocess.run(
                ['slither', contract_path, '--json', '-'],
                capture_output=True,
                text=True,
                timeout=120,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.stdout:
                try:
                    # Find JSON in output (Slither may print warnings before JSON)
                    stdout = result.stdout
                    json_start = stdout.find('{')
                    if json_start >= 0:
                        data = json.loads(stdout[json_start:])
                        
                        if 'results' in data and 'detectors' in data['results']:
                            for detector in data['results']['detectors']:
                                impact = detector.get('impact', '').lower()
                                confidence = detector.get('confidence', '').lower()
                                
                                # Only report high/medium impact issues
                                if impact in ['high', 'medium', 'critical']:
                                    # Get line numbers from elements
                                    line_num = None
                                    for elem in detector.get('elements', []):
                                        if 'source_mapping' in elem:
                                            lines = elem['source_mapping'].get('lines', [])
                                            if lines:
                                                line_num = lines[0]
                                                break
                                    
                                    findings.append({
                                        'type': detector.get('check', 'unknown'),
                                        'description': detector.get('description', ''),
                                        'severity': impact,
                                        'confidence': 0.95 if confidence == 'high' else 0.75,
                                        'line': line_num,
                                        'source': 'Slither'
                                    })
                                    
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse Slither JSON: {e}")
                    
        except subprocess.TimeoutExpired:
            logger.warning("Slither scan timed out")
        except FileNotFoundError:
            logger.debug("Slither not found")
        except Exception as e:
            logger.debug(f"Slither error: {e}")
        
        return findings


class PatternScanner(BaseScanner):
    """Fast pattern-based vulnerability scanner"""
    
    name = "PatternScanner"
    version = "3.0.0"
    
    # Vulnerability patterns (regex, description)
    PATTERNS = {
        'reentrancy': [
            (r'\.call\{.*value.*\}\s*\([^)]*\)', 'External call with value'),
            (r'\.call\.value\s*\(', 'Legacy call.value pattern'),
            (r'(\.transfer\(|\.send\().*\n.*balance', 'Transfer/send before state update'),
        ],
        'tx-origin': [
            (r'\btx\.origin\b', 'tx.origin usage'),
        ],
        'timestamp': [
            (r'\bblock\.timestamp\b', 'block.timestamp usage'),
            (r'\bnow\b\s*[<>=!]', 'now keyword for comparison'),
        ],
        'selfdestruct': [
            (r'\bselfdestruct\s*\(', 'selfdestruct call'),
            (r'\bsuicide\s*\(', 'suicide (deprecated selfdestruct)'),
        ],
        'delegatecall': [
            (r'\.delegatecall\s*\(', 'delegatecall usage'),
        ],
        'unchecked-call': [
            (r'\.call\{[^}]*\}\s*\([^)]*\)\s*;(?!\s*(require|if|bool))', 'Unchecked call return'),
        ],
        'floating-pragma': [
            (r'pragma\s+solidity\s*\^', 'Floating pragma version'),
        ],
        'arbitrary-send': [
            (r'\.call\{value:\s*\w+\}\s*\(\s*""\s*\)', 'Arbitrary ETH send'),
        ],
        'dos-gas': [
            (r'for\s*\([^)]*\.length', 'Loop using storage array length'),
        ]
    }
    
    def scan(self, contract_path: str, code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scan using regex patterns"""
        findings = []
        
        # Load code if not provided
        if code is None:
            try:
                with open(contract_path, 'r', encoding='utf-8', errors='replace') as f:
                    code = f.read()
            except Exception as e:
                logger.error(f"Cannot read file: {e}")
                return findings
        
        lines = code.split('\n')
        
        for vuln_type, patterns in self.PATTERNS.items():
            found = False
            for pattern, desc in patterns:
                if found:
                    break
                    
                for i, line in enumerate(lines, 1):
                    # Skip comments
                    stripped = line.strip()
                    if stripped.startswith('//') or stripped.startswith('*'):
                        continue
                    
                    if re.search(pattern, line, re.IGNORECASE):
                        vuln_info = VULNERABILITY_DATABASE.get(vuln_type, {})
                        findings.append({
                            'type': vuln_type,
                            'description': desc,
                            'line': i,
                            'severity': vuln_info.get('severity', Severity.MEDIUM).value,
                            'confidence': 0.70,
                            'source': 'PatternScanner'
                        })
                        found = True
                        break
        
        return findings


class AccessControlScanner(BaseScanner):
    """Scanner for access control vulnerabilities"""
    
    name = "AccessControlScanner"
    version = "3.0.0"
    
    # Safe function names that don't need access control
    SAFE_FUNCTIONS = {
        'constructor', 'receive', 'fallback',
        'balanceOf', 'totalSupply', 'name', 'symbol', 'decimals',
        'allowance', 'owner', 'paused', 'getOwner',
        'supportsInterface', 'tokenURI', 'baseURI',
        # View/pure functions are generally safe
    }
    
    def scan(self, contract_path: str, code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scan for access control issues"""
        findings = []
        
        if code is None:
            try:
                with open(contract_path, 'r', encoding='utf-8', errors='replace') as f:
                    code = f.read()
            except Exception as e:
                logger.error(f"Cannot read file: {e}")
                return findings
        
        lines = code.split('\n')
        
        # Pattern for function definitions
        func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*(public|external)(?!\s+view)(?!\s+pure)'
        modifier_pattern = r'(onlyOwner|onlyAdmin|onlyRole|require\s*\(\s*msg\.sender|require\s*\(\s*_msgSender)'
        
        for i, line in enumerate(lines, 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('*'):
                continue
            
            match = re.search(func_pattern, line)
            if match:
                func_name = match.group(1)
                
                # Skip safe functions
                if func_name.lower() in {f.lower() for f in self.SAFE_FUNCTIONS}:
                    continue
                
                # Skip if it starts with underscore (internal convention)
                if func_name.startswith('_'):
                    continue
                
                # Check surrounding context (5 lines before and 10 after)
                context_start = max(0, i - 5)
                context_end = min(len(lines), i + 10)
                context = '\n'.join(lines[context_start:context_end])
                
                # Check if access control exists
                if not re.search(modifier_pattern, context, re.IGNORECASE):
                    findings.append({
                        'type': 'access-control',
                        'description': f"Function '{func_name}' lacks access control",
                        'line': i,
                        'function': func_name,
                        'severity': 'high',
                        'confidence': 0.70,
                        'source': 'AccessControlScanner'
                    })
        
        return findings


class GasAnalyzer(BaseScanner):
    """Analyzer for gas optimization opportunities"""
    
    name = "GasAnalyzer"
    version = "3.0.0"
    
    PATTERNS = [
        (r'\.length\s*[;><=\)]', 'array-length', 'Cache array length in local variable', 10),
        (r'storage\s+\w+\s*=', 'storage-var', 'Cache storage variable in memory', 20),
        (r'\+\+\w+|\w+\+\+', 'increment', 'Use ++i instead of i++ (minor)', 3),
        (r'public\s+\w+\s*;', 'public-var', 'Public creates getter, use private if not needed', 5),
        (r'require\([^,]+,\s*"[^"]{32,}"', 'long-error', 'Long error strings cost gas', 5),
        (r'string\s+public', 'string-storage', 'String storage is expensive', 10),
        (r'>\s*0\b', 'zero-check', 'Use != 0 instead of > 0 for uints', 3),
    ]
    
    def scan(self, contract_path: str, code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Analyze gas optimization opportunities"""
        findings = []
        
        if code is None:
            try:
                with open(contract_path, 'r', encoding='utf-8', errors='replace') as f:
                    code = f.read()
            except Exception:
                return findings
        
        lines = code.split('\n')
        
        for pattern, issue_type, desc, savings in self.PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    findings.append({
                        'type': issue_type,
                        'description': desc,
                        'line': i,
                        'savings': savings,
                        'source': 'GasAnalyzer'
                    })
        
        return findings


# ==============================================================================
# MAIN GUARDESCAN CLASS
# ==============================================================================

class GuardeScan:
    """
    Main scanner class that orchestrates all scanning operations.
    
    Usage:
        scanner = GuardeScan()
        result = scanner.scan("path/to/contract.sol")
        print(result.grade, result.score)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize GuardeScan.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.cache: Dict[str, ScanResult] = {}
        
        # Initialize scanners
        self.scanners: List[BaseScanner] = [
            SlitherScanner(),
            PatternScanner(),
            AccessControlScanner(),
        ]
        
        self.gas_analyzer = GasAnalyzer()
    
    def scan(
        self,
        contract_path: str,
        use_cache: bool = True,
        scanners: Optional[List[str]] = None
    ) -> ScanResult:
        """
        Scan a contract file.
        
        Args:
            contract_path: Path to the Solidity contract
            use_cache: Whether to use cached results
            scanners: Optional list of scanner names to use
            
        Returns:
            ScanResult object with findings
            
        Raises:
            FileNotFoundError: If contract file doesn't exist
            ValueError: If file cannot be read
        """
        start_time = time.time()
        errors: List[str] = []
        warnings: List[str] = []
        
        # Validate path
        path = Path(contract_path)
        if not path.exists():
            raise FileNotFoundError(f"Contract not found: {contract_path}")
        
        if not path.suffix == '.sol':
            warnings.append(f"File doesn't have .sol extension: {path.name}")
        
        # Check cache
        file_hash = self._get_file_hash(contract_path)
        if use_cache and file_hash in self.cache:
            cached = self.cache[file_hash]
            logger.debug(f"Using cached result for {contract_path}")
            return cached
        
        # Read contract
        try:
            code = path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            raise ValueError(f"Cannot read contract: {e}")
        
        # Extract metadata
        contract_name = self._extract_contract_name(code, contract_path)
        solidity_version = self._extract_solidity_version(code)
        function_count = len(re.findall(r'\bfunction\s+\w+', code))
        
        # Determine which scanners to use
        active_scanners = self.scanners
        if scanners:
            active_scanners = [s for s in self.scanners if s.name in scanners]
        
        # Run all scanners
        all_findings: List[Dict[str, Any]] = []
        scanners_used: List[str] = []
        
        for scanner in active_scanners:
            try:
                if scanner.is_available():
                    findings = scanner.scan(contract_path, code)
                    all_findings.extend(findings)
                    scanners_used.append(scanner.name)
                    logger.debug(f"{scanner.name}: {len(findings)} findings")
                else:
                    warnings.append(f"Scanner {scanner.name} not available")
            except Exception as e:
                errors.append(f"Scanner {scanner.name} error: {str(e)}")
                logger.warning(f"Scanner {scanner.name} failed: {e}")
        
        # Run gas analyzer
        gas_findings = []
        try:
            gas_findings = self.gas_analyzer.scan(contract_path, code)
        except Exception as e:
            errors.append(f"Gas analyzer error: {str(e)}")
        
        # Merge and deduplicate findings
        vulnerabilities = self._merge_findings(all_findings, code)
        gas_issues = self._process_gas_issues(gas_findings)
        
        # Calculate score and grade
        score, grade = self._calculate_score(vulnerabilities)
        risk_rating = self._calculate_risk(vulnerabilities)
        
        # Create result
        result = ScanResult(
            contract_path=contract_path,
            contract_name=contract_name,
            scan_time=time.time() - start_time,
            vulnerabilities=vulnerabilities,
            gas_issues=gas_issues,
            grade=grade,
            score=score,
            risk_rating=risk_rating,
            solidity_version=solidity_version,
            contract_size=len(code.encode('utf-8')),
            function_count=function_count,
            scanners_used=scanners_used,
            errors=errors,
            warnings=warnings
        )
        
        # Cache result
        self.cache[file_hash] = result
        
        return result
    
    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
        exclude: Optional[List[str]] = None
    ) -> List[ScanResult]:
        """
        Scan all Solidity files in a directory.
        
        Args:
            directory: Directory path
            recursive: Whether to scan subdirectories
            exclude: Patterns to exclude
            
        Returns:
            List of ScanResult objects
        """
        results = []
        exclude = exclude or ['node_modules', 'lib', '.git', 'test']
        
        dir_path = Path(directory)
        pattern = '**/*.sol' if recursive else '*.sol'
        
        for sol_file in dir_path.glob(pattern):
            # Skip excluded directories
            if any(excl in str(sol_file) for excl in exclude):
                continue
            
            try:
                result = self.scan(str(sol_file))
                results.append(result)
            except Exception as e:
                logger.error(f"Error scanning {sol_file}: {e}")
        
        return results
    
    def _get_file_hash(self, path: str) -> str:
        """Get hash of file contents for caching"""
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _extract_contract_name(self, code: str, path: str) -> str:
        """Extract contract name from code"""
        match = re.search(r'\bcontract\s+(\w+)', code)
        if match:
            return match.group(1)
        return Path(path).stem
    
    def _extract_solidity_version(self, code: str) -> Optional[str]:
        """Extract Solidity version from pragma"""
        match = re.search(r'pragma\s+solidity\s+([^;]+)', code)
        if match:
            return match.group(1).strip()
        return None
    
    def _normalize_vuln_type(self, vuln_type: str) -> str:
        """Normalize vulnerability type names"""
        mapping = {
            'reentrancy-eth': 'reentrancy',
            'reentrancy-no-eth': 'reentrancy',
            'reentrancy-benign': 'reentrancy',
            'arbitrary-send-eth': 'arbitrary-send',
            'controlled-delegatecall': 'delegatecall',
            'missing-zero-check': 'access-control',
            'unprotected-upgrade': 'access-control',
            'unchecked-return': 'unchecked-call',
            'selfdestruct': 'selfdestruct',
        }
        normalized = vuln_type.lower().replace('_', '-').replace(' ', '-')
        return mapping.get(normalized, normalized)
    
    def _merge_findings(
        self,
        findings: List[Dict[str, Any]],
        code: str
    ) -> List[Vulnerability]:
        """Merge and deduplicate findings from all scanners"""
        # Group by normalized type
        grouped: Dict[str, List[Dict]] = {}
        for f in findings:
            vuln_type = self._normalize_vuln_type(f.get('type', 'unknown'))
            if vuln_type not in grouped:
                grouped[vuln_type] = []
            grouped[vuln_type].append(f)
        
        vulnerabilities = []
        
        for vuln_type, type_findings in grouped.items():
            # Get unique sources
            sources = list(set(f.get('source', 'Unknown') for f in type_findings))
            
            # Calculate confidence based on consensus
            if 'Slither' in sources:
                confidence = 0.95
            elif len(sources) >= 2:
                confidence = 0.85
            else:
                confidence = 0.70
            
            # Get vulnerability info from database
            vuln_info = VULNERABILITY_DATABASE.get(vuln_type, {})
            
            # Get line number (prefer first non-None)
            line_num = None
            for f in type_findings:
                if f.get('line'):
                    line_num = f['line']
                    break
            
            # Get code snippet
            code_snippet = None
            if line_num:
                lines = code.split('\n')
                start = max(0, line_num - 2)
                end = min(len(lines), line_num + 2)
                code_snippet = '\n'.join(lines[start:end])
            
            vulnerability = Vulnerability(
                vuln_id=vuln_type,
                title=vuln_info.get('title', vuln_type.replace('-', ' ').title()),
                severity=vuln_info.get('severity', Severity.MEDIUM),
                confidence=confidence,
                description=vuln_info.get('description', f'Potential {vuln_type} vulnerability detected.'),
                recommendation=vuln_info.get('recommendation', 'Review and fix the identified issue.'),
                detected_by=sources,
                line_number=line_num,
                code_snippet=code_snippet,
                cwe_id=vuln_info.get('cwe'),
                swc_id=vuln_info.get('swc'),
                references=vuln_info.get('references', [])
            )
            
            vulnerabilities.append(vulnerability)
        
        # Sort by severity
        vulnerabilities.sort(key=lambda v: v.severity)
        
        return vulnerabilities
    
    def _process_gas_issues(self, findings: List[Dict[str, Any]]) -> List[GasIssue]:
        """Process gas optimization findings"""
        issues = []
        for f in findings:
            issues.append(GasIssue(
                issue_type=f.get('type', 'unknown'),
                description=f.get('description', ''),
                line_number=f.get('line'),
                savings_percent=f.get('savings', 5),
                recommendation=f.get('description', '')
            ))
        return issues
    
    def _calculate_score(self, vulnerabilities: List[Vulnerability]) -> Tuple[float, Grade]:
        """Calculate security score and grade"""
        if not vulnerabilities:
            return 100.0, Grade.A_PLUS
        
        # Deduction weights
        deductions = {
            Severity.CRITICAL: 30,
            Severity.HIGH: 20,
            Severity.MEDIUM: 10,
            Severity.LOW: 5,
            Severity.INFO: 1
        }
        
        total_deduction = sum(
            deductions.get(v.severity, 10) * v.confidence
            for v in vulnerabilities
        )
        
        score = max(0, min(100, 100 - total_deduction))
        
        # Determine grade
        if score >= 97:
            grade = Grade.A_PLUS
        elif score >= 93:
            grade = Grade.A
        elif score >= 90:
            grade = Grade.B_PLUS
        elif score >= 87:
            grade = Grade.B
        elif score >= 83:
            grade = Grade.C_PLUS
        elif score >= 80:
            grade = Grade.C
        elif score >= 77:
            grade = Grade.D_PLUS
        elif score >= 70:
            grade = Grade.D
        else:
            grade = Grade.F
        
        return score, grade
    
    def _calculate_risk(self, vulnerabilities: List[Vulnerability]) -> str:
        """Calculate risk rating"""
        if not vulnerabilities:
            return "SAFE"
        
        if any(v.severity == Severity.CRITICAL for v in vulnerabilities):
            return "CRITICAL"
        if any(v.severity == Severity.HIGH for v in vulnerabilities):
            return "HIGH"
        if any(v.severity == Severity.MEDIUM for v in vulnerabilities):
            return "MEDIUM"
        return "LOW"
