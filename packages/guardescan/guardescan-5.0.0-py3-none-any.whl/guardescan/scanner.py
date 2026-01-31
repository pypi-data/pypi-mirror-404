"""
GuardeScan Convenience Functions
Simple API for scanning contracts
"""

from typing import List, Optional, Union
from pathlib import Path

from guardescan.core import GuardeScan, ScanResult


# Module-level scanner instance (lazy initialization)
_scanner: Optional[GuardeScan] = None


def _get_scanner() -> GuardeScan:
    """Get or create the default scanner instance"""
    global _scanner
    if _scanner is None:
        _scanner = GuardeScan()
    return _scanner


def scan(path: Union[str, Path], **kwargs) -> ScanResult:
    """
    Scan a Solidity contract or directory.
    
    This is the simplest way to use GuardeScan:
    
        from guardescan import scan
        result = scan("MyContract.sol")
        print(result.grade, result.score)
    
    Args:
        path: Path to a .sol file or directory
        **kwargs: Additional arguments passed to scanner
        
    Returns:
        ScanResult for single file, or list of ScanResult for directory
        
    Examples:
        # Scan a single file
        result = scan("MyContract.sol")
        
        # Check if contract is safe
        if result.is_safe:
            print("No vulnerabilities found!")
        
        # Get specific vulnerabilities
        critical = result.get_by_severity(Severity.CRITICAL)
    """
    scanner = _get_scanner()
    path = Path(path)
    
    if path.is_dir():
        results = scanner.scan_directory(str(path), **kwargs)
        # Return first result for directory scan
        return results[0] if results else ScanResult(
            contract_path=str(path),
            contract_name=path.name,
            scan_time=0,
            vulnerabilities=[],
            gas_issues=[],
            grade=__import__('guardescan.core', fromlist=['Grade']).Grade.A_PLUS,
            score=100.0,
            risk_rating="SAFE"
        )
    else:
        return scanner.scan(str(path), **kwargs)


def scan_file(path: Union[str, Path], **kwargs) -> ScanResult:
    """
    Scan a single Solidity file.
    
    Args:
        path: Path to the .sol file
        **kwargs: Additional scanner options
        
    Returns:
        ScanResult object
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    scanner = _get_scanner()
    return scanner.scan(str(path), **kwargs)


def scan_directory(
    path: Union[str, Path],
    recursive: bool = True,
    exclude: Optional[List[str]] = None,
    **kwargs
) -> List[ScanResult]:
    """
    Scan all Solidity files in a directory.
    
    Args:
        path: Directory path
        recursive: Whether to scan subdirectories (default: True)
        exclude: Patterns to exclude (default: ['node_modules', 'lib', 'test'])
        **kwargs: Additional scanner options
        
    Returns:
        List of ScanResult objects, one per file
        
    Example:
        results = scan_directory("./contracts")
        for result in results:
            print(f"{result.contract_name}: {result.grade.value}")
    """
    scanner = _get_scanner()
    return scanner.scan_directory(str(path), recursive=recursive, exclude=exclude)


def quick_check(path: Union[str, Path]) -> bool:
    """
    Quickly check if a contract is safe (no critical/high issues).
    
    Args:
        path: Path to the contract
        
    Returns:
        True if contract has no critical or high severity issues
        
    Example:
        if quick_check("MyContract.sol"):
            print("Contract looks safe!")
    """
    result = scan(path)
    return not result.has_critical and not result.has_high


def get_grade(path: Union[str, Path]) -> str:
    """
    Get the security grade for a contract.
    
    Args:
        path: Path to the contract
        
    Returns:
        Grade string (e.g., "A+", "B", "F")
    """
    result = scan(path)
    return result.grade.value


def get_score(path: Union[str, Path]) -> float:
    """
    Get the security score for a contract.
    
    Args:
        path: Path to the contract
        
    Returns:
        Score from 0.0 to 100.0
    """
    result = scan(path)
    return result.score
