"""Integration tests for BrowserEngine."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from odds_scraper.core.browser import BrowserEngine
from odds_scraper.config.settings import BrowserConfig, LocationConfig, ProxyConfig
from pydantic import SecretStr


class TestBrowserEngine:
    """Test suite for BrowserEngine."""
    
    @pytest.fixture
    def browser_config(self):
        """Create a basic browser configuration."""
        return BrowserConfig(
            headless=True,
            browser_args=['--no-sandbox'],
            user_agents=['Mozilla/5.0 Test Agent']
        )
    
    @pytest.fixture
    def browser_engine(self, browser_config):
        """Create BrowserEngine instance."""
        return BrowserEngine(browser_config)
    
    def test_initialization(self, browser_engine, browser_config):
        """Test BrowserEngine initialization."""
        assert browser_engine.config == browser_config
        assert isinstance(browser_engine.config, BrowserConfig)
    
    def test_get_random_referer(self, browser_engine):
        """Test random referer selection."""
        referer = browser_engine.get_random_referer()
        assert referer in browser_engine.config.referers
        assert isinstance(referer, str)
    
    def test_get_random_location(self, browser_engine):
        """Test random location selection."""
        location = browser_engine._get_random_location()
        
        assert isinstance(location, dict)
        assert 'timezone' in location
        assert 'longitude' in location
        assert 'latitude' in location
        
        assert isinstance(location['timezone'], str)
        assert isinstance(location['longitude'], float)
        assert isinstance(location['latitude'], float)
    
    def test_get_proxy_none_when_no_proxies(self, browser_engine):
        """Test proxy settings when no proxies configured."""
        proxy = browser_engine._get_proxy()
        assert proxy is None
    
    def test_get_proxy_with_configuration(self):
        """Test proxy settings with configured proxies."""
        proxy_config = ProxyConfig(
            server="http://proxy.example.com:8080",
            username=SecretStr("user123"),
            password=SecretStr("pass456")
        )
        
        config = BrowserConfig(proxies=[proxy_config])
        engine = BrowserEngine(config)
        
        proxy = engine._get_proxy()
        assert proxy is not None
        assert proxy.server == "http://proxy.example.com:8080"
        assert proxy.username == "user123"
        assert proxy.password == "pass456"
    
    def test_get_proxy_without_credentials(self):
        """Test proxy settings without credentials."""
        proxy_config = ProxyConfig(server="http://proxy.example.com:8080")
        config = BrowserConfig(proxies=[proxy_config])
        engine = BrowserEngine(config)
        
        proxy = engine._get_proxy()
        assert proxy is not None
        assert proxy.server == "http://proxy.example.com:8080"
        assert proxy.username is None
        assert proxy.password is None
    
    def test_multiple_locations(self):
        """Test with multiple location configurations."""
        locations = [
            LocationConfig(timezone='America/New_York', longitude=-74.0, latitude=40.7),
            LocationConfig(timezone='America/Chicago', longitude=-87.6, latitude=41.8),
            LocationConfig(timezone='America/Los_Angeles', longitude=-118.2, latitude=34.0)
        ]
        
        config = BrowserConfig(locations=locations)
        engine = BrowserEngine(config)
        
        # Test that we get one of the configured locations
        location = engine._get_random_location()
        assert location['timezone'] in ['America/New_York', 'America/Chicago', 'America/Los_Angeles']
    
    def test_multiple_user_agents(self):
        """Test with multiple user agents."""
        user_agents = [
            'Mozilla/5.0 Agent 1',
            'Mozilla/5.0 Agent 2',
            'Mozilla/5.0 Agent 3'
        ]
        config = BrowserConfig(user_agents=user_agents)
        engine = BrowserEngine(config)
        
        assert engine.config.user_agents == user_agents
    
    def test_browser_args_configuration(self):
        """Test browser arguments configuration."""
        custom_args = ['--no-sandbox', '--disable-gpu', '--window-size=1920,1080']
        config = BrowserConfig(browser_args=custom_args)
        engine = BrowserEngine(config)
        
        assert engine.config.browser_args == custom_args
    
    def test_headless_mode_configuration(self):
        """Test headless mode configuration."""
        # Headless mode
        config_headless = BrowserConfig(headless=True)
        engine_headless = BrowserEngine(config_headless)
        assert engine_headless.config.headless is True
        
        # Visible mode
        config_visible = BrowserConfig(headless=False)
        engine_visible = BrowserEngine(config_visible)
        assert engine_visible.config.headless is False


# These tests require Playwright to be installed and may be slow
# Mark them as integration tests
@pytest.mark.integration
@pytest.mark.asyncio
class TestBrowserEngineIntegration:
    """Integration tests requiring Playwright."""
    
    @pytest.fixture
    def browser_config(self):
        """Create a basic browser configuration for integration tests."""
        return BrowserConfig(
            headless=True,  # Always headless in tests
            browser_args=['--no-sandbox', '--disable-dev-shm-usage']
        )
    
    @pytest.fixture
    def browser_engine(self, browser_config):
        """Create BrowserEngine instance."""
        return BrowserEngine(browser_config)
    
    async def test_create_context_basic(self, browser_engine):
        """Test basic browser context creation and cleanup."""
        async with browser_engine.create_context() as page:
            assert page is not None
            # Page should be an AgentQL-wrapped page
            assert hasattr(page, 'goto')
    
    async def test_create_context_navigation(self, browser_engine):
        """Test navigating to a page."""
        async with browser_engine.create_context() as page:
            # Navigate to a simple test page
            response = await page.goto('https://example.com')
            assert response is not None
            assert response.ok
    
    async def test_create_context_cleanup(self, browser_engine):
        """Test that browser context is properly cleaned up."""
        page_ref = None
        
        async with browser_engine.create_context() as page:
            page_ref = page
            assert page is not None
        
        # After context exits, page should be closed
        # Attempting to use it should raise an error
        with pytest.raises(Exception):
            await page_ref.goto('https://example.com')
    
    async def test_create_context_error_handling(self):
        """Test error handling during context creation."""
        # Create config with invalid browser args that should cause an error
        bad_config = BrowserConfig(
            browser_args=['--invalid-argument-that-does-not-exist-12345']
        )
        engine = BrowserEngine(bad_config)
        
        # Should handle error gracefully and raise
        with pytest.raises(Exception):
            async with engine.create_context() as page:
                pass


@pytest.mark.unit
class TestBrowserEngineWithMocks:
    """Unit tests using mocks to avoid Playwright dependency."""
    
    @pytest.fixture
    def browser_config(self):
        """Create browser configuration."""
        return BrowserConfig()
    
    @pytest.fixture
    def browser_engine(self, browser_config):
        """Create BrowserEngine instance."""
        return BrowserEngine(browser_config)
    
    @pytest.mark.asyncio
    async def test_create_context_with_mock_playwright(self, browser_engine):
        """Test context creation with mocked Playwright."""
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright_instance = Mock()
        
        # Setup mock chain
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        with patch('odds_scraper.core.browser.async_playwright') as mock_playwright:
            mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
            
            with patch('odds_scraper.core.browser.agentql.wrap_async') as mock_wrap:
                mock_wrapped_page = AsyncMock()
                mock_wrap.return_value = mock_wrapped_page
                
                async with browser_engine.create_context() as page:
                    assert page == mock_wrapped_page
                    
                    # Verify Playwright was called correctly
                    mock_playwright_instance.chromium.launch.assert_called_once()
                    mock_browser.new_context.assert_called_once()
                    
                    # Verify AgentQL wrapping
                    mock_wrap.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_context_applies_configuration(self, browser_engine):
        """Test that configuration is properly applied to browser context."""
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright_instance = Mock()
        
        # Setup mock chain
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        with patch('odds_scraper.core.browser.async_playwright') as mock_playwright:
            mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
            
            with patch('odds_scraper.core.browser.agentql.wrap_async') as mock_wrap:
                mock_wrapped_page = AsyncMock()
                mock_wrap.return_value = mock_wrapped_page
                
                async with browser_engine.create_context() as page:
                    # Verify launch arguments were passed
                    launch_call = mock_playwright_instance.chromium.launch.call_args
                    assert launch_call.kwargs['headless'] == browser_engine.config.headless
                    assert launch_call.kwargs['args'] == browser_engine.config.browser_args
                    
                    # Verify context configuration
                    context_call = mock_browser.new_context.call_args
                    assert 'user_agent' in context_call.kwargs
                    assert 'geolocation' in context_call.kwargs
                    assert 'extra_http_headers' in context_call.kwargs
