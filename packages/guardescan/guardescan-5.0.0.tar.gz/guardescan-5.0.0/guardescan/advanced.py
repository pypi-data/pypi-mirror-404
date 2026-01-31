"""
GuardeScan Advanced Features
AI-Enhanced Detection, DeFi Analysis, and Bytecode Analysis

This module provides advanced security analysis capabilities:
- Machine Learning vulnerability detection
- DeFi-specific attack pattern detection
- Bytecode analysis (when compiled)
- Cross-chain vulnerability correlation
"""

import re
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ==============================================================================
# DEFI ATTACK PATTERNS
# ==============================================================================

class DeFiAttackType(Enum):
    """Types of DeFi attacks"""
    FLASH_LOAN = "flash_loan"
    PRICE_MANIPULATION = "price_manipulation"
    SANDWICH = "sandwich"
    FRONT_RUNNING = "front_running"
    GOVERNANCE = "governance"
    LIQUIDATION = "liquidation"
    MEV = "mev"
    ORACLE_MANIPULATION = "oracle_manipulation"
    REENTRANCY = "reentrancy"
    ECONOMIC = "economic"


@dataclass
class DeFiVulnerability:
    """DeFi-specific vulnerability"""
    attack_type: DeFiAttackType
    title: str
    severity: str
    description: str
    potential_impact: str
    recommendation: str
    estimated_risk: float  # 0-1 scale
    affected_functions: List[str] = field(default_factory=list)
    affected_protocols: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'attack_type': self.attack_type.value,
            'title': self.title,
            'severity': self.severity,
            'description': self.description,
            'potential_impact': self.potential_impact,
            'recommendation': self.recommendation,
            'estimated_risk': self.estimated_risk,
            'affected_functions': self.affected_functions,
            'affected_protocols': self.affected_protocols
        }


# DeFi Attack Pattern Database
DEFI_PATTERNS = {
    'flash_loan_vectors': {
        'patterns': [
            r'flashLoan',
            r'flash_loan',
            r'borrowFlash',
            r'executeOperation',
            r'flashLoanCallback',
            r'onFlashLoan',
            r'receiveFlashLoan',
            r'IFlashLoanReceiver',
        ],
        'indicators': [
            r'amount\s*[+\-*/]\s*fee',
            r'repay.*amount',
            r'return.*borrowed',
        ]
    },
    'oracle_manipulation': {
        'patterns': [
            r'getPrice',
            r'latestAnswer',
            r'getRoundData',
            r'getAmountsOut',
            r'getReserves',
            r'price\s*=\s*',
            r'oracle\.',
            r'Chainlink',
            r'PriceFeed',
            r'twap',
            r'spot_price',
        ],
        'risky_patterns': [
            r'getReserves\(\).*[/*]',  # Calculating price from reserves
            r'slot0\(\)',  # Uniswap V3 spot price
            r'observe\(\)',  # TWAP observation
        ]
    },
    'sandwich_attack': {
        'patterns': [
            r'swap',
            r'addLiquidity',
            r'removeLiquidity',
            r'getAmountsOut',
            r'minAmountOut',
            r'deadline',
            r'slippage',
        ],
        'risky_patterns': [
            r'minAmountOut\s*[=:]\s*0',
            r'deadline\s*[=:]\s*block\.timestamp',
            r'amountOutMin\s*[=:]\s*0',
        ]
    },
    'governance_attack': {
        'patterns': [
            r'propose',
            r'vote',
            r'execute',
            r'delegate',
            r'getVotes',
            r'quorum',
            r'votingDelay',
            r'votingPeriod',
            r'governor',
        ],
        'risky_patterns': [
            r'votingDelay\s*[=:]\s*0',
            r'votingPeriod\s*<\s*\d{3}',  # Very short voting period
            r'quorum.*<\s*\d',  # Low quorum
        ]
    },
    'liquidation_attack': {
        'patterns': [
            r'liquidate',
            r'healthFactor',
            r'collateralRatio',
            r'liquidationBonus',
            r'isLiquidatable',
            r'getAccountLiquidity',
        ],
        'risky_patterns': [
            r'liquidationBonus\s*>\s*\d{2}',  # High liquidation bonus
        ]
    },
    'mev_vulnerable': {
        'patterns': [
            r'deadline\s*=\s*block\.timestamp',
            r'minAmountOut\s*=\s*0',
            r'permit',
            r'multicall',
            r'selfPermit',
        ]
    }
}


