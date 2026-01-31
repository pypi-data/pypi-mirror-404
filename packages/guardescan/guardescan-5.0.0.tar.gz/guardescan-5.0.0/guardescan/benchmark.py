"""
GuardeScan Benchmark Framework
Rigorous validation against real-world exploits and academic benchmarks

This module provides tools to measure:
- True Positive Rate (Recall) - Did we catch known vulnerabilities?
- False Positive Rate - Did we flag safe code as vulnerable?
- Precision - Of what we flagged, how much was actually vulnerable?
- F1 Score - Overall accuracy metric
- Comparison with other tools
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Real-world exploit database
# These are contracts that were ACTUALLY exploited on mainnet
REAL_WORLD_EXPLOITS = {
    # === ETHEREUM HIGH-PROFILE HACKS ===
    'dao_hack_2016': {
        'name': 'The DAO Hack',
        'chain': 'ethereum',
        'date': '2016-06-17',
        'loss': '$60M',
        'vulnerability': 'reentrancy',
        'description': 'Classic reentrancy attack that split Ethereum',
        'expected_findings': ['reentrancy'],
        'code': '''
// Simplified DAO vulnerable withdraw
contract DAO {
    mapping(address => uint) public balances;
    
    function withdraw(uint amount) public {
        require(balances[msg.sender] >= amount);
        // VULNERABLE: External call before state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;  // State update AFTER call
    }
}
'''
    },
    'parity_wallet_2017': {
        'name': 'Parity Wallet Hack',
        'chain': 'ethereum',
        'date': '2017-07-19',
        'loss': '$30M',
        'vulnerability': 'access_control',
        'description': 'Unprotected initWallet function',
        'expected_findings': ['access_control', 'unprotected_initialization'],
        'code': '''
contract WalletLibrary {
    address public owner;
    
    // VULNERABLE: Anyone can call initWallet
    function initWallet(address _owner) public {
        owner = _owner;
    }
    
    function execute(address _to, uint _value, bytes memory _data) public {
        require(msg.sender == owner);
        _to.call{value: _value}(_data);
    }
}
'''
    },
    'beanstalk_2022': {
        'name': 'Beanstalk Flash Loan Governance Attack',
        'chain': 'ethereum', 
        'date': '2022-04-17',
        'loss': '$182M',
        'vulnerability': 'flash_loan_governance',
        'description': 'Flash loan used to gain voting power and pass malicious proposal',
        'expected_findings': ['flash_loan', 'governance'],
        'code': '''
contract BeanstalkGovernance {
    mapping(address => uint) public votes;
    
    // VULNERABLE: Uses current balance for voting (flash loan vulnerable)
    function getVotes(address account) public view returns (uint) {
        return votes[account];  // No snapshot!
    }
    
    function propose(bytes memory proposal) public {
        require(getVotes(msg.sender) > proposalThreshold);
        // ... create proposal
    }
    
    function vote(uint proposalId) public {
        uint weight = getVotes(msg.sender);  // Current balance, not snapshot
        // ... cast vote
    }
}
'''
    },
    'ronin_bridge_2022': {
        'name': 'Ronin Bridge Hack',
        'chain': 'ethereum',
        'date': '2022-03-23',
        'loss': '$625M',
        'vulnerability': 'access_control',
        'description': 'Compromised validator keys, but also lacked multi-sig threshold protection',
        'expected_findings': ['access_control', 'centralization'],
        'code': '''
contract RoninBridge {
    address[] public validators;
    uint public threshold = 5;  // Only 5 of 9 needed
    
    // VULNERABLE: Low threshold + no timelock
    function withdrawERC20(
        address token,
        address to,
        uint amount,
        bytes[] memory signatures
    ) public {
        require(signatures.length >= threshold);
        // No timelock, no monitoring, instant execution
        IERC20(token).transfer(to, amount);
    }
}
'''
    },
    'wormhole_2022': {
        'name': 'Wormhole Bridge Hack',
        'chain': 'solana',
        'date': '2022-02-02',
        'loss': '$320M',
        'vulnerability': 'signature_verification',
        'description': 'Signature verification bypass in Solana program',
        'expected_findings': ['missing_signer_check', 'signature_verification'],
        'solana_code': '''
// Simplified vulnerable Wormhole code
pub fn complete_transfer(ctx: Context<CompleteTransfer>, vaa: VAA) -> Result<()> {
    // VULNERABLE: Guardian signature not properly verified
    // Attacker could pass arbitrary VAA data
    
    let amount = vaa.payload.amount;
    let recipient = vaa.payload.recipient;
    
    // Mint tokens without proper verification
    token::mint_to(
        ctx.accounts.mint_ctx(),
        amount
    )?;
    
    Ok(())
}
'''
    },
    'cream_oracle_2021': {
        'name': 'Cream Finance Oracle Manipulation',
        'chain': 'ethereum',
        'date': '2021-10-27',
        'loss': '$130M',
        'vulnerability': 'oracle_manipulation',
        'description': 'Flash loan used to manipulate oracle price',
        'expected_findings': ['oracle_manipulation', 'flash_loan'],
        'code': '''
contract CreamLending {
    // VULNERABLE: Uses spot price from AMM
    function getPrice(address token) public view returns (uint) {
        (uint reserve0, uint reserve1,) = IUniswapPair(pair).getReserves();
        return reserve1 * 1e18 / reserve0;  // Spot price - manipulatable!
    }
    
    function borrow(address token, uint amount) public {
        uint collateralValue = getCollateralValue(msg.sender);
        uint price = getPrice(token);  // Uses manipulated price
        require(amount * price <= collateralValue * ltv);
        // ... execute borrow
    }
}
'''
    },
    'badger_dao_2021': {
        'name': 'BadgerDAO Frontend Attack',
        'chain': 'ethereum',
        'date': '2021-12-02',
        'loss': '$120M',
        'vulnerability': 'approval_abuse',
        'description': 'Infinite approval exploit via compromised frontend',
        'expected_findings': ['unlimited_approval', 'centralization'],
        'code': '''
// The contract itself wasn't vulnerable, but had risky patterns
contract BadgerVault {
    // Pattern that enabled the attack:
    function deposit(uint amount) public {
        // User had given unlimited approval
        token.transferFrom(msg.sender, address(this), amount);
    }
    
    // No approval limit checks
    // No withdrawal delays
    // Centralized upgrade capability
}
'''
    },
    
    # === SOLANA EXPLOITS ===
    'cashio_2022': {
        'name': 'Cashio Infinite Mint',
        'chain': 'solana',
        'date': '2022-03-23',
        'loss': '$52M',
        'vulnerability': 'account_validation',
        'description': 'Missing validation allowed minting with fake collateral',
        'expected_findings': ['missing_account_validation', 'missing_owner_check'],
        'solana_code': '''
pub fn mint_cash(ctx: Context<MintCash>, amount: u64) -> Result<()> {
    // VULNERABLE: Collateral account not properly validated
    // Attacker created fake collateral account
    
    let collateral = &ctx.accounts.collateral;
    // Missing: verify collateral.owner == COLLATERAL_PROGRAM
    // Missing: verify collateral.mint == EXPECTED_MINT
    
    token::mint_to(
        ctx.accounts.mint_ctx(),
        amount
    )?;
    
    Ok(())
}
'''
    },
    'mango_markets_2022': {
        'name': 'Mango Markets Manipulation',
        'chain': 'solana',
        'date': '2022-10-11',
        'loss': '$114M',
        'vulnerability': 'oracle_manipulation',
        'description': 'Oracle price manipulation via low liquidity market',
        'expected_findings': ['oracle_manipulation', 'price_manipulation'],
        'solana_code': '''
pub fn update_price(ctx: Context<UpdatePrice>) -> Result<()> {
    // VULNERABLE: Single oracle source, no TWAP
    let price = ctx.accounts.oracle.price;
    
    // No staleness check
    // No deviation check
    // No multi-oracle aggregation
    
    ctx.accounts.market.oracle_price = price;
    
    Ok(())
}
'''
    },
}

# Academic benchmark datasets
ACADEMIC_BENCHMARKS = {
    'smartbugs': {
        'name': 'SmartBugs Curated Dataset',
        'url': 'https://github.com/smartbugs/smartbugs',
        'description': 'Curated dataset of vulnerable Solidity contracts',
        'categories': [
            'reentrancy',
            'access_control', 
            'arithmetic',
            'unchecked_low_level_calls',
            'denial_of_service',
            'bad_randomness',
            'front_running',
            'time_manipulation',
            'short_addresses',
        ]
    },
    'not_so_smart_contracts': {
        'name': 'Trail of Bits - Not So Smart Contracts',
        'url': 'https://github.com/crytic/not-so-smart-contracts',
        'description': 'Examples of common vulnerabilities',
    },
    'damn_vulnerable_defi': {
        'name': 'Damn Vulnerable DeFi',
        'url': 'https://www.damnvulnerabledefi.xyz/',
        'description': 'DeFi-specific vulnerability challenges',
    }
}

# Competitor tools for comparison
COMPETITOR_TOOLS = {
    'slither': {
        'name': 'Slither',
        'command': 'slither',
        'chain': 'ethereum',
        'type': 'static_analysis',
        'strengths': ['pattern detection', 'data flow', 'AST analysis'],
    },
    'mythril': {
        'name': 'Mythril',
        'command': 'myth analyze',
        'chain': 'ethereum', 
        'type': 'symbolic_execution',
        'strengths': ['deep analysis', 'exploit generation'],
    },
    'securify2': {
        'name': 'Securify2',
        'command': 'securify2',
        'chain': 'ethereum',
        'type': 'static_analysis',
        'strengths': ['pattern matching', 'semantic analysis'],
    },
    'soteria': {
        'name': 'Soteria',
        'command': 'soteria',
        'chain': 'solana',
        'type': 'static_analysis',
        'strengths': ['solana-specific', 'anchor support'],
    },
    'move_prover': {
        'name': 'Move Prover',
        'command': 'aptos move prove',
        'chain': 'aptos',
        'type': 'formal_verification',
        'strengths': ['mathematical proofs', 'complete verification'],
    }
}


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test"""
    test_name: str
    expected_vulns: List[str]
    found_vulns: List[str]
    true_positives: int
    false_positives: int
    false_negatives: int
    scan_time: float
    
    @property
    def precision(self) -> float:
        """Of what we found, how much was correct?"""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        """Of what exists, how much did we find?"""
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1_score(self) -> float:
        """Harmonic mean of precision and recall"""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)


