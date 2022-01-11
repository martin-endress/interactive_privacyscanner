import asyncio
import json
import random
import janus

from threading import Thread
from datetime import datetime
from result import Result
from pathlib import Path
from urllib.parse import urlparse

from scanner_messages import ScannerMessage, MessageType
from utils import slugify, DirectoryFileHandler, event_wait
from browser import ChromeBrowser
from chromedev.extractors import CookiesExtractor

EXTRACTOR_CLASSES = [CookiesExtractor]


class ScannerInitError(ValueError):
    pass


class ScannerError(ValueError):
    pass


def format_result_folder(netloc):
    results_dir = slugify(netloc) + "_"
    now = datetime.now()
    results_dir += now.strftime("%y-%m-%d_%H-%M")
    return results_dir


class UserInteraction:
    def __init__(self):
        self._user_interaction = asyncio.Event()


class InteractiveScanner(Thread):
    # , url, logger, options, debugging_port=9222):
    def __init__(self, url, debugging_port):
        super().__init__()
        self.daemon = True
        self.event_loop = asyncio.new_event_loop()
        init_queue_task = self.event_loop.create_task(self._init_queue())
        self.event_loop.run_until_complete(init_queue_task)
        self.url = url
        # self.logger = logger
        # self.options = options
        self.debugging_port = debugging_port
        # self.init_result(options)
        # self._extractor_classes = EXTRACTOR_CLASSES
        # self._extractors = []
        # self._loop = asyncio.get_event_loop()
        # self._page_loaded = asyncio.Event()
        # self._request_will_be_sent = asyncio.Event()
        # self._response_log = []
        # self._user_interaction = asyncio.Event()
        # self.user_interaction_breakpoints = ["focus", "click", "mouseWheel"]

    async def _init_queue(self):
        self._queue = janus.Queue()

    def run(self):
        self.event_loop.run_until_complete(self._start_scanner())
        self.event_loop.close()

    def put_msg(self, msg):
        if not isinstance(msg, ScannerMessage):
            raise ScannerError('Element is not a Scanner Message.')
        if self._queue is None:
            raise ScannerInitError('Queue not correctly initialized.')
        self._queue.sync_q.put(msg)

    async def _start_scanner(self):
        while True:
            message = await self._queue.async_q.get()
            match message:
                case ScannerMessage(message_type=MessageType.StartScan):
                    print("starting scan of site%s" % message.content)
                    await asyncio.sleep(2)
                case ScannerMessage(message_type=MessageType.StopScan):
                    print('stopping scan')
                    break
                case unknown_command:
                    print(f"Unknown command '{unknown_command}' ignored.")
        return
        async with ChromeBrowser(debugging_port=self.debugging_port) as browser:
            await browser.Target.setAutoAttach(
                autoAttach=True, waitForDebuggerOnStart=False, flatten=True
            )

            self.target = await browser.new_target()

            # Register domain notifications and callbacks
            await self.register_callbacks()

            # Navigate to url
            await self.target.Input.setIgnoreInputEvents(ignore=True)
            await self.target.Page.navigate(url=self.url)

            await self.target.BackgroundService.startObserving(service="backgroundFetch")

            loaded = await self._await_page_load()
            await self.scroll_down_up()
            await self._await_page_load()

            # Activate Debugger breakpoints
            for event_name in self.user_interaction_breakpoints:
                await self.target.DOMDebugger.setEventListenerBreakpoint(eventName=event_name)

            while True:
                if loaded:
                    print("Page loaded, extracting info..")
                    target_info = await self.target.Target.getTargetInfo()
                    url = target_info["targetInfo"]["url"]
                    url_parsed = urlparse(url)
                    if not self.start_url_netloc == url_parsed.netloc:
                        print("Site exited, ending scan..")
                        break
                    await self._extract_information(url, self._user_interaction_reason)
                else:
                    print("no further content was loaded, contining")
                print('waiting for next input...')
                self._request_will_be_sent.clear()
                self._user_interaction.clear()
                await self.target.Input.setIgnoreInputEvents(ignore=False)
                self._response_log.clear()
                if not await event_wait(self._user_interaction, 10):
                    print("no further input, exiting")
                    break
                await self.target.Input.setIgnoreInputEvents(ignore=True)
                loaded = await self._await_page_load()
            await self.target.close()

    def init_result(self, options):
        site_parsed = urlparse(self.url)
        self.start_url_netloc = site_parsed.netloc
        if site_parsed.scheme not in ("http", "https"):
            raise ScannerInitError("Invalid site url: {}".format(self.url))
        # TODO add ability to override this in options
        results_dir = None
        if results_dir is None:
            results_dir = format_result_folder(site_parsed.netloc)
        results_dir = (Path("results") / results_dir).resolve()
        if results_dir.exists() or results_dir.is_file():
            raise ScannerInitError("Folder already exists." + str(results_dir))
        try:
            results_dir.mkdir(parents=True)
        except IOError as e:
            raise ScannerInitError(
                "Could not create results directory: {}".format(e)
            ) from e

        self.result_file = results_dir / "results.json"
        result_json = {"site_url": self.url,
                       #   "scan_start": datetime.utcnow(),
                       "interaction": []}
        try:
            with self.result_file.open("w") as f:
                json.dump(result_json, f, indent=2)
                f.write("\n")
        except IOError as e:
            raise ScannerInitError(
                "Could not write result JSON: {}".format(e)) from e

        self.result = Result(result_json, DirectoryFileHandler(results_dir))

    async def _set_page_loaded(self, **kwargs):
        self._page_loaded.set()

    async def _set_request_will_be_sent(self, **kwargs):
        self._user_interaction_reason = "request_will_be_sent"
        self._user_interaction.set()

    async def _response_received(self, response, **kwargs):
        self._response_log.append(response)

    async def _backgroundServiceEventReceived(self, backgroundServiceEvent, **kwargs):
        print("Background service Event")

    async def _debugger_paused(self, reason, data, **kwargs):
        print("Debugger Paused, reason: %s, data: %s" % (reason, data))
        await self.target.Debugger.resume()
        self.debugger_paused = True
        if reason == "EventListener":
            event_name = data["eventName"]
            event_name = event_name[len("listener:"):]
            if event_name in self.user_interaction_breakpoints:
                self._user_interaction_reason = event_name
                self._user_interaction.set()
                return
        # print("EROOR: %s", reason)
        # self.debugger_paused = False
        # print("Debugger resumed")

    async def scroll_down_up(self):
        layout = await self.target.Page.getLayoutMetrics()
        height = layout['contentSize']['height']
        print(height)
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
            "Network.loadingFinished", self._set_page_loaded)
        self.target.register_event(
            "Network.requestWillBeSent", self._set_request_will_be_sent)
        self.target.register_event(
            "Network.responseReceived", self._response_received)
        self.target.register_event(
            "Debugger.paused", self._debugger_paused)
        self.target.register_event(
            "BackgroundService.backgroundServiceEventReceived", self._backgroundServiceEventReceived)

    async def _await_page_load(self):
        print("awaiting page load")
        loaded = await event_wait(self._page_loaded, 0.5)
        if not loaded:
            print("no update was made, continuing")
            return loaded
        for _ in range(6):
            await asyncio.sleep(1)
            self._page_loaded.clear()
            loaded = await event_wait(self._page_loaded, 2)
            if not loaded:
                return True
        print("ERROR: TIMEOUT on load")

    async def _extract_information(self, url, reason):
        intermediate_result = {"url": url, "event": reason}
        for extractor_class in self._extractor_classes:
            self._extractors.append(extractor_class(
                self.target, intermediate_result, self.logger, self.options))

        for extractor in self._extractors:
            await extractor.extract_information()
        self.result["interaction"].append(intermediate_result)

    def store_result(self):
        try:
            with self.result_file.open("w") as f:
                json.dump(self.result.get_results(),
                          f, indent=2, sort_keys=True)
                f.write("\n")
        except IOError as e:
            raise ScannerInitError(
                "Could not write result JSON: {}".format(e)) from e
