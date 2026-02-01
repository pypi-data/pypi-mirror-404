"""Type definitions for BrowserTotal Scanner."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Literal, TypedDict


class BrowserStore(str, Enum):
    """Supported browser extension stores."""

    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"
    OPERA = "opera"
    SAFARI = "safari"
    BRAVE = "brave"


class Platform(str, Enum):
    """Supported non-browser platforms."""

    VSCODE = "vscode"
    OPENVSX = "openvsx"
    JETBRAINS = "jetbrains"
    NPMJS = "npmjs"
    PYPI = "pypi"
    WORDPRESS = "wordpress"
    HUGGINGFACE = "huggingface"
    APPSOURCE = "appsource"
    POWERSHELLGALLERY = "powershellgallery"
    SALESFORCE = "salesforce"


class ScanStatus(str, Enum):
    """Scan result status."""

    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    UNKNOWN = "unknown"
    ERROR = "error"


class ThreatSeverity(str, Enum):
    """Threat severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScanPhase(str, Enum):
    """Scan progress phases."""

    INITIALIZING = "initializing"
    NAVIGATING = "navigating"
    SCANNING = "scanning"
    EXTRACTING = "extracting"
    COMPLETE = "complete"


@dataclass
class ThreatInfo:
    """Information about a detected threat."""

    type: str
    severity: ThreatSeverity
    description: str


@dataclass
class ScanProgress:
    """Progress information during a scan."""

    phase: ScanPhase
    message: str
    progress: float = 0.0


ProgressCallback = Callable[[ScanProgress], None]


@dataclass
class ScannerOptions:
    """Configuration options for the scanner."""

    headless: bool = True
    timeout: int = 420000
    wait_for_results: bool = True
    disable_ai: bool = True
    user_data_dir: str | None = None


@dataclass
class UrlScanResult:
    """Result of a URL scan."""

    url: str
    status: ScanStatus
    score: int
    threats: list[ThreatInfo] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    scan_url: str = ""
    timestamp: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtensionScanResult:
    """Result of a browser extension scan."""

    extension_id: str
    name: str
    status: ScanStatus
    score: int
    permissions: list[str] = field(default_factory=list)
    threats: list[ThreatInfo] = field(default_factory=list)
    scan_url: str = ""
    timestamp: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class PackageScanResult:
    """Result of a package/plugin scan."""

    package_name: str
    platform: str
    name: str
    version: str
    status: ScanStatus
    score: int
    dependencies: list[str] = field(default_factory=list)
    threats: list[ThreatInfo] = field(default_factory=list)
    scan_url: str = ""
    timestamp: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class ScanEventData(TypedDict, total=False):
    """Raw event data from BrowserTotal."""

    url: str
    status: str
    score: int
    threats: list[dict[str, Any]]
    categories: list[str]
    extension_id: str
    name: str
    permissions: list[str]
    package_name: str
    platform: str
    version: str
    dependencies: list[str]
    timestamp: str
