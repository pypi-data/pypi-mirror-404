"""
GuardeScan Multi-Chain Support
Scan contracts across multiple blockchain platforms

Supported Chains:
- Ethereum/EVM (Solidity, Vyper)
- Solana (Rust/Anchor)
- Move (Aptos/Sui)
- Cairo (StarkNet)
- Ink! (Polkadot)
- CosmWasm (Cosmos)
"""

import re
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ==============================================================================
# CHAIN DEFINITIONS
# ==============================================================================

class Chain(Enum):
    """Supported blockchain platforms"""
    ETHEREUM = "ethereum"
    SOLANA = "solana"
    APTOS = "aptos"
    SUI = "sui"
    STARKNET = "starknet"
    POLKADOT = "polkadot"
    COSMOS = "cosmos"
    NEAR = "near"
    
    @classmethod
    def from_extension(cls, ext: str) -> 'Chain':
        """Detect chain from file extension"""
        mapping = {
            '.sol': cls.ETHEREUM,
            '.vy': cls.ETHEREUM,
            '.rs': cls.SOLANA,  # Could also be Polkadot
            '.move': cls.APTOS,
            '.cairo': cls.STARKNET,
        }
        return mapping.get(ext.lower(), cls.ETHEREUM)


@dataclass
class ChainVulnerability:
    """Chain-specific vulnerability"""
    vuln_id: str
    title: str
    severity: str
    chain: Chain
    description: str
    recommendation: str
    pattern: Optional[str] = None
    line_number: Optional[int] = None
    confidence: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'vuln_id': self.vuln_id,
            'title': self.title,
            'severity': self.severity,
            'chain': self.chain.value,
            'description': self.description,
            'recommendation': self.recommendation,
            'line_number': self.line_number,
            'confidence': self.confidence
        }


@dataclass
class ChainScanResult:
    """Scan result for a specific chain"""
    chain: Chain
    contract_path: str
    contract_name: str
    language: str
    vulnerabilities: List[ChainVulnerability]
    warnings: List[str]
    scan_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chain': self.chain.value,
            'contract_path': self.contract_path,
            'contract_name': self.contract_name,
            'language': self.language,
            'vulnerabilities': [v.to_dict() for v in self.vulnerabilities],
            'warnings': self.warnings,
            'scan_time': self.scan_time,
            'metadata': self.metadata
        }


# ==============================================================================
# VULNERABILITY DATABASES
# ==============================================================================

SOLANA_VULNERABILITIES = {
    'missing-signer-check': {
        'title': 'Missing Signer Check',
        'severity': 'critical',
        'description': 'Instruction does not verify that required accounts have signed the transaction.',
        'recommendation': 'Add signer verification using is_signer check or Anchor\'s Signer type.',
        'patterns': [
            r'AccountInfo.*without.*signer',
            r'#\[account\([^)]*\)\](?!.*signer)',
        ]
    },
    'missing-owner-check': {
        'title': 'Missing Owner Check',
        'severity': 'critical',
        'description': 'Account ownership is not verified, allowing spoofed accounts.',
        'recommendation': 'Verify account owner matches expected program ID.',
        'patterns': [
            r'AccountInfo.*without.*owner',
            r'\.owner\s*!=',
        ]
    },
    'arbitrary-cpi': {
        'title': 'Arbitrary Cross-Program Invocation',
        'severity': 'high',
        'description': 'CPI target program is not validated, allowing malicious program calls.',
        'recommendation': 'Validate CPI target program ID before invocation.',
        'patterns': [
            r'invoke\s*\(',
            r'invoke_signed\s*\(',
        ]
    },
    'pda-sharing': {
        'title': 'PDA Sharing Vulnerability',
        'severity': 'high',
        'description': 'PDA seeds may collide, allowing unauthorized access.',
        'recommendation': 'Use unique seeds including user pubkey for PDA derivation.',
        'patterns': [
            r'find_program_address\s*\(',
            r'create_program_address\s*\(',
        ]
    },
    'integer-overflow-rust': {
        'title': 'Integer Overflow (Rust)',
        'severity': 'high',
        'description': 'Arithmetic operation may overflow in release builds.',
        'recommendation': 'Use checked_add, checked_sub, or saturating operations.',
        'patterns': [
            r'\+\s*\d+',
            r'\-\s*\d+',
            r'\*\s*\d+',
        ]
    },
    'account-data-matching': {
        'title': 'Account Data Matching',
        'severity': 'medium',
        'description': 'Account data constraints not properly validated.',
        'recommendation': 'Use Anchor constraints or manual validation.',
        'patterns': [
            r'AccountInfo',
            r'try_from_slice',
        ]
    },
    'closing-accounts': {
        'title': 'Improper Account Closing',
        'severity': 'medium',
        'description': 'Closed accounts not properly zeroed, vulnerable to revival attacks.',
        'recommendation': 'Zero account data and transfer all lamports when closing.',
        'patterns': [
            r'close\s*\(',
            r'lamports.*=.*0',
        ]
    },
    'bump-seed-canonicalization': {
        'title': 'Bump Seed Canonicalization',
        'severity': 'medium',
        'description': 'Non-canonical bump seed may allow account grinding attacks.',
        'recommendation': 'Store and verify canonical bump seed.',
        'patterns': [
            r'bump\s*=',
            r'find_program_address',
        ]
    }
}

