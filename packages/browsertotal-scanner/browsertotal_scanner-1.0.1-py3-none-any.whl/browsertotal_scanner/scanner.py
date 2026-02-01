"""BrowserTotal Scanner - Security scanning using BrowserTotal."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import urllib.parse
from datetime import datetime, timezone
from typing import Any

import httpx
from playwright.async_api import Browser, Page, Route, async_playwright

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


CORS_PROXY_HOST = "app.browsertotal.com"

# Browser store name mappings for URL paths
BROWSER_STORE_MAP: dict[str, str] = {
    "chrome": "google",
    "firefox": "mozilla",
    "edge": "microsoft",
    "opera": "opera",
    "safari": "safari",
    "brave": "brave",
}


def to_hex(s: str) -> str:
    """Convert string to hex encoding (character by character)."""
    return "".join(format(ord(char), "02x") for char in s)


class BrowserTotalScanner:
    """Scanner for analyzing URLs, extensions, and packages using BrowserTotal."""

    BASE_URL = os.environ.get("BROWSERTOTAL_URL", "https://browsertotal.com")
    DEFAULT_TIMEOUT = 420000

    def __init__(self, options: ScannerOptions | None = None) -> None:
        """Initialize the scanner with optional configuration."""
        self.options = options or ScannerOptions()
        self._browser: Browser | None = None
        self._playwright: Any = None

    def _build_hash_params(self) -> str:
        """Build hash parameters for automation."""
        params = ["automationEvent=true"]
        if self.options.disable_ai:
            params.append("disableAI=true")
        return "#" + "&".join(params)

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is launched and return it."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            launch_options: dict[str, Any] = {
                "headless": self.options.headless,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            }
            if self.options.user_data_dir:
                launch_options["user_data_dir"] = self.options.user_data_dir

            self._browser = await self._playwright.chromium.launch(**launch_options)
        return self._browser

    async def _setup_cors_proxy_bypass(self, page: Page) -> None:
        """Setup request interception to bypass CORS proxy in Python context."""

        async def handle_route(route: Route) -> None:
            url = route.request.url
            try:
                parsed_url = urllib.parse.urlparse(url)
                if parsed_url.netloc == CORS_PROXY_HOST:
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    if "t" in query_params:
                        encoded_url = query_params["t"][0]

                        # Decode: base64 decode → URL decode
                        decoded_url = urllib.parse.unquote(
                            base64.b64decode(encoded_url).decode("utf-8")
                        )

                        print(f"[Scanner] Bypassing CORS proxy: {decoded_url}")

                        # Forward relevant headers
                        request_headers = route.request.headers
                        headers_to_forward = [
                            "accept",
                            "accept-language",
                            "user-agent",
                            "content-type",
                            "authorization",
                        ]
                        headers = {
                            k: v
                            for k, v in request_headers.items()
                            if k.lower() in headers_to_forward
                        }

                        try:
                            async with httpx.AsyncClient() as client:
                                response = await client.request(
                                    method=route.request.method,
                                    url=decoded_url,
                                    headers=headers,
                                    content=route.request.post_data,
                                    follow_redirects=True,
                                )

                                # Build response headers
                                response_headers = dict(response.headers)
                                # Remove headers that shouldn't be forwarded
                                for h in [
                                    "content-encoding",
                                    "transfer-encoding",
                                    "connection",
                                ]:
                                    response_headers.pop(h, None)

                                # Add CORS headers
                                response_headers["access-control-allow-origin"] = "*"

                                await route.fulfill(
                                    status=response.status_code,
                                    headers=response_headers,
                                    body=response.content,
                                )
                                return
                        except Exception as fetch_error:
                            print(
                                f"[Scanner] CORS proxy bypass fetch error for {decoded_url}: {fetch_error}"
                            )
                            await route.continue_()
                            return
            except Exception:
                # Not a valid URL or parsing error, continue normally
                pass

            await route.continue_()

        # Intercept all requests
        await page.route("**/*", handle_route)

    async def _create_page(self) -> Page:
        """Create a new page with CORS proxy bypass enabled."""
        browser = await self._ensure_browser()
        page = await browser.new_page()
        await self._setup_cors_proxy_bypass(page)
        return page

    async def close(self) -> None:
        """Close the browser and cleanup resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def __aenter__(self) -> "BrowserTotalScanner":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _report_progress(
        self, callback: ProgressCallback | None, progress: ScanProgress
    ) -> None:
        """Report progress if callback is provided."""
        if callback:
            callback(progress)

    @staticmethod
    def _map_status(event_status: str | None, risk_level: str | None = None) -> ScanStatus:
        """Map API status to ScanStatus enum."""
        if event_status == "error":
            return ScanStatus.ERROR

        level = (risk_level or "").lower()
        if level in ("critical", "malicious"):
            return ScanStatus.MALICIOUS
        if level in ("high", "suspicious"):
            return ScanStatus.SUSPICIOUS
        if level in ("safe", "low", "clean"):
            return ScanStatus.SAFE
        if level == "medium":
            return ScanStatus.SUSPICIOUS

        return ScanStatus.UNKNOWN

    @staticmethod
    def _map_threats(threats_data: list[dict[str, Any]] | None) -> list[ThreatInfo]:
        """Map raw threat data to ThreatInfo objects."""
        if not threats_data:
            return []
        result: list[ThreatInfo] = []
        for threat in threats_data:
            threat_type = threat.get("type") or threat.get("description") or "unknown"
            if isinstance(threat, str):
                threat_type = threat
            severity_str = (threat.get("severity") or "medium").lower()
            try:
                severity = ThreatSeverity(severity_str)
            except ValueError:
                severity = ThreatSeverity.MEDIUM
            result.append(
                ThreatInfo(
                    type=threat_type,
                    severity=severity,
                    description=threat.get("description", "") if isinstance(threat, dict) else "",
                )
            )
        return result

    async def _setup_page_listener(self, page: Page) -> None:
        """Set up the scan result event listener on the page before navigation."""
        # Use add_init_script to inject listener before page loads (like evaluateOnNewDocument)
        await page.add_init_script(
            """
            window.addEventListener('scan_result', function(event) {
                console.log('__SCAN_RESULT__:' + JSON.stringify(event.detail));
            });
        """
        )

    def _parse_scan_result(self, msg_text: str, expected_type: str) -> dict[str, Any] | None:
        """Parse scan result from console message."""
        if not msg_text.startswith("__SCAN_RESULT__:"):
            return None
        try:
            data = json.loads(msg_text[16:])
            if data and data.get("type") == expected_type:
                print(f"[Scanner] Received scan_result event: {data.get('type')}")
                return data
            else:
                print(
                    f"[Scanner] Received wrong event type: {data.get('type') if data else None}, "
                    f"expected: {expected_type}"
                )
                return None
        except json.JSONDecodeError:
            return None

    def _map_url_event_result(
        self,
        event_result: dict[str, Any],
        original_url: str,
        scan_url: str,
    ) -> UrlScanResult:
        """Map event result to UrlScanResult."""
        data = event_result.get("data") or {}

        threats_data = data.get("threats") or data.get("vulnerabilities") or []

        return UrlScanResult(
            url=original_url,
            status=self._map_status(event_result.get("status"), data.get("riskLevel")),
            score=data.get("score", 0),
            threats=self._map_threats(threats_data),
            categories=data.get("categories", []),
            scan_url=scan_url.split("#")[0],
            timestamp=event_result.get("timestamp", datetime.now(timezone.utc).isoformat()),
            raw=event_result,
        )

    def _map_extension_event_result(
        self,
        event_result: dict[str, Any],
        extension_id: str,
        scan_url: str,
    ) -> ExtensionScanResult:
        """Map event result to ExtensionScanResult."""
        data = event_result.get("data") or {}

        threats_data = data.get("threats") or data.get("vulnerabilities") or []

        return ExtensionScanResult(
            extension_id=extension_id,
            name=data.get("name", ""),
            status=self._map_status(event_result.get("status"), data.get("riskLevel")),
            score=data.get("score", 0),
            permissions=data.get("permissions", []),
            threats=self._map_threats(threats_data),
            scan_url=scan_url.split("#")[0],
            timestamp=event_result.get("timestamp", datetime.now(timezone.utc).isoformat()),
            raw=event_result,
        )

    def _map_package_event_result(
        self,
        event_result: dict[str, Any],
        package_name: str,
        platform: str,
        scan_url: str,
    ) -> PackageScanResult:
        """Map event result to PackageScanResult."""
        data = event_result.get("data") or {}

        threats_data = data.get("threats") or data.get("vulnerabilities") or []

        return PackageScanResult(
            package_name=package_name,
            platform=platform,
            name=data.get("name", ""),
            version=data.get("version", ""),
            status=self._map_status(event_result.get("status"), data.get("riskLevel")),
            score=data.get("score", 0),
            dependencies=data.get("dependencies", []),
            threats=self._map_threats(threats_data),
            scan_url=scan_url.split("#")[0],
            timestamp=event_result.get("timestamp", datetime.now(timezone.utc).isoformat()),
            raw=event_result,
        )

    async def scan_url(
        self,
        url: str,
        on_progress: ProgressCallback | None = None,
    ) -> UrlScanResult:
        """Scan a URL for security threats."""
        page = await self._create_page()

        # Collect scan results here
        scan_results: list[dict[str, Any]] = []

        def on_console(msg: Any) -> None:
            text = msg.text
            if text.startswith("__SCAN_RESULT__:"):
                try:
                    data = json.loads(text[16:])
                    print(f"[Scanner] Received scan_result event: {data.get('type')}")
                    scan_results.append(data)
                except json.JSONDecodeError as e:
                    print(f"[Scanner] JSON decode error: {e}")

        # Register console listener FIRST
        page.on("console", on_console)

        try:
            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.INITIALIZING, "Starting URL scan..."),
            )

            # Set up JS listener BEFORE navigation
            await self._setup_page_listener(page)

            hex_encoded_url = to_hex(url)
            scan_url = f"{self.BASE_URL}/analysis/urls/{hex_encoded_url}{self._build_hash_params()}"

            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.NAVIGATING, f"Navigating to {scan_url}"),
            )

            await page.goto(scan_url, wait_until="domcontentloaded", timeout=self.options.timeout)

            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.SCANNING, "Waiting for scan results..."),
            )

            event_result: dict[str, Any] | None = None

            if self.options.wait_for_results:
                # Poll for results with timeout
                timeout_seconds = self.options.timeout / 1000
                start_time = asyncio.get_event_loop().time()

                while not scan_results:
                    if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                        print("[Scanner] Timeout waiting for scan_result event")
                        break
                    await asyncio.sleep(0.5)

                # Find result with matching type
                for result in scan_results:
                    if result.get("type") == "url":
                        event_result = result
                        break

            if event_result:
                self._report_progress(
                    on_progress,
                    ScanProgress(ScanPhase.COMPLETE, "Scan complete", 1.0),
                )
                return self._map_url_event_result(event_result, url, scan_url)

            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.COMPLETE, "Scan error"),
            )
            raise RuntimeError("Scan error")

        finally:
            page.remove_listener("console", on_console)
            await page.close()

    async def scan_extension(
        self,
        extension_id: str,
        store: BrowserStore | str = BrowserStore.CHROME,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult:
        """Scan a browser extension (Chrome, Firefox, Edge, Opera, Safari, Brave)."""
        store_value = store.value if isinstance(store, BrowserStore) else store
        store_path = BROWSER_STORE_MAP.get(store_value, store_value)
        scan_url = f"{self.BASE_URL}/analysis/live/store/{store_path}/{extension_id}{self._build_hash_params()}"

        return await self._scan_generic_extension(
            extension_id, scan_url, f"{store_value} extension", on_progress
        )

    async def scan_vscode_extension(
        self,
        extension_id: str,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult:
        """Scan a VS Code Marketplace extension."""
        scan_url = f"{self.BASE_URL}/analysis/live/store/vscode/{extension_id}{self._build_hash_params()}"
        return await self._scan_generic_extension(
            extension_id, scan_url, "VS Code extension", on_progress
        )

    async def scan_openvsx_extension(
        self,
        extension_id: str,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult:
        """Scan an Open VSX Registry extension."""
        scan_url = f"{self.BASE_URL}/analysis/live/store/openvsx/{extension_id}{self._build_hash_params()}"
        return await self._scan_generic_extension(
            extension_id, scan_url, "Open VSX extension", on_progress
        )

    async def scan_jetbrains_plugin(
        self,
        plugin_id: str,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult:
        """Scan a JetBrains plugin."""
        scan_url = f"{self.BASE_URL}/analysis/live/store/jetbrains/{plugin_id}{self._build_hash_params()}"
        return await self._scan_generic_extension(
            plugin_id, scan_url, "JetBrains plugin", on_progress
        )

    async def scan_npm_package(
        self,
        package_name: str,
        on_progress: ProgressCallback | None = None,
    ) -> PackageScanResult:
        """Scan an npm package."""
        encoded_name = urllib.parse.quote(package_name, safe="")
        scan_url = f"{self.BASE_URL}/analysis/live/store/npmjs/{encoded_name}{self._build_hash_params()}"
        return await self._scan_generic_package(
            package_name, "npmjs", scan_url, "npm package", on_progress
        )

    async def scan_pypi_package(
        self,
        package_name: str,
        on_progress: ProgressCallback | None = None,
    ) -> PackageScanResult:
        """Scan a PyPI package."""
        encoded_name = urllib.parse.quote(package_name, safe="")
        scan_url = f"{self.BASE_URL}/analysis/live/store/pypi/{encoded_name}{self._build_hash_params()}"
        return await self._scan_generic_package(
            package_name, "pypi", scan_url, "PyPI package", on_progress
        )

    async def scan_wordpress_plugin(
        self,
        plugin_slug: str,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult:
        """Scan a WordPress plugin."""
        encoded_slug = urllib.parse.quote(plugin_slug, safe="")
        scan_url = f"{self.BASE_URL}/analysis/live/store/wordpress/{encoded_slug}{self._build_hash_params()}"
        return await self._scan_generic_extension(
            plugin_slug, scan_url, "WordPress plugin", on_progress
        )

    async def scan_huggingface(
        self,
        model_id: str,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult:
        """Scan a Hugging Face model or space."""
        encoded_id = urllib.parse.quote(model_id, safe="")
        scan_url = f"{self.BASE_URL}/analysis/live/store/huggingface/{encoded_id}{self._build_hash_params()}"
        return await self._scan_generic_extension(
            model_id, scan_url, "Hugging Face model", on_progress
        )

    async def scan_appsource_addin(
        self,
        addin_id: str,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult:
        """Scan a Microsoft AppSource add-in."""
        scan_url = f"{self.BASE_URL}/analysis/live/store/appsource/{addin_id}{self._build_hash_params()}"
        return await self._scan_generic_extension(
            addin_id, scan_url, "AppSource add-in", on_progress
        )

    async def scan_powershell_module(
        self,
        module_name: str,
        on_progress: ProgressCallback | None = None,
    ) -> PackageScanResult:
        """Scan a PowerShell Gallery module."""
        encoded_name = urllib.parse.quote(module_name, safe="")
        scan_url = f"{self.BASE_URL}/analysis/live/store/powershellgallery/{encoded_name}{self._build_hash_params()}"
        return await self._scan_generic_package(
            module_name, "powershellgallery", scan_url, "PowerShell module", on_progress
        )

    async def scan_salesforce_app(
        self,
        app_id: str,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult:
        """Scan a Salesforce AppExchange app."""
        scan_url = f"{self.BASE_URL}/analysis/live/store/salesforce/{app_id}{self._build_hash_params()}"
        return await self._scan_generic_extension(
            app_id, scan_url, "Salesforce app", on_progress
        )

    async def scan_by_platform(
        self,
        identifier: str,
        platform: Platform | BrowserStore | str,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult | PackageScanResult:
        """Scan using a specific platform."""
        # Check if it's a browser store
        platform_str = platform.value if isinstance(platform, (Platform, BrowserStore)) else platform
        if platform_str in BROWSER_STORE_MAP:
            return await self.scan_extension(identifier, platform_str, on_progress)

        # Map platform to appropriate scan method
        if platform_str == "vscode":
            return await self.scan_vscode_extension(identifier, on_progress)
        elif platform_str == "openvsx":
            return await self.scan_openvsx_extension(identifier, on_progress)
        elif platform_str == "jetbrains":
            return await self.scan_jetbrains_plugin(identifier, on_progress)
        elif platform_str == "npmjs":
            return await self.scan_npm_package(identifier, on_progress)
        elif platform_str == "pypi":
            return await self.scan_pypi_package(identifier, on_progress)
        elif platform_str == "wordpress":
            return await self.scan_wordpress_plugin(identifier, on_progress)
        elif platform_str == "huggingface":
            return await self.scan_huggingface(identifier, on_progress)
        elif platform_str == "appsource":
            return await self.scan_appsource_addin(identifier, on_progress)
        elif platform_str == "powershellgallery":
            return await self.scan_powershell_module(identifier, on_progress)
        elif platform_str == "salesforce":
            return await self.scan_salesforce_app(identifier, on_progress)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    async def _scan_generic_extension(
        self,
        extension_id: str,
        scan_url: str,
        type_name: str,
        on_progress: ProgressCallback | None = None,
    ) -> ExtensionScanResult:
        """Internal method for scanning extensions/plugins."""
        page = await self._create_page()

        # Collect scan results here
        scan_results: list[dict[str, Any]] = []

        def on_console(msg: Any) -> None:
            text = msg.text
            if text.startswith("__SCAN_RESULT__:"):
                try:
                    data = json.loads(text[16:])
                    print(f"[Scanner] Received scan_result event: {data.get('type')}")
                    scan_results.append(data)
                except json.JSONDecodeError as e:
                    print(f"[Scanner] JSON decode error: {e}")

        # Register console listener FIRST
        page.on("console", on_console)

        try:
            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.INITIALIZING, f"Starting {type_name} scan..."),
            )

            # Set up JS listener BEFORE navigation
            await self._setup_page_listener(page)

            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.NAVIGATING, f"Navigating to {scan_url}"),
            )

            await page.goto(scan_url, wait_until="domcontentloaded", timeout=self.options.timeout)

            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.SCANNING, f"Waiting for {type_name} analysis..."),
            )

            event_result: dict[str, Any] | None = None

            if self.options.wait_for_results:
                # Poll for results with timeout
                timeout_seconds = self.options.timeout / 1000
                start_time = asyncio.get_event_loop().time()

                while not scan_results:
                    if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                        print("[Scanner] Timeout waiting for scan_result event")
                        break
                    await asyncio.sleep(0.5)

                # Find result with matching type
                for result in scan_results:
                    if result.get("type") == "extension":
                        event_result = result
                        break

            if event_result:
                self._report_progress(
                    on_progress,
                    ScanProgress(ScanPhase.COMPLETE, "Scan complete", 1.0),
                )
                return self._map_extension_event_result(
                    event_result, extension_id, scan_url
                )

            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.COMPLETE, "Scan error"),
            )
            raise RuntimeError("Scan error")

        finally:
            page.remove_listener("console", on_console)
            await page.close()

    async def _scan_generic_package(
        self,
        package_name: str,
        platform: str,
        scan_url: str,
        type_name: str,
        on_progress: ProgressCallback | None = None,
    ) -> PackageScanResult:
        """Internal method for scanning packages."""
        page = await self._create_page()

        # Collect scan results here
        scan_results: list[dict[str, Any]] = []

        def on_console(msg: Any) -> None:
            text = msg.text
            if text.startswith("__SCAN_RESULT__:"):
                try:
                    data = json.loads(text[16:])
                    print(f"[Scanner] Received scan_result event: {data.get('type')}")
                    scan_results.append(data)
                except json.JSONDecodeError as e:
                    print(f"[Scanner] JSON decode error: {e}")

        # Register console listener FIRST
        page.on("console", on_console)

        try:
            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.INITIALIZING, f"Starting {type_name} scan..."),
            )

            # Set up JS listener BEFORE navigation
            await self._setup_page_listener(page)

            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.NAVIGATING, f"Navigating to {scan_url}"),
            )

            await page.goto(scan_url, wait_until="domcontentloaded", timeout=self.options.timeout)

            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.SCANNING, f"Waiting for {type_name} analysis..."),
            )

            event_result: dict[str, Any] | None = None

            if self.options.wait_for_results:
                # Poll for results with timeout
                timeout_seconds = self.options.timeout / 1000
                start_time = asyncio.get_event_loop().time()

                while not scan_results:
                    if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                        print("[Scanner] Timeout waiting for scan_result event")
                        break
                    await asyncio.sleep(0.5)

                # Find result with matching type
                for result in scan_results:
                    if result.get("type") == "extension":
                        event_result = result
                        break

            if event_result:
                self._report_progress(
                    on_progress,
                    ScanProgress(ScanPhase.COMPLETE, "Scan complete", 1.0),
                )
                return self._map_package_event_result(
                    event_result, package_name, platform, scan_url
                )

            self._report_progress(
                on_progress,
                ScanProgress(ScanPhase.COMPLETE, "Scan error"),
            )
            raise RuntimeError("Scan error")

        finally:
            page.remove_listener("console", on_console)
            await page.close()