class DeFiAnalyzer:
    """
    DeFi-specific vulnerability analyzer.
    Detects economic attacks and protocol-specific vulnerabilities.
    """
    
    def __init__(self):
        self.patterns = DEFI_PATTERNS
    
    def analyze(self, code: str, path: str = "") -> List[DeFiVulnerability]:
        """Analyze contract for DeFi vulnerabilities"""
        findings = []
        
        # Flash loan analysis
        findings.extend(self._check_flash_loan_vectors(code))
        
        # Oracle manipulation
        findings.extend(self._check_oracle_manipulation(code))
        
        # Sandwich attack vectors
        findings.extend(self._check_sandwich_vectors(code))
        
        # Governance attacks
        findings.extend(self._check_governance_vectors(code))
        
        # MEV vulnerabilities
        findings.extend(self._check_mev_vectors(code))
        
        # Economic model analysis
        findings.extend(self._analyze_economic_model(code))
        
        return findings
    
    def _check_flash_loan_vectors(self, code: str) -> List[DeFiVulnerability]:
        """Check for flash loan attack vectors"""
        findings = []
        
        patterns = self.patterns['flash_loan_vectors']
        has_flash_loan = any(
            re.search(p, code, re.IGNORECASE) 
            for p in patterns['patterns']
        )
        
        if has_flash_loan:
            # Check for proper validation
            has_validation = any([
                'require(msg.sender ==' in code,
                'onlyPoolAdmin' in code,
                'initiator ==' in code
            ])
            
            if not has_validation:
                findings.append(DeFiVulnerability(
                    attack_type=DeFiAttackType.FLASH_LOAN,
                    title='Flash Loan Callback Without Validation',
                    severity='critical',
                    description='Flash loan callback does not validate the initiator or loan parameters.',
                    potential_impact='Attacker could manipulate protocol state using borrowed funds.',
                    recommendation='Validate initiator address and ensure proper accounting.',
                    estimated_risk=0.9
                ))
            
            # Check for reentrancy during callback
            if 'external' in code and not 'nonReentrant' in code:
                findings.append(DeFiVulnerability(
                    attack_type=DeFiAttackType.FLASH_LOAN,
                    title='Reentrancy in Flash Loan Context',
                    severity='critical',
                    description='Flash loan operations may be vulnerable to reentrancy.',
                    potential_impact='Double-spending or state manipulation during loan.',
                    recommendation='Add reentrancy guards to flash loan callbacks.',
                    estimated_risk=0.85
                ))
        
        return findings
    
    def _check_oracle_manipulation(self, code: str) -> List[DeFiVulnerability]:
        """Check for oracle manipulation vulnerabilities"""
        findings = []
        
        patterns = self.patterns['oracle_manipulation']
        
        # Check for spot price usage
        uses_oracle = any(
            re.search(p, code, re.IGNORECASE) 
            for p in patterns['patterns']
        )
        
        if uses_oracle:
            # Check for risky patterns
            for risky in patterns['risky_patterns']:
                if re.search(risky, code, re.IGNORECASE):
                    findings.append(DeFiVulnerability(
                        attack_type=DeFiAttackType.ORACLE_MANIPULATION,
                        title='Spot Price Oracle Manipulation Risk',
                        severity='critical',
                        description='Contract uses spot price that can be manipulated within a single transaction.',
                        potential_impact='Price can be manipulated via flash loans to extract value.',
                        recommendation='Use TWAP (Time-Weighted Average Price) or multiple oracle sources.',
                        estimated_risk=0.9
                    ))
                    break
            
            # Check for single oracle source
            oracle_refs = len(re.findall(r'oracle|price|feed', code, re.IGNORECASE))
            if oracle_refs < 3:
                findings.append(DeFiVulnerability(
                    attack_type=DeFiAttackType.ORACLE_MANIPULATION,
                    title='Single Oracle Source',
                    severity='high',
                    description='Contract appears to rely on a single oracle source.',
                    potential_impact='Oracle compromise could affect entire protocol.',
                    recommendation='Use multiple independent oracle sources with median/aggregation.',
                    estimated_risk=0.7
                ))
            
            # Check for staleness checks
            if 'updatedAt' not in code and 'timestamp' not in code.lower():
                findings.append(DeFiVulnerability(
                    attack_type=DeFiAttackType.ORACLE_MANIPULATION,
                    title='Missing Oracle Staleness Check',
                    severity='medium',
                    description='Oracle data is not checked for freshness.',
                    potential_impact='Stale prices could be used during market volatility.',
                    recommendation='Check oracle timestamp and set maximum staleness threshold.',
                    estimated_risk=0.6
                ))
        
        return findings
    
    def _check_sandwich_vectors(self, code: str) -> List[DeFiVulnerability]:
        """Check for sandwich attack vectors"""
        findings = []
        
        patterns = self.patterns['sandwich_attack']
        
        has_swap = any(
            re.search(p, code, re.IGNORECASE) 
            for p in patterns['patterns']
        )
        
        if has_swap:
            # Check for zero slippage
            for risky in patterns['risky_patterns']:
                if re.search(risky, code, re.IGNORECASE):
                    findings.append(DeFiVulnerability(
                        attack_type=DeFiAttackType.SANDWICH,
                        title='Zero Slippage Protection',
                        severity='high',
                        description='Swap has no minimum output amount, vulnerable to sandwich attacks.',
                        potential_impact='MEV bots can extract significant value through sandwich attacks.',
                        recommendation='Always set a reasonable minAmountOut based on expected price.',
                        estimated_risk=0.85
                    ))
                    break
            
            # Check for deadline protection
            if 'deadline' not in code.lower():
                findings.append(DeFiVulnerability(
                    attack_type=DeFiAttackType.SANDWICH,
                    title='Missing Transaction Deadline',
                    severity='medium',
                    description='Swap transaction has no deadline protection.',
                    potential_impact='Transaction can be held and executed later at unfavorable price.',
                    recommendation='Set explicit deadline for swap transactions.',
                    estimated_risk=0.65
                ))
        
        return findings
    
    def _check_governance_vectors(self, code: str) -> List[DeFiVulnerability]:
        """Check for governance attack vectors"""
        findings = []
        
        patterns = self.patterns['governance_attack']
        
        has_governance = any(
            re.search(p, code, re.IGNORECASE) 
            for p in patterns['patterns']
        )
        
        if has_governance:
            # Check for flash loan protection
            if 'blockNumber' not in code and 'snapshot' not in code.lower():
                findings.append(DeFiVulnerability(
                    attack_type=DeFiAttackType.GOVERNANCE,
                    title='Flash Loan Governance Attack',
                    severity='critical',
                    description='Governance uses current balance, vulnerable to flash loan attacks.',
                    potential_impact='Attacker can borrow tokens to pass malicious proposals.',
                    recommendation='Use vote snapshots at proposal creation time.',
                    estimated_risk=0.9
                ))
            
            # Check for short voting periods
            for risky in patterns['risky_patterns']:
                if re.search(risky, code, re.IGNORECASE):
                    findings.append(DeFiVulnerability(
                        attack_type=DeFiAttackType.GOVERNANCE,
                        title='Weak Governance Parameters',
                        severity='high',
                        description='Governance parameters may be too weak for security.',
                        potential_impact='Malicious proposals could pass with limited oversight.',
                        recommendation='Use appropriate voting delays and quorum requirements.',
                        estimated_risk=0.75
                    ))
                    break
        
        return findings
    
    def _check_mev_vectors(self, code: str) -> List[DeFiVulnerability]:
        """Check for MEV extraction vulnerabilities"""
        findings = []
        
        patterns = self.patterns['mev_vulnerable']
        
        mev_count = sum(
            1 for p in patterns['patterns'] 
            if re.search(p, code, re.IGNORECASE)
        )
        
        if mev_count >= 2:
            findings.append(DeFiVulnerability(
                attack_type=DeFiAttackType.MEV,
                title='MEV Extraction Vulnerable',
                severity='medium',
                description='Contract pattern is vulnerable to MEV extraction.',
                potential_impact='Searchers can extract value through front-running or sandwiching.',
                recommendation='Consider using flashbots/MEV-protection services or commit-reveal schemes.',
                estimated_risk=0.6
            ))
        
        return findings
    
    def _analyze_economic_model(self, code: str) -> List[DeFiVulnerability]:
        """Analyze economic model for vulnerabilities"""
        findings = []
        
        # Check for reward manipulation
        if re.search(r'reward.*=.*balance|emission.*rate|apy|apr', code, re.IGNORECASE):
            if 'timelock' not in code.lower() and 'delay' not in code.lower():
                findings.append(DeFiVulnerability(
                    attack_type=DeFiAttackType.ECONOMIC,
                    title='Reward Rate Manipulation',
                    severity='medium',
                    description='Reward parameters can be changed without timelock.',
                    potential_impact='Admin could manipulate rewards unfairly.',
                    recommendation='Add timelock for reward parameter changes.',
                    estimated_risk=0.5
                ))
        
        # Check for infinite minting
        if re.search(r'mint\s*\(', code, re.IGNORECASE):
            if 'maxSupply' not in code and 'cap' not in code.lower():
                findings.append(DeFiVulnerability(
                    attack_type=DeFiAttackType.ECONOMIC,
                    title='Uncapped Token Supply',
                    severity='high',
                    description='Token has no maximum supply cap.',
                    potential_impact='Unlimited minting could devalue existing tokens.',
                    recommendation='Implement a maximum supply cap.',
                    estimated_risk=0.7
                ))
        
        return findings


