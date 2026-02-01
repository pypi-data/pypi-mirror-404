# BrowserTotal Scanner

A Python SDK for security scanning URLs, browser extensions, IDE plugins, and software packages using [BrowserTotal](https://browsertotal.com).

## Installation

```bash
pip install browsertotal-scanner
```

After installation, install Playwright browsers:

```bash
playwright install chromium
```

## Quick Start

```python
import asyncio
from browsertotal_scanner import scan_url, scan_extension, BrowserStore

async def main():
    # Scan a URL
    result = await scan_url("https://example.com")
    print(f"URL Status: {result.status.value}, Score: {result.score}")

    # Scan a Chrome extension
    result = await scan_extension("cjpalhdlnbpafiamejdnhcphjbkeiagm", BrowserStore.CHROME)
    print(f"Extension: {result.name}, Status: {result.status.value}")

asyncio.run(main())
```

## Features

- **URL Scanning**: Analyze websites for security threats
- **Browser Extensions**: Scan extensions from Chrome, Firefox, Edge, Opera, Safari, and Brave
- **IDE Plugins**: Scan VS Code, Open VSX, and JetBrains plugins
- **Package Registries**: Scan npm, PyPI, WordPress plugins, and more
- **AI Analysis**: Optional AI-powered threat detection
- **Progress Tracking**: Monitor scan progress with callbacks
- **Async Support**: Built with asyncio for efficient concurrent scanning

## Supported Platforms

| Category | Platforms |
|----------|-----------|
| Browser Extensions | Chrome, Firefox, Edge, Opera, Safari, Brave |
| IDE Extensions | VS Code Marketplace, Open VSX, JetBrains |
| Package Registries | npm, PyPI, WordPress |
| Other | Hugging Face, AppSource, PowerShell Gallery, Salesforce AppExchange |

## Usage

### Using the Scanner Class

For multiple scans, use the `BrowserTotalScanner` class to reuse the browser instance:

```python
import asyncio
from browsertotal_scanner import BrowserTotalScanner, ScannerOptions, BrowserStore

async def main():
    options = ScannerOptions(
        headless=True,
        timeout=420000,
        disable_ai=True  # Set to False for AI analysis
    )

    async with BrowserTotalScanner(options) as scanner:
        # Scan multiple targets
        url_result = await scanner.scan_url("https://example.com")
        ext_result = await scanner.scan_extension("ext-id", BrowserStore.CHROME)
        npm_result = await scanner.scan_npm_package("lodash")

asyncio.run(main())
```

### Convenience Functions

For one-off scans:

```python
from browsertotal_scanner import (
    scan_url,
    scan_extension,
    scan_vscode_extension,
    scan_jetbrains_plugin,
    scan_npm_package,
    scan_pypi_package,
    scan_wordpress_plugin,
)

# Each function creates and closes its own browser instance
result = await scan_url("https://example.com")
result = await scan_extension("extension-id", "chrome")
result = await scan_vscode_extension("publisher.extension")
result = await scan_jetbrains_plugin("plugin-id")
result = await scan_npm_package("package-name")
result = await scan_pypi_package("package-name")
result = await scan_wordpress_plugin("plugin-slug")
```

### Progress Tracking

Monitor scan progress with a callback:

```python
from browsertotal_scanner import scan_url, ScanProgress

def on_progress(progress: ScanProgress):
    print(f"[{progress.phase.value}] {progress.message}")

result = await scan_url("https://example.com", on_progress=on_progress)
```

### Configuration Options

```python
from browsertotal_scanner import ScannerOptions

options = ScannerOptions(
    headless=True,          # Run browser in headless mode (default: True)
    timeout=420000,         # Timeout in milliseconds (default: 420000)
    wait_for_results=True,  # Wait for scan completion (default: True)
    disable_ai=True,        # Skip AI analysis for faster scans (default: True)
    user_data_dir=None,     # Custom browser profile directory
)
```

### Environment Variables

- `BROWSERTOTAL_URL`: Override the BrowserTotal base URL (default: `https://browsertotal.com`)

## Result Types

### UrlScanResult

```python
@dataclass
class UrlScanResult:
    url: str
    status: ScanStatus  # safe, suspicious, malicious, unknown, error
    score: int
    threats: list[ThreatInfo]
    categories: list[str]
    scan_url: str
    timestamp: str
    raw: dict[str, Any]
```

### ExtensionScanResult

```python
@dataclass
class ExtensionScanResult:
    extension_id: str
    name: str
    status: ScanStatus
    score: int
    permissions: list[str]
    threats: list[ThreatInfo]
    scan_url: str
    timestamp: str
    raw: dict[str, Any]
```

### PackageScanResult

```python
@dataclass
class PackageScanResult:
    package_name: str
    platform: str
    name: str
    version: str
    status: ScanStatus
    score: int
    dependencies: list[str]
    threats: list[ThreatInfo]
    scan_url: str
    timestamp: str
    raw: dict[str, Any]
```

## Requirements

- Python >= 3.9
- Playwright >= 1.40.0

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [BrowserTotal](https://browsertotal.com)
- [GitHub Repository](https://github.com/SeraphicSecurity/BrowserTotal)
- [Report Issues](https://github.com/SeraphicSecurity/BrowserTotal/issues)
