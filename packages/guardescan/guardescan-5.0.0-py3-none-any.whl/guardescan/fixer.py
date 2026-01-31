"""
GuardeScan Auto-Fix Module
Automatically fix common vulnerabilities
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Optional

from guardescan.core import GuardeScan, Vulnerability, Severity

VERSION = '3.0.0'

# Auto-fix patterns: (vuln_type, search_pattern, replacement, description)
AUTO_FIX_PATTERNS = [
    # tx.origin -> msg.sender
    ('tx-origin', r'\btx\.origin\b', 'msg.sender', 'Replaced tx.origin with msg.sender'),
    
    # Add require for unchecked calls
    ('unchecked-call', 
     r'(\w+)\.call\{([^}]+)\}\(([^)]*)\)\s*;(?!\s*require)',
     r'(bool success, ) = \1.call{\2}(\3);\n        require(success, "Call failed");',
     'Added return value check for external call'),
    
    # Floating pragma -> fixed pragma
    ('floating-pragma',
     r'pragma\s+solidity\s*\^(\d+\.\d+\.\d+)',
     r'pragma solidity \1',
     'Fixed floating pragma to specific version'),
]

# Import additions
IMPORTS_TO_ADD = {
    'reentrancy': 'import "@openzeppelin/contracts/security/ReentrancyGuard.sol";',
    'access-control': 'import "@openzeppelin/contracts/access/Ownable.sol";',
}


def generate_fix(contract_path: str, output_path: Optional[str] = None) -> Tuple[str, List[str]]:
    """
    Generate auto-fixed version of a contract.
    
    Args:
        contract_path: Path to the contract to fix
        output_path: Optional path for output (if None, returns code only)
        
    Returns:
        Tuple of (fixed_code, list_of_fixes_applied)
    """
    # Read original code
    with open(contract_path, 'r', encoding='utf-8', errors='replace') as f:
        code = f.read()
    
    # Scan for vulnerabilities
    scanner = GuardeScan()
    result = scanner.scan(contract_path)
    
    fixed_code = code
    fixes_applied = []
    imports_to_add = set()
    
    # Apply pattern-based fixes
    for vuln in result.vulnerabilities:
        for vuln_type, pattern, replacement, description in AUTO_FIX_PATTERNS:
            if vuln.vuln_id == vuln_type or vuln_type in vuln.vuln_id:
                new_code = re.sub(pattern, replacement, fixed_code)
                if new_code != fixed_code:
                    fixed_code = new_code
                    fixes_applied.append(description)
        
        # Check if imports needed
        if vuln.vuln_id in IMPORTS_TO_ADD:
            imports_to_add.add(IMPORTS_TO_ADD[vuln.vuln_id])
    
    # Add ReentrancyGuard if reentrancy found
    if any(v.vuln_id == 'reentrancy' for v in result.vulnerabilities):
        if 'ReentrancyGuard' not in fixed_code:
            fixed_code = _add_reentrancy_guard(fixed_code)
            fixes_applied.append('Added ReentrancyGuard inheritance')
            imports_to_add.add('import "@openzeppelin/contracts/security/ReentrancyGuard.sol";')
    
    # Add Ownable if access control issues found
    if any(v.vuln_id == 'access-control' for v in result.vulnerabilities):
        if 'Ownable' not in fixed_code and 'onlyOwner' not in fixed_code:
            fixed_code = _add_ownable(fixed_code)
            fixes_applied.append('Added Ownable inheritance')
            imports_to_add.add('import "@openzeppelin/contracts/access/Ownable.sol";')
    
    # Add imports after pragma
    if imports_to_add:
        fixed_code = _add_imports(fixed_code, imports_to_add)
        fixes_applied.append(f'Added {len(imports_to_add)} import(s)')
    
    # Add header comment
    header = f'''// SPDX-License-Identifier: MIT
// AUTO-FIXED by GuardeScan v{VERSION}
// Original: {contract_path}
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Fixes applied: {len(fixes_applied)}
//   - {chr(10) + "//   - ".join(fixes_applied) if fixes_applied else "None"}

'''
    
    # Remove existing SPDX if we're adding header
    fixed_code = re.sub(r'^//\s*SPDX-License-Identifier:[^\n]*\n', '', fixed_code)
    fixed_code = header + fixed_code
    
    # Save if output path provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fixed_code)
    
    return fixed_code, fixes_applied


def _add_imports(code: str, imports: set) -> str:
    """Add imports after pragma statement"""
    # Find pragma
    pragma_match = re.search(r'pragma\s+solidity[^;]+;', code)
    if pragma_match:
        insert_pos = pragma_match.end()
        import_block = '\n\n' + '\n'.join(sorted(imports))
        code = code[:insert_pos] + import_block + code[insert_pos:]
    return code


def _add_reentrancy_guard(code: str) -> str:
    """Add ReentrancyGuard to contract"""
    # Find contract declaration
    contract_match = re.search(r'contract\s+(\w+)(\s+is\s+([^{]+))?\s*\{', code)
    if contract_match:
        contract_name = contract_match.group(1)
        existing_inheritance = contract_match.group(3)
        
        if existing_inheritance:
            # Add to existing inheritance
            new_inheritance = f"ReentrancyGuard, {existing_inheritance.strip()}"
            new_declaration = f"contract {contract_name} is {new_inheritance} {{"
        else:
            # Add new inheritance
            new_declaration = f"contract {contract_name} is ReentrancyGuard {{"
        
        code = code[:contract_match.start()] + new_declaration + code[contract_match.end():]
    
    return code


def _add_ownable(code: str) -> str:
    """Add Ownable to contract"""
    # Find contract declaration
    contract_match = re.search(r'contract\s+(\w+)(\s+is\s+([^{]+))?\s*\{', code)
    if contract_match:
        contract_name = contract_match.group(1)
        existing_inheritance = contract_match.group(3)
        
        if existing_inheritance:
            # Add to existing inheritance
            new_inheritance = f"Ownable, {existing_inheritance.strip()}"
            new_declaration = f"contract {contract_name} is {new_inheritance} {{"
        else:
            # Add new inheritance
            new_declaration = f"contract {contract_name} is Ownable {{"
        
        code = code[:contract_match.start()] + new_declaration + code[contract_match.end():]
    
    return code


def suggest_fixes(vulnerabilities: List[Vulnerability]) -> List[dict]:
    """
    Suggest fixes for vulnerabilities without applying them.
    
    Returns list of fix suggestions with code examples.
    """
    suggestions = []
    
    for vuln in vulnerabilities:
        suggestion = {
            'vulnerability': vuln.title,
            'severity': vuln.severity.value,
            'fix_available': False,
            'suggestion': vuln.recommendation,
            'code_example': None
        }
        
        if vuln.vuln_id == 'reentrancy':
            suggestion['fix_available'] = True
            suggestion['code_example'] = '''
// Add ReentrancyGuard
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract MyContract is ReentrancyGuard {
    function withdraw() external nonReentrant {
        // Safe from reentrancy
    }
}
'''
        
        elif vuln.vuln_id == 'tx-origin':
            suggestion['fix_available'] = True
            suggestion['code_example'] = '''
// Replace tx.origin with msg.sender
// Before:
require(tx.origin == owner);

// After:
require(msg.sender == owner);
'''
        
        elif vuln.vuln_id == 'unchecked-call':
            suggestion['fix_available'] = True
            suggestion['code_example'] = '''
// Check return value of external calls
// Before:
target.call{value: amount}("");

// After:
(bool success, ) = target.call{value: amount}("");
require(success, "Call failed");
'''
        
        elif vuln.vuln_id == 'access-control':
            suggestion['fix_available'] = True
            suggestion['code_example'] = '''
// Add access control
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyContract is Ownable {
    function adminFunction() external onlyOwner {
        // Only owner can call
    }
}
'''
        
        suggestions.append(suggestion)
    
    return suggestions