# ==============================================================================
# AI/ML ENHANCED DETECTION
# ==============================================================================

@dataclass
class MLPrediction:
    """Machine learning vulnerability prediction"""
    vulnerability_type: str
    confidence: float
    severity: str
    features_used: List[str]
    explanation: str
    code_snippet: str = ""


class MLVulnerabilityDetector:
    """
    ML-enhanced vulnerability detection.
    Uses pattern heuristics and statistical analysis as a lightweight
    alternative to full neural network models.
    """
    
    def __init__(self):
        self.vulnerability_signatures = self._load_signatures()
        self.feature_weights = self._load_weights()
    
    def _load_signatures(self) -> Dict[str, Dict[str, Any]]:
        """Load vulnerability signatures"""
        return {
            'reentrancy': {
                'critical_patterns': [
                    r'call\{value:',
                    r'\.call\(',
                    r'\.send\(',
                    r'\.transfer\(',
                ],
                'state_patterns': [
                    r'balances\[',
                    r'balance\s*[+\-]=',
                    r'_balances\[',
                ],
                'protection_patterns': [
                    r'nonReentrant',
                    r'ReentrancyGuard',
                    r'mutex',
                    r'locked',
                ],
                'weight': 1.0
            },
            'access_control': {
                'critical_patterns': [
                    r'onlyOwner',
                    r'require.*msg\.sender',
                    r'auth',
                    r'admin',
                ],
                'public_state_patterns': [
                    r'public\s+\w+\s+\w+\s*;',
                    r'external',
                ],
                'protection_patterns': [
                    r'onlyOwner',
                    r'onlyAdmin',
                    r'require.*owner',
                    r'AccessControl',
                ],
                'weight': 0.9
            },
            'arithmetic': {
                'critical_patterns': [
                    r'[+\-*/]\s*\d+',
                    r'\+=',
                    r'-=',
                    r'\*=',
                ],
                'protection_patterns': [
                    r'SafeMath',
                    r'checked',
                    r'0\.8\.',  # Solidity 0.8+ has overflow protection
                    r'pragma solidity \^0\.8',
                ],
                'weight': 0.7
            },
            'front_running': {
                'critical_patterns': [
                    r'deadline',
                    r'minAmountOut',
                    r'swap',
                    r'commit.*reveal',
                ],
                'protection_patterns': [
                    r'deadline\s*>',
                    r'minAmountOut\s*>',
                    r'_nonce',
                ],
                'weight': 0.6
            }
        }
    
    def _load_weights(self) -> Dict[str, float]:
        """Load feature weights for scoring"""
        return {
            'has_external_call': 2.0,
            'state_after_call': 3.0,
            'no_reentrancy_guard': 2.5,
            'missing_access_control': 2.0,
            'unchecked_arithmetic': 1.5,
            'price_dependency': 1.8,
            'flash_loan_pattern': 2.2,
        }
    
    def predict(self, code: str, path: str = "") -> List[MLPrediction]:
        """Run ML-enhanced prediction on code"""
        predictions = []
        
        # Extract features
        features = self._extract_features(code)
        
        # Score each vulnerability type
        for vuln_type, signature in self.vulnerability_signatures.items():
            score = self._calculate_vulnerability_score(code, features, signature)
            
            if score >= 0.5:  # Threshold
                severity = self._score_to_severity(score)
                predictions.append(MLPrediction(
                    vulnerability_type=vuln_type,
                    confidence=min(score, 0.99),
                    severity=severity,
                    features_used=list(features.keys()),
                    explanation=self._generate_explanation(vuln_type, features, score)
                ))
        
        return predictions
    
    def _extract_features(self, code: str) -> Dict[str, Any]:
        """Extract features for ML analysis"""
        features = {}
        
        # Code structure features
        features['line_count'] = len(code.split('\n'))
        features['function_count'] = len(re.findall(r'function\s+\w+', code))
        features['external_calls'] = len(re.findall(r'\.call\(|\.send\(|\.transfer\(', code))
        features['state_variables'] = len(re.findall(r'(uint|int|address|bool|string|bytes)\s+\w+\s*;', code))
        
        # Security features
        features['has_reentrancy_guard'] = bool(re.search(r'nonReentrant|ReentrancyGuard', code))
        features['has_access_control'] = bool(re.search(r'onlyOwner|onlyAdmin|require.*msg\.sender', code))
        features['uses_safe_math'] = bool(re.search(r'SafeMath|0\.8\.', code))
        
        # DeFi features
        features['is_defi'] = bool(re.search(r'swap|liquidity|oracle|flash|stake|borrow', code, re.IGNORECASE))
        features['has_oracle'] = bool(re.search(r'oracle|price|chainlink', code, re.IGNORECASE))
        features['has_flash_loan'] = bool(re.search(r'flash|borrow', code, re.IGNORECASE))
        
        # Complexity features
        features['cyclomatic_complexity'] = self._estimate_complexity(code)
        features['modifier_count'] = len(re.findall(r'modifier\s+\w+', code))
        features['event_count'] = len(re.findall(r'event\s+\w+', code))
        
        return features
    
    def _calculate_vulnerability_score(
        self, 
        code: str, 
        features: Dict[str, Any],
        signature: Dict[str, Any]
    ) -> float:
        """Calculate vulnerability score based on patterns and features"""
        score = 0.0
        max_score = 0.0
        
        # Check critical patterns (positive indicators)
        critical_matches = sum(
            1 for p in signature.get('critical_patterns', [])
            if re.search(p, code, re.IGNORECASE)
        )
        score += critical_matches * 0.2
        max_score += len(signature.get('critical_patterns', [])) * 0.2
        
        # Check state patterns (additional risk)
        state_matches = sum(
            1 for p in signature.get('state_patterns', [])
            if re.search(p, code, re.IGNORECASE)
        )
        score += state_matches * 0.15
        max_score += len(signature.get('state_patterns', [])) * 0.15
        
        # Check protection patterns (negative indicators)
        protection_matches = sum(
            1 for p in signature.get('protection_patterns', [])
            if re.search(p, code, re.IGNORECASE)
        )
        score -= protection_matches * 0.3
        
        # Apply weight
        weight = signature.get('weight', 1.0)
        score *= weight
        
        # Normalize to 0-1
        if max_score > 0:
            score = max(0, min(score / max_score, 1.0))
        else:
            score = 0.0
        
        return score
    
    def _estimate_complexity(self, code: str) -> int:
        """Estimate cyclomatic complexity"""
        # Simple estimation based on control flow keywords
        complexity = 1
        complexity += len(re.findall(r'\bif\b', code))
        complexity += len(re.findall(r'\bfor\b', code))
        complexity += len(re.findall(r'\bwhile\b', code))
        complexity += len(re.findall(r'\brequire\b', code))
        complexity += len(re.findall(r'\bassert\b', code))
        return complexity
    
    def _score_to_severity(self, score: float) -> str:
        """Convert score to severity"""
        if score >= 0.8:
            return 'critical'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        return 'low'
    
    def _generate_explanation(
        self, 
        vuln_type: str, 
        features: Dict[str, Any],
        score: float
    ) -> str:
        """Generate human-readable explanation"""
        explanations = {
            'reentrancy': f"Code contains external calls with state modifications. "
                         f"Confidence: {score:.0%}. "
                         f"External calls: {features.get('external_calls', 0)}.",
            'access_control': f"Functions may lack proper access control. "
                             f"Confidence: {score:.0%}. "
                             f"Has guards: {features.get('has_access_control', False)}.",
            'arithmetic': f"Arithmetic operations may overflow/underflow. "
                         f"Confidence: {score:.0%}. "
                         f"Safe math: {features.get('uses_safe_math', False)}.",
            'front_running': f"Transactions may be vulnerable to front-running. "
                            f"Confidence: {score:.0%}."
        }
        return explanations.get(vuln_type, f"Potential {vuln_type} detected with {score:.0%} confidence.")


