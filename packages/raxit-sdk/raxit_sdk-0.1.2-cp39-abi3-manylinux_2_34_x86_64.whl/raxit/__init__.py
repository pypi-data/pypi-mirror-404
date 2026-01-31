"""RAXIT SDK - Runtime AI eXecution Integrity & Trust

Security scanning and trust boundary analysis for AI agent applications.
"""

from importlib.metadata import version, PackageNotFoundError

from .raxit import scan_py

try:
    __version__ = version("raxit-sdk")
except PackageNotFoundError:
    # Package not installed (development mode or editable install)
    __version__ = "0.1.0"  # Fallback matches pyproject.toml

__all__ = ["scan", "__version__"]


def scan(path: str, format: str = "yaml", verbose: bool = False) -> str:
    """Scan a directory for AI agent assets.

    Args:
        path: Path to the directory or file to scan
        format: Output format, either 'yaml' or 'json' (default: 'yaml')
        verbose: Enable verbose output (default: False)

    Returns:
        Scan results in the specified format

    Example:
        >>> import raxit
        >>> result = raxit.scan("./my-agent-project")
        >>> print(result)
    """
    return scan_py(path, format, verbose)