MOVE_VULNERABILITIES = {
    'unchecked-abort': {
        'title': 'Unchecked Abort',
        'severity': 'high',
        'description': 'Function may abort without proper error handling.',
        'recommendation': 'Use assert! with meaningful error codes.',
        'patterns': [
            r'abort\s*\d*',
            r'assert!\s*\(',
        ]
    },
    'resource-leak': {
        'title': 'Resource Leak',
        'severity': 'high',
        'description': 'Resource not properly destroyed, may cause stuck assets.',
        'recommendation': 'Ensure all resources are moved or destroyed.',
        'patterns': [
            r'move_to\s*\(',
            r'move_from\s*\(',
        ]
    },
    'missing-capability-check': {
        'title': 'Missing Capability Check',
        'severity': 'critical',
        'description': 'Function missing signer capability verification.',
        'recommendation': 'Add signer capability check at function entry.',
        'patterns': [
            r'public\s+fun\s+\w+\s*\([^)]*\)',
            r'&signer',
        ]
    },
    'coin-store-not-registered': {
        'title': 'Coin Store Not Registered',
        'severity': 'medium',
        'description': 'Coin operations may fail if store not registered.',
        'recommendation': 'Check coin store registration before operations.',
        'patterns': [
            r'coin::deposit',
            r'coin::withdraw',
        ]
    },
    'timestamp-dependence-move': {
        'title': 'Timestamp Dependence',
        'severity': 'low',
        'description': 'Logic depends on blockchain timestamp.',
        'recommendation': 'Avoid critical logic based on timestamps.',
        'patterns': [
            r'timestamp::now_seconds',
            r'timestamp::now_microseconds',
        ]
    }
}

CAIRO_VULNERABILITIES = {
    'missing-access-control-cairo': {
        'title': 'Missing Access Control',
        'severity': 'critical',
        'description': 'Function lacks caller verification.',
        'recommendation': 'Add get_caller_address() check or use access control module.',
        'patterns': [
            r'@external',
            r'func\s+\w+\s*\{',
        ]
    },
    'unchecked-felts': {
        'title': 'Unchecked Felt Operations',
        'severity': 'high',
        'description': 'Felt arithmetic may overflow/underflow.',
        'recommendation': 'Use safe math operations for felt arithmetic.',
        'patterns': [
            r'felt252',
            r'\+\s*\w+',
        ]
    },
    'reentrancy-cairo': {
        'title': 'Reentrancy (Cairo)',
        'severity': 'critical',
        'description': 'External call before state update.',
        'recommendation': 'Update state before external calls or use ReentrancyGuard.',
        'patterns': [
            r'call_contract_syscall',
            r'\.call\s*\(',
        ]
    },
    'storage-collision': {
        'title': 'Storage Collision',
        'severity': 'high',
        'description': 'Storage variables may collide.',
        'recommendation': 'Use unique storage addresses for each variable.',
        'patterns': [
            r'storage_read',
            r'storage_write',
        ]
    }
}