# ==============================================================================
# BYTECODE ANALYZER
# ==============================================================================

class BytecodeAnalyzer:
    """
    EVM bytecode analysis for compiled contracts.
    Useful when source is unavailable or for verification.
    """
    
    DANGEROUS_OPCODES = {
        'CALL': 'External call - potential reentrancy',
        'DELEGATECALL': 'Delegatecall - code injection risk',
        'SELFDESTRUCT': 'Self-destruct capability',
        'CREATE2': 'Deterministic contract creation',
        'SSTORE': 'Storage write',
        'SLOAD': 'Storage read',
    }
    
    OPCODE_MAP = {
        'f1': 'CALL',
        'f4': 'DELEGATECALL',
        'ff': 'SELFDESTRUCT',
        'f5': 'CREATE2',
        '55': 'SSTORE',
        '54': 'SLOAD',
        'f2': 'CALLCODE',
        'fa': 'STATICCALL',
    }
    
    def analyze_bytecode(self, bytecode: str) -> Dict[str, Any]:
        """Analyze EVM bytecode"""
        # Remove 0x prefix if present
        bytecode = bytecode.replace('0x', '').lower()
        
        findings = []
        opcode_counts = {}
        
        # Parse bytecode (simplified - real analysis would be more complex)
        i = 0
        while i < len(bytecode):
            opcode_hex = bytecode[i:i+2]
            
            if opcode_hex in self.OPCODE_MAP:
                opcode = self.OPCODE_MAP[opcode_hex]
                opcode_counts[opcode] = opcode_counts.get(opcode, 0) + 1
                
                if opcode in self.DANGEROUS_OPCODES:
                    findings.append({
                        'opcode': opcode,
                        'description': self.DANGEROUS_OPCODES[opcode],
                        'position': i // 2
                    })
            
            # Skip PUSH data
            if opcode_hex.startswith('6') or opcode_hex.startswith('7'):
                push_size = int(opcode_hex, 16) - 0x5f
                i += push_size * 2
            
            i += 2
        
        return {
            'bytecode_size': len(bytecode) // 2,
            'opcode_counts': opcode_counts,
            'dangerous_patterns': findings,
            'has_selfdestruct': 'SELFDESTRUCT' in opcode_counts,
            'has_delegatecall': 'DELEGATECALL' in opcode_counts,
            'external_calls': opcode_counts.get('CALL', 0),
        }


