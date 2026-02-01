"""Browser engine for Sportsbook scraping."""
import random
from contextlib import asynccontextmanager
from typing import Optional

import agentql
from playwright.async_api import async_playwright, Geolocation, ProxySettings

from commonv2 import get_logger
from odds_scraper.config.settings import BrowserConfig

logger = get_logger(__name__)


class BrowserEngine:
    """
    Manages Playwright browser lifecycle with anti-detection.
    
    Features:
    - Random user agents, viewport sizes
    - Proxy support
    - Stealth mode via AgentQL
    """
    
    def __init__(self, config: BrowserConfig):
        self.config = config
    
    @asynccontextmanager
    async def create_context(self):
        """
        Create and manage browser context.
        
        Yields:
            AgentQL-wrapped Playwright page
        """
        browser = None
        context = None
        
        try:
            async with async_playwright() as playwright:
                # Launch browser
                browser = await playwright.chromium.launch(
                    headless=self.config.headless,
                    args=self.config.browser_args,
                    ignore_default_args=self.config.browser_ignored_args
                )
                
                # Randomize fingerprint
                user_agent = random.choice(self.config.user_agents)
                location = self._get_random_location()
                
                # Create context with anti-detection
                context = await browser.new_context(
                    proxy=self._get_proxy(),
                    locale="en-US",
                    timezone_id=location['timezone'],
                    extra_http_headers={
                        "Accept-Language": random.choice(self.config.accept_languages),
                        "Referer": self.get_random_referer(),
                        "DNT": random.choice(["0", "1"]),
                        "Connection": "keep-alive",
                        "Accept-Encoding": "gzip, deflate, br",
                    },
                    geolocation=Geolocation(
                        longitude=location['longitude'],
                        latitude=location['latitude']
                    ),
                    user_agent=user_agent,
                    permissions=["notifications"],
                    viewport={
                        "width": 1920 + random.randint(-50, 50),
                        "height": 1080 + random.randint(-50, 50),
                    },
                )
                
                # Create AgentQL-wrapped page
                page = await agentql.wrap_async(context.new_page())
                await page.enable_stealth_mode(nav_user_agent=user_agent)
                
                logger.debug(f"Browser context created (UA: {user_agent[:50]}...)")
                yield page
                
        except Exception as e:
            logger.error(f"Browser context error: {e}", exc_info=True)
            raise
        finally:
            # Playwright's 'async with' block handles cleanup of browser and context.
            # Explicitly closing here can cause "Target closed" errors if the block has already exited.
            try:
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except Exception:
                pass
    
    def get_random_referer(self) -> str:
        """Get random referer for anti-detection."""
        return random.choice(self.config.referers)
    
    def _get_random_location(self) -> dict:
        """Get random geolocation from config."""
        location = random.choice(self.config.locations)
        return {
            'timezone': location.timezone,
            'longitude': location.longitude,
            'latitude': location.latitude
        }
    
    def _get_proxy(self) -> Optional[ProxySettings]:
        """Get random proxy settings if configured."""
        if not self.config.proxies:
            return None
        
        proxy_config = random.choice(self.config.proxies)
        return ProxySettings(
            server=proxy_config.server,
            username=proxy_config.username.get_secret_value() if proxy_config.username else None,
            password=proxy_config.password.get_secret_value() if proxy_config.password else None
        )