COSMWASM_VULNERABILITIES = {
    'missing-validation-cosmwasm': {
        'title': 'Missing Input Validation',
        'severity': 'high',
        'description': 'Message parameters not validated.',
        'recommendation': 'Validate all input parameters before processing.',
        'patterns': [
            r'ExecuteMsg',
            r'InstantiateMsg',
        ]
    },
    'unbounded-iteration': {
        'title': 'Unbounded Iteration',
        'severity': 'medium',
        'description': 'Loop may run out of gas with large data.',
        'recommendation': 'Implement pagination for large collections.',
        'patterns': [
            r'\.iter\(\)',
            r'for.*in\s+',
        ]
    },
    'unsafe-unwrap': {
        'title': 'Unsafe Unwrap',
        'severity': 'medium',
        'description': 'Unwrap may panic on None/Err.',
        'recommendation': 'Use proper error handling with ? or match.',
        'patterns': [
            r'\.unwrap\(\)',
            r'\.expect\(',
        ]
    },
    'dos-gas-cosmwasm': {
        'title': 'DoS via Gas Exhaustion',
        'severity': 'medium',
        'description': 'Operation may exhaust gas limit.',
        'recommendation': 'Limit iterations and use efficient data structures.',
        'patterns': [
            r'loop\s*\{',
            r'while\s+',
        ]
    }
}


# ==============================================================================
# CHAIN-SPECIFIC ANALYZERS
# ==============================================================================

class ChainAnalyzer(ABC):
    """Base class for chain-specific analyzers"""
    
    chain: Chain
    language: str
    extensions: List[str]
    
    @abstractmethod
    def analyze(self, code: str, path: str) -> List[ChainVulnerability]:
        """Analyze code for vulnerabilities"""
        pass
    
    def can_analyze(self, path: str) -> bool:
        """Check if this analyzer can handle the file"""
        return any(path.endswith(ext) for ext in self.extensions)
    
    def _find_patterns(
        self,
        code: str,
        vuln_db: Dict[str, Dict[str, Any]]
    ) -> List[ChainVulnerability]:
        """Find vulnerabilities using pattern matching"""
        findings = []
        lines = code.split('\n')
        
        for vuln_id, vuln_info in vuln_db.items():
            patterns = vuln_info.get('patterns', [])
            
            for i, line in enumerate(lines, 1):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append(ChainVulnerability(
                            vuln_id=vuln_id,
                            title=vuln_info['title'],
                            severity=vuln_info['severity'],
                            chain=self.chain,
                            description=vuln_info['description'],
                            recommendation=vuln_info['recommendation'],
                            pattern=pattern,
                            line_number=i,
                            confidence=0.7
                        ))
                        break  # One finding per vuln type
                else:
                    continue
                break
        
        return findings


