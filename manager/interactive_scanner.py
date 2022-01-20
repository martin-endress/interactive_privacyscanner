import asyncio
import logging
import random
from threading import Thread
from urllib.parse import urlparse

import janus

import result
import utils
from browser import ChromeBrowser
from chromedev.extractors import CookiesExtractor
from errors import ScannerInitError, ScannerError
from scanner_messages import ScannerMessage, MessageType

EXTRACTOR_CLASSES = [CookiesExtractor]
INTERACTION_BREAKPOINTS = ["focus", "click", "mouseWheel"]

logger = logging.getLogger('cdp_controller')


class UserInteraction:
    def __init__(self):
        self._user_interaction = asyncio.Event()


class InteractiveScanner(Thread):
    def __init__(self, url, debugging_port, options):
        super().__init__()
        # Mark this thread as daemon
        self.daemon = True

        # Init Message Queue
        self.event_loop = asyncio.new_event_loop()
        init_queue_task = self.event_loop.create_task(self._init_queue())
        self.event_loop.run_until_complete(init_queue_task)

        # Init Scanner
        self.url = url
        self.options = options
        self.debugging_port = debugging_port
        self.result = result.init_from_scanner(url)
        self._extractors = []
        self._page_loaded = asyncio.Event()
        self._request_will_be_sent = asyncio.Event()
        self._response_log = []
        self._user_interaction = asyncio.Event()

    async def _init_queue(self):
        self._queue = janus.Queue()

    def run(self):
        self.event_loop.run_until_complete(self.__start_scanner())
        self.event_loop.close()

    def put_msg(self, msg):
        if not isinstance(msg, ScannerMessage):
            raise ScannerError('Element is not a Scanner Message.')
        if self._queue is None:
            raise ScannerInitError('Queue not correctly initialized.')
        self._queue.sync_q.put(msg)

    async def __start_scanner(self):
        async with ChromeBrowser(debugging_port=self.debugging_port) as b:
            self.browser = b
            while True:
                logger.info("Waiting for scanner message.")
                message = await self._queue.async_q.get()
                try:
                    r = await self.__process_message(message)
                    if r:
                        logger.info('Scan complete, terminating thread.')
                        return
                except ScannerError as e:
                    logger.error(str(e))
                    continue

    async def __process_message(self, message):
        logger.info('processing message %s' % str(message))
        match message:
            case ScannerMessage(message_type=MessageType.StartScan):
                await self.__navigate_to_page()
            case ScannerMessage(message_type=MessageType.StopScan):
                return True
            case unknown_command:
                raise ScannerError(f"Unknown command '{unknown_command}' ignored.")
        return False

    async def __navigate_to_page(self):
        await self.browser.Target.setAutoAttach(
            autoAttach=True, waitForDebuggerOnStart=False, flatten=True
        )
        self.target = await self.browser.new_target()
        logger.info("new target created")

        # Register domain notifications and callbacks
        await self.register_callbacks()

        # Navigate to url
        await self.target.Input.setIgnoreInputEvents(ignore=True)
        logger.info("navigating to page")
        await self.target.Page.navigate(url=self.url)

        await self.target.BackgroundService.startObserving(service="backgroundFetch")

        loaded = await self.__await_page_load()
        return
        await self.scroll_down_up()
        await self.__await_page_load()

        # Activate Debugger breakpoints
        for event_name in INTERACTION_BREAKPOINTS:
            await self.target.DOMDebugger.setEventListenerBreakpoint(eventName=event_name)

        return

        while True:
            if loaded:
                logger.info("Page loaded, extracting info..")
                target_info = await self.target.Target.getTargetInfo()
                url = target_info["targetInfo"]["url"]
                url_parsed = urlparse(url)
                if not self.start_url_netloc == url_parsed.netloc:
                    logger.info("Site exited, ending scan..")
                    break
                await self.__extract_information(url, self._user_interaction_reason)
            else:
                logger.info("no further content was loaded, contining")
            logger.info('waiting for next input...')
            self._request_will_be_sent.clear()
            self._user_interaction.clear()
            await self.target.Input.setIgnoreInputEvents(ignore=False)
            self._response_log.clear()
            if not await utils.event_wait(self._user_interaction, 10):
                logger.info("no further input, exiting")
                break
            await self.target.Input.setIgnoreInputEvents(ignore=True)
            loaded = await self.__await_page_load()
        await self.target.close()

    async def __set_page_loaded(self, **kwargs):
        self._page_loaded.set()

    async def __set_request_will_be_sent(self, **kwargs):
        self._user_interaction_reason = "request_will_be_sent"
        self._user_interaction.set()

    async def __response_received(self, response, **kwargs):
        self._response_log.append(response)

    async def __backgroundServiceEventReceived(self, backgroundServiceEvent, **kwargs):
        logger.info("Background service Event")

    async def __debugger_paused(self, reason, data, **kwargs):
        logger.info("Debugger Paused, reason: %s, data: %s" % (reason, data))
        await self.target.Debugger.resume()
        self.debugger_paused = True
        if reason == "EventListener":
            event_name = data["eventName"]
            event_name = event_name[len("listener:"):]
            if event_name in INTERACTION_BREAKPOINTS:
                self._user_interaction_reason = event_name
                self._user_interaction.set()
                return
        # logger.info("EROOR: %s", reason)
        # self.debugger_paused = False
        # logger.info("Debugger resumed")

    async def scroll_down_up(self):
        layout = await self.target.Page.getLayoutMetrics()
        height = layout['contentSize']['height']
        logger.info(height)
        viewport_height = layout['visualViewport']['clientHeight']
        viewport_width = layout['visualViewport']['clientWidth']
        x = random.randint(0, viewport_width - 1)
        y = random.randint(0, viewport_height - 1)
        await self.target.Input.setIgnoreInputEvents(ignore=False)
        await self.target.Input.dispatchMouseEvent(
            type="mouseWheel", x=x, y=y, deltaX=0, deltaY=height)
        await asyncio.sleep(0.5)
        await self.target.Input.dispatchMouseEvent(
            type="mouseWheel", x=10, y=10, deltaX=0, deltaY=-height)
        await self.target.Input.setIgnoreInputEvents(ignore=True)

    async def register_callbacks(self):
        # Enable domain notifications
        await self.target.Network.enable()
        await self.target.Page.enable()
        await self.target.DOM.enable()
        await self.target.Security.enable()
        await self.target.Debugger.enable()
        await self.target.Runtime.enable()

        # Enable callbacks
        self.target.register_event(
            "Network.loadingFinished", self.__set_page_loaded)
        self.target.register_event(
            "Network.requestWillBeSent", self.__set_request_will_be_sent)
        self.target.register_event(
            "Network.responseReceived", self.__response_received)
        self.target.register_event(
            "Debugger.paused", self.__debugger_paused)
        self.target.register_event(
            "BackgroundService.backgroundServiceEventReceived", self.__backgroundServiceEventReceived)

    async def __await_page_load(self):
        logger.info("awaiting page load")
        loaded = await utils.event_wait(self._page_loaded, 0.5)
        if not loaded:
            logger.info("no update was made, continuing")
            return loaded
        for _ in range(6):
            await asyncio.sleep(1)
            self._page_loaded.clear()
            loaded = await utils.event_wait(self._page_loaded, 2)
            if not loaded:
                return True
        logger.info("ERROR: TIMEOUT on load")

    async def __extract_information(self, url, reason):
        intermediate_result = {"url": url, "event": reason}
        for extractor_class in EXTRACTOR_CLASSES:
            self._extractors.append(extractor_class(
                self.target, intermediate_result, logger, self.options))

        for extractor in self._extractors:
            await extractor.extract_information()
        self.result["interaction"].append(intermediate_result)
