"""BrowserTotal Scanner - Security scanning for URLs, extensions, and packages."""

from .scanner import (
    BrowserTotalScanner,
    scan_extension,
    scan_jetbrains_plugin,
    scan_npm_package,
    scan_pypi_package,
    scan_url,
    scan_vscode_extension,
    scan_wordpress_plugin,
)
from .types import (
    BrowserStore,
    ExtensionScanResult,
    PackageScanResult,
    Platform,
    ProgressCallback,
    ScannerOptions,
    ScanPhase,
    ScanProgress,
    ScanStatus,
    ThreatInfo,
    ThreatSeverity,
    UrlScanResult,
)

__all__ = [
    # Main class
    "BrowserTotalScanner",
    # Convenience functions
    "scan_url",
    "scan_extension",
    "scan_vscode_extension",
    "scan_jetbrains_plugin",
    "scan_npm_package",
    "scan_pypi_package",
    "scan_wordpress_plugin",
    # Types
    "ScannerOptions",
    "BrowserStore",
    "Platform",
    "ScanStatus",
    "ThreatSeverity",
    "ScanPhase",
    "ThreatInfo",
    "ScanProgress",
    "ProgressCallback",
    "UrlScanResult",
    "ExtensionScanResult",
    "PackageScanResult",
]

__version__ = "1.0.0"