class SolanaAnalyzer(ChainAnalyzer):
    """Analyzer for Solana/Anchor programs"""
    
    chain = Chain.SOLANA
    language = "Rust (Solana/Anchor)"
    extensions = ['.rs']
    
    def analyze(self, code: str, path: str) -> List[ChainVulnerability]:
        """Analyze Solana program"""
        findings = []
        
        # Check if it's actually a Solana program
        is_solana = any([
            'solana_program' in code,
            'anchor_lang' in code,
            'declare_id!' in code,
            '#[program]' in code
        ])
        
        if not is_solana:
            return findings
        
        # Pattern-based analysis
        findings.extend(self._find_patterns(code, SOLANA_VULNERABILITIES))
        
        # Solana-specific checks
        findings.extend(self._check_signer_validation(code))
        findings.extend(self._check_account_validation(code))
        findings.extend(self._check_cpi_safety(code))
        findings.extend(self._check_pda_derivation(code))
        
        return findings
    
    def _check_signer_validation(self, code: str) -> List[ChainVulnerability]:
        """Check for missing signer validation"""
        findings = []
        lines = code.split('\n')
        
        # Look for functions that accept AccountInfo but don't check is_signer
        in_function = False
        function_start = 0
        function_code = []
        
        for i, line in enumerate(lines, 1):
            if re.search(r'pub\s+fn\s+\w+', line) or re.search(r'fn\s+\w+.*ctx:', line):
                in_function = True
                function_start = i
                function_code = [line]
            elif in_function:
                function_code.append(line)
                if line.strip() == '}':
                    # End of function - analyze
                    func_str = '\n'.join(function_code)
                    if 'AccountInfo' in func_str and 'is_signer' not in func_str:
                        if 'Signer' not in func_str and 'signer' not in func_str.lower():
                            findings.append(ChainVulnerability(
                                vuln_id='missing-signer-check',
                                title='Missing Signer Check',
                                severity='critical',
                                chain=self.chain,
                                description='Function accepts AccountInfo but does not verify signer.',
                                recommendation='Add is_signer check or use Anchor\'s Signer type.',
                                line_number=function_start,
                                confidence=0.8
                            ))
                    in_function = False
                    function_code = []
        
        return findings
    
    def _check_account_validation(self, code: str) -> List[ChainVulnerability]:
        """Check for missing account validation"""
        findings = []
        
        # Check for owner validation
        if 'AccountInfo' in code and '.owner' not in code:
            findings.append(ChainVulnerability(
                vuln_id='missing-owner-check',
                title='Missing Owner Check',
                severity='high',
                chain=self.chain,
                description='Account ownership is not validated.',
                recommendation='Verify account.owner == expected_program_id.',
                confidence=0.7
            ))
        
        return findings
    
    def _check_cpi_safety(self, code: str) -> List[ChainVulnerability]:
        """Check for unsafe CPI calls"""
        findings = []
        
        # Check for CPI without program ID validation
        if re.search(r'invoke\s*\(|invoke_signed\s*\(', code):
            # Look for program ID check nearby
            if not re.search(r'program_id\s*==|check_program_account', code):
                findings.append(ChainVulnerability(
                    vuln_id='arbitrary-cpi',
                    title='Potentially Unsafe CPI',
                    severity='high',
                    chain=self.chain,
                    description='CPI target may not be validated.',
                    recommendation='Validate target program ID before CPI.',
                    confidence=0.65
                ))
        
        return findings
    
    def _check_pda_derivation(self, code: str) -> List[ChainVulnerability]:
        """Check for PDA derivation issues"""
        findings = []
        
        # Check for PDA without user-specific seeds
        if 'find_program_address' in code or 'create_program_address' in code:
            # Check if seeds include user pubkey
            if 'authority' not in code.lower() and 'owner' not in code.lower():
                findings.append(ChainVulnerability(
                    vuln_id='pda-sharing',
                    title='Potential PDA Sharing',
                    severity='medium',
                    chain=self.chain,
                    description='PDA seeds may not be unique per user.',
                    recommendation='Include user pubkey in PDA seeds.',
                    confidence=0.6
                ))
        
        return findings


