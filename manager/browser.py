import asyncio

import playwright.async_api as async_api
from playwright.async_api import async_playwright

import logs
from errors import ScannerError

logger = logs.get_logger('chrome_api')

SCREENSHOT_QUALITY = 80
INIT_JS_PATH = "https://cdn.jsdelivr.net/gh/martin-endress/interactive_privacyscanner@record-interaction/manager/tmp/init.js"


class Browser:
    def __init__(self, debugging_port, files_path):
        ip = "localhost"
        self._debugger_url = "http://{}:{}".format(ip, debugging_port)
        self.files_path = files_path

    async def __aenter__(self):
        await self._await_browser()

        # Create Browser
        self._playwright = await async_playwright().start()
        chromium = self._playwright.chromium
        self._browser = await chromium.connect_over_cdp(self._debugger_url)

        # Create Context (like incognito session)
        har_path = self.files_path / 'network.har'
        self._context = await self._browser.new_context(accept_downloads=False, record_har_path=har_path,
                                                        record_har_omit_content=True)

        # Create Tab
        self._page = await self._context.new_page()

        # Set init script for JS debug capabilities (see #22)
        await self._page.add_init_script(path="tmp/init2.js")

        # CDP session
        self._cdp_session = await self._context.new_cdp_session(self._page)
        await self.set_dom_breakpoints()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._context.close()
        await self._browser.close()
        await self._playwright.stop()
        logger.warning('playwright stopped')

    async def _await_browser(self, timeout=10000):
        # TODO improve
        await asyncio.sleep(3)

    async def set_dom_breakpoints(self):
        setEventBreakpoint = "DOMDebugger.setEventListenerBreakpoint"
        params = {"eventName": "click"}
        # await self._cdp_session.send(setEventBreakpoint, params)
        self._cdp_session.on('Debugger.paused', debugger_paused)

    async def cpd_send_message(self, msg, **params):
        return await self._cdp_session.send(method=msg, params=params)

    def register_event(self, event_name, function):
        # see https://playwright.dev/python/docs/api/class-cdpsession
        self._cdp_session.on(event_name, function)

    def register_page_event(self, event_name, function):
        # see https://playwright.dev/python/docs/api/class-page
        self._page.on(event_name, function)

    async def navigate_url(self, url):
        await self._page.goto(url, wait_until='domcontentloaded')

    async def get_cookies(self):
        return await self._context.cookies()

    async def clear_cookies(self):
        await self._context.clear_cookies()

    async def take_screenshot(self, path):
        await self._page.screenshot(path=path, quality=SCREENSHOT_QUALITY, type='jpeg')

    async def ignore_inputs(self, ignore):
        await self.cpd_send_message('Input.setIgnoreInputEvents', ignore=ignore)

    async def perform_user_interaction(self, interaction):
        # user interaction event is defined through 'event' and 'selector'
        event = interaction['event']
        selector = interaction['selector']
        match event:
            case 'click':
                try:
                    await self._page.click(selector, timeout=10 * 1000)  # 10 seconds
                except async_api.TimeoutError as e:
                    raise ScannerError(f"Locator not found, scan aborted ({e}).") from e
            case default:
                raise ScannerError(f"Unknown event '{default}', scan aborted.")


def debugger_paused(*args):
    logger.info(f"Debugger paused. Reason: args: {str(args)}.")  # self.cpd_send_message('Debugger.resume')