@dataclass
class BenchmarkSuite:
    """Complete benchmark results"""
    tool_name: str
    tool_version: str
    timestamp: str
    results: List[BenchmarkResult]
    total_time: float
    
    @property
    def overall_precision(self) -> float:
        total_tp = sum(r.true_positives for r in self.results)
        total_fp = sum(r.false_positives for r in self.results)
        if total_tp + total_fp == 0:
            return 0.0
        return total_tp / (total_tp + total_fp)
    
    @property
    def overall_recall(self) -> float:
        total_tp = sum(r.true_positives for r in self.results)
        total_fn = sum(r.false_negatives for r in self.results)
        if total_tp + total_fn == 0:
            return 0.0
        return total_tp / (total_tp + total_fn)
    
    @property
    def overall_f1(self) -> float:
        if self.overall_precision + self.overall_recall == 0:
            return 0.0
        return 2 * (self.overall_precision * self.overall_recall) / (self.overall_precision + self.overall_recall)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tool': self.tool_name,
            'version': self.tool_version,
            'timestamp': self.timestamp,
            'metrics': {
                'precision': f"{self.overall_precision:.1%}",
                'recall': f"{self.overall_recall:.1%}",
                'f1_score': f"{self.overall_f1:.1%}",
            },
            'results': [
                {
                    'test': r.test_name,
                    'precision': f"{r.precision:.1%}",
                    'recall': f"{r.recall:.1%}",
                    'f1': f"{r.f1_score:.1%}",
                    'time': f"{r.scan_time:.2f}s"
                }
                for r in self.results
            ],
            'total_time': f"{self.total_time:.2f}s"
        }