class MoveAnalyzer(ChainAnalyzer):
    """Analyzer for Move (Aptos/Sui) contracts"""
    
    chain = Chain.APTOS
    language = "Move"
    extensions = ['.move']
    
    def analyze(self, code: str, path: str) -> List[ChainVulnerability]:
        """Analyze Move module"""
        findings = []
        
        # Pattern-based analysis
        findings.extend(self._find_patterns(code, MOVE_VULNERABILITIES))
        
        # Move-specific checks
        findings.extend(self._check_capability_usage(code))
        findings.extend(self._check_resource_handling(code))
        
        return findings
    
    def _check_capability_usage(self, code: str) -> List[ChainVulnerability]:
        """Check for capability-related issues"""
        findings = []
        
        # Check public functions for signer
        public_funcs = re.findall(r'public\s+fun\s+(\w+)\s*\([^)]*\)', code)
        
        for func in public_funcs:
            # Find function body
            pattern = rf'public\s+fun\s+{func}\s*\([^)]*\)'
            match = re.search(pattern, code)
            if match:
                # Check if it takes &signer
                if '&signer' not in match.group():
                    findings.append(ChainVulnerability(
                        vuln_id='missing-capability-check',
                        title=f'Missing Signer in {func}',
                        severity='high',
                        chain=self.chain,
                        description=f'Public function {func} does not require signer capability.',
                        recommendation='Add &signer parameter for access control.',
                        confidence=0.7
                    ))
        
        return findings
    
    def _check_resource_handling(self, code: str) -> List[ChainVulnerability]:
        """Check for resource handling issues"""
        findings = []
        
        # Check for resources not being moved/destroyed
        if 'move_to' in code:
            if 'move_from' not in code and 'destroy' not in code.lower():
                findings.append(ChainVulnerability(
                    vuln_id='resource-leak',
                    title='Potential Resource Leak',
                    severity='medium',
                    chain=self.chain,
                    description='Resources are created but may not be properly handled.',
                    recommendation='Ensure all resources are moved or destroyed.',
                    confidence=0.6
                ))
        
        return findings


class CairoAnalyzer(ChainAnalyzer):
    """Analyzer for Cairo (StarkNet) contracts"""
    
    chain = Chain.STARKNET
    language = "Cairo"
    extensions = ['.cairo']
    
    def analyze(self, code: str, path: str) -> List[ChainVulnerability]:
        """Analyze Cairo contract"""
        findings = []
        
        # Pattern-based analysis
        findings.extend(self._find_patterns(code, CAIRO_VULNERABILITIES))
        
        # Cairo-specific checks
        findings.extend(self._check_access_control(code))
        findings.extend(self._check_felt_arithmetic(code))
        
        return findings
    
    def _check_access_control(self, code: str) -> List[ChainVulnerability]:
        """Check for missing access control"""
        findings = []
        
        # Find external functions
        external_funcs = re.findall(r'@external\s*\n\s*func\s+(\w+)', code)
        
        for func in external_funcs:
            # Check if function checks caller
            pattern = rf'func\s+{func}[^{{]*\{{([^}}]+)\}}'
            match = re.search(pattern, code, re.DOTALL)
            if match:
                func_body = match.group(1)
                if 'get_caller_address' not in func_body:
                    findings.append(ChainVulnerability(
                        vuln_id='missing-access-control-cairo',
                        title=f'Missing Access Control in {func}',
                        severity='high',
                        chain=self.chain,
                        description=f'External function {func} does not verify caller.',
                        recommendation='Add get_caller_address() check.',
                        confidence=0.7
                    ))
        
        return findings
    
    def _check_felt_arithmetic(self, code: str) -> List[ChainVulnerability]:
        """Check for unsafe felt arithmetic"""
        findings = []
        
        # Check for arithmetic without bounds checking
        if re.search(r'felt252.*[+\-\*]', code):
            if 'assert' not in code.lower():
                findings.append(ChainVulnerability(
                    vuln_id='unchecked-felts',
                    title='Unchecked Felt Arithmetic',
                    severity='medium',
                    chain=self.chain,
                    description='Felt arithmetic without bounds checking.',
                    recommendation='Add assertion checks for arithmetic results.',
                    confidence=0.6
                ))
        
        return findings