# Convenience functions for one-off scans


async def scan_url(
    url: str,
    options: ScannerOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> UrlScanResult:
    """Convenience function to scan a URL."""
    async with BrowserTotalScanner(options) as scanner:
        return await scanner.scan_url(url, on_progress)


async def scan_extension(
    extension_id: str,
    store: BrowserStore | str = BrowserStore.CHROME,
    options: ScannerOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> ExtensionScanResult:
    """Convenience function to scan a browser extension."""
    async with BrowserTotalScanner(options) as scanner:
        return await scanner.scan_extension(extension_id, store, on_progress)


async def scan_vscode_extension(
    extension_id: str,
    options: ScannerOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> ExtensionScanResult:
    """Convenience function to scan a VS Code extension."""
    async with BrowserTotalScanner(options) as scanner:
        return await scanner.scan_vscode_extension(extension_id, on_progress)


async def scan_jetbrains_plugin(
    plugin_id: str,
    options: ScannerOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> ExtensionScanResult:
    """Convenience function to scan a JetBrains plugin."""
    async with BrowserTotalScanner(options) as scanner:
        return await scanner.scan_jetbrains_plugin(plugin_id, on_progress)


async def scan_npm_package(
    package_name: str,
    options: ScannerOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> PackageScanResult:
    """Convenience function to scan an npm package."""
    async with BrowserTotalScanner(options) as scanner:
        return await scanner.scan_npm_package(package_name, on_progress)


async def scan_pypi_package(
    package_name: str,
    options: ScannerOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> PackageScanResult:
    """Convenience function to scan a PyPI package."""
    async with BrowserTotalScanner(options) as scanner:
        return await scanner.scan_pypi_package(package_name, on_progress)


async def scan_wordpress_plugin(
    plugin_slug: str,
    options: ScannerOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> ExtensionScanResult:
    """Convenience function to scan a WordPress plugin."""
    async with BrowserTotalScanner(options) as scanner:
        return await scanner.scan_wordpress_plugin(plugin_slug, on_progress)