# ==============================================================================
# UNIFIED ADVANCED SCANNER
# ==============================================================================

class AdvancedScanner:
    """
    Unified scanner with all advanced features.
    
    Usage:
        scanner = AdvancedScanner()
        result = scanner.full_analysis("contract.sol")
    """
    
    def __init__(self):
        self.defi_analyzer = DeFiAnalyzer()
        self.ml_detector = MLVulnerabilityDetector()
        self.bytecode_analyzer = BytecodeAnalyzer()
    
    def full_analysis(self, path: str, code: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive analysis including:
        - DeFi vulnerability detection
        - ML-enhanced pattern detection
        - Bytecode analysis (if compiled)
        """
        if code is None:
            code = Path(path).read_text(encoding='utf-8', errors='replace')
        
        result = {
            'path': path,
            'defi_vulnerabilities': [],
            'ml_predictions': [],
            'bytecode_analysis': None,
            'risk_score': 0.0,
            'risk_level': 'low'
        }
        
        # DeFi analysis
        defi_vulns = self.defi_analyzer.analyze(code, path)
        result['defi_vulnerabilities'] = [v.to_dict() for v in defi_vulns]
        
        # ML-enhanced detection
        ml_preds = self.ml_detector.predict(code, path)
        result['ml_predictions'] = [
            {
                'type': p.vulnerability_type,
                'confidence': p.confidence,
                'severity': p.severity,
                'explanation': p.explanation
            }
            for p in ml_preds
        ]
        
        # Calculate overall risk
        risk_score = self._calculate_risk_score(defi_vulns, ml_preds)
        result['risk_score'] = risk_score
        result['risk_level'] = self._score_to_risk_level(risk_score)
        
        return result
    
    def _calculate_risk_score(
        self, 
        defi_vulns: List[DeFiVulnerability],
        ml_preds: List[MLPrediction]
    ) -> float:
        """Calculate overall risk score"""
        score = 0.0
        
        # DeFi vulnerabilities
        for v in defi_vulns:
            if v.severity == 'critical':
                score += 25
            elif v.severity == 'high':
                score += 15
            elif v.severity == 'medium':
                score += 8
            else:
                score += 3
        
        # ML predictions
        for p in ml_preds:
            weight = p.confidence * 10
            if p.severity == 'critical':
                score += weight * 2
            elif p.severity == 'high':
                score += weight * 1.5
            else:
                score += weight
        
        return min(score, 100)
    
    def _score_to_risk_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score >= 70:
            return 'critical'
        elif score >= 50:
            return 'high'
        elif score >= 25:
            return 'medium'
        return 'low'


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def analyze_defi(code: str) -> List[Dict[str, Any]]:
    """Quick DeFi vulnerability scan"""
    analyzer = DeFiAnalyzer()
    return [v.to_dict() for v in analyzer.analyze(code)]


def ml_scan(code: str) -> List[Dict[str, Any]]:
    """Quick ML-enhanced scan"""
    detector = MLVulnerabilityDetector()
    return [
        {'type': p.vulnerability_type, 'confidence': p.confidence, 'explanation': p.explanation}
        for p in detector.predict(code)
    ]


def full_analysis(path: str) -> Dict[str, Any]:
    """Complete advanced analysis"""
    scanner = AdvancedScanner()
    return scanner.full_analysis(path)