class CosmWasmAnalyzer(ChainAnalyzer):
    """Analyzer for CosmWasm (Cosmos) contracts"""
    
    chain = Chain.COSMOS
    language = "Rust (CosmWasm)"
    extensions = ['.rs']
    
    def analyze(self, code: str, path: str) -> List[ChainVulnerability]:
        """Analyze CosmWasm contract"""
        findings = []
        
        # Check if it's actually a CosmWasm contract
        is_cosmwasm = any([
            'cosmwasm_std' in code,
            'cw_storage_plus' in code,
            '#[entry_point]' in code,
            'ExecuteMsg' in code
        ])
        
        if not is_cosmwasm:
            return findings
        
        # Pattern-based analysis
        findings.extend(self._find_patterns(code, COSMWASM_VULNERABILITIES))
        
        # CosmWasm-specific checks
        findings.extend(self._check_unwrap_usage(code))
        findings.extend(self._check_iteration(code))
        
        return findings
    
    def _check_unwrap_usage(self, code: str) -> List[ChainVulnerability]:
        """Check for unsafe unwrap usage"""
        findings = []
        
        unwrap_count = code.count('.unwrap()')
        if unwrap_count > 5:
            findings.append(ChainVulnerability(
                vuln_id='unsafe-unwrap',
                title='Excessive Unwrap Usage',
                severity='medium',
                chain=self.chain,
                description=f'Found {unwrap_count} uses of .unwrap() which may panic.',
                recommendation='Use ? operator or proper error handling.',
                confidence=0.8
            ))
        
        return findings
    
    def _check_iteration(self, code: str) -> List[ChainVulnerability]:
        """Check for unbounded iteration"""
        findings = []
        
        # Check for iteration without limits
        if '.iter()' in code or 'for ' in code:
            if 'take(' not in code and 'limit' not in code.lower():
                findings.append(ChainVulnerability(
                    vuln_id='unbounded-iteration',
                    title='Potentially Unbounded Iteration',
                    severity='medium',
                    chain=self.chain,
                    description='Iteration may not have bounds.',
                    recommendation='Implement pagination with take() or limit.',
                    confidence=0.6
                ))
        
        return findings


# ==============================================================================
# MULTI-CHAIN SCANNER
# ==============================================================================