class GuardeScanBenchmark:
    """
    Benchmark framework for GuardeScan.
    
    Tests against:
    1. Real-world exploits (ground truth)
    2. Academic benchmark datasets
    3. Comparison with other tools
    """
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def run_exploit_benchmarks(self, verbose: bool = True) -> BenchmarkSuite:
        """Run benchmarks against real-world exploits"""
        from guardescan import scan
        from guardescan.chains_enhanced import EnhancedMultiChainScanner
        import tempfile
        import os
        
        start_time = time.time()
        results = []
        
        scanner = EnhancedMultiChainScanner()
        
        if verbose:
            print("\n" + "="*60)
            print("GuardeScan Benchmark - Real World Exploits")
            print("="*60 + "\n")
        
        for exploit_id, exploit in REAL_WORLD_EXPLOITS.items():
            if verbose:
                print(f"Testing: {exploit['name']} ({exploit['loss']})")
            
            # Get code
            code = exploit.get('code') or exploit.get('solana_code', '')
            if not code:
                continue
            
            # Write to temp file
            ext = '.rs' if exploit['chain'] == 'solana' else '.sol'
            with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                # Run scan
                scan_start = time.time()
                
                if exploit['chain'] == 'ethereum':
                    result = scan(temp_path)
                    found = [v.vuln_id.lower() for v in result.vulnerabilities]
                else:
                    result = scanner.scan(temp_path)
                    found = [v.vuln_id.lower() for v in result.vulnerabilities]
                
                scan_time = time.time() - scan_start
                
                # Compare with expected
                expected = [v.lower() for v in exploit['expected_findings']]
                
                # Calculate metrics
                true_positives = 0
                false_negatives = 0
                
                for exp in expected:
                    # Check if any finding matches (partial match ok)
                    if any(exp in f or f in exp for f in found):
                        true_positives += 1
                    else:
                        false_negatives += 1
                
                # False positives - findings not in expected
                false_positives = len(found) - true_positives
                if false_positives < 0:
                    false_positives = 0
                
                bench_result = BenchmarkResult(
                    test_name=exploit['name'],
                    expected_vulns=expected,
                    found_vulns=found,
                    true_positives=true_positives,
                    false_positives=false_positives,
                    false_negatives=false_negatives,
                    scan_time=scan_time
                )
                
                results.append(bench_result)
                
                if verbose:
                    status = "✓" if bench_result.recall >= 0.5 else "✗"
                    print(f"  {status} Recall: {bench_result.recall:.0%}, "
                          f"Found: {found[:3]}...")
                
            finally:
                os.unlink(temp_path)
        
        total_time = time.time() - start_time
        
        suite = BenchmarkSuite(
            tool_name="GuardeScan",
            tool_version="4.0.0",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            results=results,
            total_time=total_time
        )
        
        if verbose:
            print("\n" + "-"*60)
            print(f"Overall Results:")
            print(f"  Precision: {suite.overall_precision:.1%}")
            print(f"  Recall: {suite.overall_recall:.1%}")
            print(f"  F1 Score: {suite.overall_f1:.1%}")
            print(f"  Total Time: {suite.total_time:.2f}s")
            print("-"*60 + "\n")
        
        return suite
    
    def compare_with_slither(self, contract_path: str) -> Dict[str, Any]:
        """Compare GuardeScan results with Slither"""
        import shutil
        
        results = {
            'guardescan': {},
            'slither': {},
            'comparison': {}
        }
        
        # Run GuardeScan
        from guardescan import scan
        gs_start = time.time()
        gs_result = scan(contract_path)
        gs_time = time.time() - gs_start
        
        results['guardescan'] = {
            'vulnerabilities': len(gs_result.vulnerabilities),
            'time': gs_time,
            'findings': [v.title for v in gs_result.vulnerabilities]
        }
        
        # Run Slither if available
        if shutil.which('slither'):
            try:
                sl_start = time.time()
                sl_output = subprocess.run(
                    ['slither', contract_path, '--json', '-'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                sl_time = time.time() - sl_start
                
                if sl_output.returncode == 0:
                    sl_json = json.loads(sl_output.stdout)
                    sl_findings = sl_json.get('results', {}).get('detectors', [])
                    
                    results['slither'] = {
                        'vulnerabilities': len(sl_findings),
                        'time': sl_time,
                        'findings': [f.get('check', '') for f in sl_findings[:10]]
                    }
            except Exception as e:
                results['slither'] = {'error': str(e)}
        else:
            results['slither'] = {'error': 'Slither not installed'}
        
        # Compare
        if 'error' not in results['slither']:
            gs_count = results['guardescan']['vulnerabilities']
            sl_count = results['slither']['vulnerabilities']
            
            results['comparison'] = {
                'guardescan_found_more': gs_count > sl_count,
                'difference': gs_count - sl_count,
                'speed_comparison': f"GuardeScan {gs_time/results['slither']['time']:.1f}x {'faster' if gs_time < results['slither']['time'] else 'slower'}"
            }
        
        return results
    
    def generate_report(self, suite: BenchmarkSuite, output_path: str = None) -> str:
        """Generate detailed benchmark report"""
        
        report = f"""
# GuardeScan Benchmark Report

**Tool:** {suite.tool_name} v{suite.tool_version}
**Date:** {suite.timestamp}

## Overall Metrics

| Metric | Score | Industry Standard |
|--------|-------|-------------------|
| **Precision** | {suite.overall_precision:.1%} | >80% good, >90% excellent |
| **Recall** | {suite.overall_recall:.1%} | >70% good, >85% excellent |
| **F1 Score** | {suite.overall_f1:.1%} | >75% good, >87% excellent |

## What These Metrics Mean

- **Precision**: Of all vulnerabilities reported, {suite.overall_precision:.0%} were real issues (not false alarms)
- **Recall**: Of all actual vulnerabilities, we detected {suite.overall_recall:.0%} of them
- **F1 Score**: Combined accuracy metric balancing precision and recall

## Individual Test Results

| Exploit | Loss | Precision | Recall | F1 |
|---------|------|-----------|--------|-----|
"""
        
        for r in suite.results:
            report += f"| {r.test_name} | - | {r.precision:.0%} | {r.recall:.0%} | {r.f1_score:.0%} |\n"
        
        report += f"""

## Comparison with Industry Tools

| Tool | Type | Precision | Recall | Speed |
|------|------|-----------|--------|-------|
| **GuardeScan** | Static + ML | {suite.overall_precision:.0%} | {suite.overall_recall:.0%} | Fast |
| Slither | Static | ~85% | ~75% | Fast |
| Mythril | Symbolic | ~90% | ~60% | Slow |
| Securify2 | Static | ~80% | ~70% | Medium |

## Recommendations for Validation

1. **Run on your own contracts** - Test with code you know
2. **Use multiple tools** - No single tool catches everything
3. **Manual review** - Tools are aids, not replacements
4. **Track false positives** - Report them to improve the tool

## Limitations

- Benchmark based on simplified exploit reproductions
- Real exploits may have additional complexity
- Some vulnerabilities require runtime analysis
- Cross-contract interactions not fully tested

---
*Generated by GuardeScan Benchmark Framework*
"""
        
        if output_path:
            Path(output_path).write_text(report)
        
        return report


def run_benchmark(verbose: bool = True) -> BenchmarkSuite:
    """Run complete benchmark suite"""
    benchmark = GuardeScanBenchmark()
    return benchmark.run_exploit_benchmarks(verbose=verbose)


def compare_tools(contract_path: str) -> Dict[str, Any]:
    """Compare GuardeScan with other tools"""
    benchmark = GuardeScanBenchmark()
    return benchmark.compare_with_slither(contract_path)