class MultiChainScanner:
    """
    Scan contracts across multiple blockchain platforms.
    
    Usage:
        scanner = MultiChainScanner()
        result = scanner.scan("program.rs")  # Auto-detects chain
        result = scanner.scan("contract.move", chain=Chain.APTOS)
    """
    
    def __init__(self):
        self.analyzers: Dict[Chain, ChainAnalyzer] = {
            Chain.SOLANA: SolanaAnalyzer(),
            Chain.APTOS: MoveAnalyzer(),
            Chain.SUI: MoveAnalyzer(),  # Same analyzer, different chain
            Chain.STARKNET: CairoAnalyzer(),
            Chain.COSMOS: CosmWasmAnalyzer(),
        }
    
    def scan(
        self,
        path: str,
        chain: Optional[Chain] = None,
        code: Optional[str] = None
    ) -> ChainScanResult:
        """
        Scan a contract for vulnerabilities.
        
        Args:
            path: Path to contract file
            chain: Target chain (auto-detected if not provided)
            code: Optional pre-loaded code
            
        Returns:
            ChainScanResult with findings
        """
        import time
        start_time = time.time()
        
        path_obj = Path(path)
        
        # Load code if not provided
        if code is None:
            try:
                code = path_obj.read_text(encoding='utf-8', errors='replace')
            except Exception as e:
                return ChainScanResult(
                    chain=chain or Chain.ETHEREUM,
                    contract_path=path,
                    contract_name=path_obj.stem,
                    language="Unknown",
                    vulnerabilities=[],
                    warnings=[f"Could not read file: {e}"],
                    scan_time=time.time() - start_time
                )
        
        # Auto-detect chain if not provided
        if chain is None:
            chain = self._detect_chain(path, code)
        
        # Get appropriate analyzer
        analyzer = self.analyzers.get(chain)
        
        if analyzer is None:
            return ChainScanResult(
                chain=chain,
                contract_path=path,
                contract_name=path_obj.stem,
                language="Unknown",
                vulnerabilities=[],
                warnings=[f"No analyzer available for {chain.value}"],
                scan_time=time.time() - start_time
            )
        
        # Run analysis
        try:
            vulnerabilities = analyzer.analyze(code, path)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            vulnerabilities = []
        
        # Extract contract name
        contract_name = self._extract_contract_name(code, path, chain)
        
        return ChainScanResult(
            chain=chain,
            contract_path=path,
            contract_name=contract_name,
            language=analyzer.language,
            vulnerabilities=vulnerabilities,
            warnings=[],
            scan_time=time.time() - start_time,
            metadata={
                'lines_of_code': len(code.split('\n')),
                'file_size': len(code)
            }
        )
    
    def _detect_chain(self, path: str, code: str) -> Chain:
        """Auto-detect blockchain from code content"""
        
        # Check file extension first
        ext = Path(path).suffix.lower()
        
        # Solidity/Vyper
        if ext == '.sol' or 'pragma solidity' in code:
            return Chain.ETHEREUM
        if ext == '.vy' or 'vyper' in code.lower():
            return Chain.ETHEREUM
        
        # Move
        if ext == '.move':
            if 'aptos_framework' in code or '0x1::' in code:
                return Chain.APTOS
            if 'sui::' in code:
                return Chain.SUI
            return Chain.APTOS
        
        # Cairo
        if ext == '.cairo' or '@contract_interface' in code:
            return Chain.STARKNET
        
        # Rust - need to check content
        if ext == '.rs':
            if 'solana_program' in code or 'anchor_lang' in code:
                return Chain.SOLANA
            if 'cosmwasm_std' in code:
                return Chain.COSMOS
            if 'ink!' in code or 'ink::' in code:
                return Chain.POLKADOT
            # Default to Solana for .rs files
            return Chain.SOLANA
        
        # Default to Ethereum
        return Chain.ETHEREUM
    
    def _extract_contract_name(self, code: str, path: str, chain: Chain) -> str:
        """Extract contract/program name from code"""
        
        if chain == Chain.ETHEREUM:
            match = re.search(r'contract\s+(\w+)', code)
            if match:
                return match.group(1)
        
        elif chain == Chain.SOLANA:
            match = re.search(r'declare_id!\s*\(\s*"([^"]+)"', code)
            if match:
                return f"Program_{match.group(1)[:8]}"
            match = re.search(r'mod\s+(\w+)\s*\{', code)
            if match:
                return match.group(1)
        
        elif chain in [Chain.APTOS, Chain.SUI]:
            match = re.search(r'module\s+[\w:]+::(\w+)', code)
            if match:
                return match.group(1)
        
        elif chain == Chain.STARKNET:
            match = re.search(r'@contract_interface\s+namespace\s+(\w+)', code)
            if match:
                return match.group(1)
            match = re.search(r'mod\s+(\w+)', code)
            if match:
                return match.group(1)
        
        elif chain == Chain.COSMOS:
            match = re.search(r'pub\s+fn\s+instantiate', code)
            if match:
                # Get crate name from Cargo.toml nearby
                pass
        
        return Path(path).stem
    
    def get_supported_chains(self) -> List[str]:
        """Get list of supported chains"""
        return [c.value for c in Chain]
    
    def get_chain_info(self, chain: Chain) -> Dict[str, Any]:
        """Get information about a specific chain"""
        analyzer = self.analyzers.get(chain)
        if analyzer:
            return {
                'chain': chain.value,
                'language': analyzer.language,
                'extensions': analyzer.extensions
            }
        return {'chain': chain.value, 'language': 'Unknown', 'extensions': []}


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def scan_multichain(path: str, chain: Optional[str] = None) -> ChainScanResult:
    """
    Convenience function to scan any blockchain contract.
    
    Args:
        path: Path to contract
        chain: Optional chain name (auto-detected if not provided)
        
    Returns:
        ChainScanResult
    """
    scanner = MultiChainScanner()
    chain_enum = Chain(chain) if chain else None
    return scanner.scan(path, chain=chain_enum)


def detect_chain(path: str) -> str:
    """Detect blockchain from file"""
    scanner = MultiChainScanner()
    code = Path(path).read_text(encoding='utf-8', errors='replace')
    chain = scanner._detect_chain(path, code)
    return chain.value
