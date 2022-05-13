import asyncio
import json
import logging
from threading import Thread
from urllib.parse import urlparse

import janus

import podman_container
import result
from browser2 import Browser
from chromedev.extractors import CookiesExtractor, RequestsExtractor, ResponsesExtractor
from errors import ScannerInitError, ScannerError
from scanner_messages import ScannerMessage, MessageType

EXTRACTOR_CLASSES = [CookiesExtractor, RequestsExtractor, ResponsesExtractor]

logger = logging.getLogger('scanner')


class InteractiveScanner(Thread):
    def __init__(self, url, debugging_port, container_id, options):
        super().__init__()
        # Mark this thread as daemon
        self.daemon = True

        self.logger = logging.getLogger('cdp_controller_%s' % self.name)

        # Init Message Queue
        self.event_loop = asyncio.new_event_loop()
        init_queue_task = self.event_loop.create_task(self._init_queue())
        self.event_loop.run_until_complete(init_queue_task)

        # Set socket
        self.client_socket = None

        # Init Scanner
        self.url = url
        self.start_url_netloc = urlparse(url).netloc
        self.options = options
        self.debugging_port = debugging_port
        self.container_id = container_id
        self.result = result.init_from_scanner(url)
        self._extractors = []
        self._request_will_be_sent = asyncio.Event()
        self.stop_scan_event = asyncio.Event()
        self.page = Page()

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
        har_path = self.result.get_har_path()
        async with Browser(debugging_port=self.debugging_port, har_location=har_path) as browser:
            self.browser = browser
            while True:
                self.logger.info("Waiting for scanner message.")
                message = await self._queue.async_q.get()
                try:
                    rec_poison_pill = await self._process_message(message)
                    if rec_poison_pill:
                        self.logger.info('Scan complete, terminating thread.')
                        return
                except ScannerError as e:
                    self.logger.error(str(e))
                    continue

    async def _process_message(self, message):
        self.logger.info('processing message %s' % str(message))
        match message:
            case ScannerMessage(message_type=MessageType.StartScan):
                await self._start_scan()
            case ScannerMessage(message_type=MessageType.RegisterInteraction):
                await self._register_interaction()
            case ScannerMessage(message_type=MessageType.ClearCookies):
                await self._clear_cookies()
            case ScannerMessage(message_type=MessageType.TakeScreenshot):
                await self._take_screenshot()
            case ScannerMessage(message_type=MessageType.StopScan):
                await self._stop_scan()
                return True
            case unknown_command:
                raise ScannerError(
                    f"Unknown command '{unknown_command}' ignored.")
        return False

    # Socket Communication

    def set_socket(self, socket):
        self.client_socket = socket

    def send_socket_msg(self, msg):
        msg_json = json.dumps(msg)
        if self.client_socket == None:
            logger.error('Client socket not set up, ignoring message:' + msg_json)
            return
        else:
            logger.info('sending message' + msg_json)
            self.client_socket.send(msg_json)

    # Scanner Functions

    async def _start_scan(self):
        """
        Create new target and navigate to page
        """
        await self._register_callbacks()
        await self.browser.ignore_inputs(True)
        await self._navigate_to_page()
        #        if not loaded:
        #            raise ScannerError("Initial page is not loaded.")
        await self._record_information('initial scan')
        await self.browser.ignore_inputs(False)
        self.send_socket_msg({"ScanComplete": ""})

    async def _navigate_to_page(self):
        self.logger.info("Navigating to Start URL.")
        await self.browser.navigate_url(self.url)
        await self.browser.await_page_load()
        await self.browser.cpd_send_message("BackgroundService.startObserving", service="backgroundFetch")

    async def _record_information(self, reason):
        target_info = await self.browser.cpd_send_message('Target.getTargetInfo')
        url = target_info["targetInfo"]["url"]
        url_parsed = urlparse(url)
        if not self.start_url_netloc == url_parsed.netloc:
            self.logger.info("Site exited or forwarded..")

        intermediate_result = {"url": url, "event": reason}
        self._extractors.clear()
        for extractor_class in EXTRACTOR_CLASSES:
            self._extractors.append(extractor_class(
                self.browser,
                self.page,
                self.options
            ))

        for extractor in self._extractors:
            extractor_info = await extractor.extract_information()
            # append result
            intermediate_result = intermediate_result | extractor_info.copy()
        self.page = Page()
        self.result["interaction"].append(intermediate_result.copy())

    async def _register_interaction(self):
        await self.browser.ignore_inputs(True)
        await self._record_information('manual interaction')
        await self.browser.ignore_inputs(False)
        self.send_socket_msg({"ScanComplete": ""})

    async def _stop_scan(self):
        await self.browser.ignore_inputs(True)
        await self._record_information('end scan')
        self.result.store_result()
        podman_container.stop_container(self.container_id)
        self.send_socket_msg({"ScanComplete": ""})

    async def _clear_cookies(self):
        await self.browser.clear_cookies()
        self.send_socket_msg({"Log": "Cookies deleted"})

    # Callback Functions

    async def _set_frame_navigated(self, frame, **kwargs):
        if frame['url'] != 'about:blank':
            self.send_socket_msg({"URLChanged": frame['url']})

    async def _set_request_will_be_sent(self, requestId, request, **kwargs):
        request['request_id'] = requestId
        self.page.add_request(request)

    async def _request_served_from_cache(self, **kwargs):
        pass  # ignored for now

    async def _response_received(self, response, requestId, **kwargs):
        response['request_id'] = requestId
        self.page.add_response(response)

    async def _backgroundServiceEventReceived(self, backgroundServiceEvent, **kwargs):
        # ignored for now
        self.logger.info("Background service Event")

    async def _mouseEventReceived(self, **kwargs):
        self.send_socket_msg({'Mouse Event': ""})

    # Callback Definition

    async def _register_callbacks(self):
        """
        Register domain notifications and callbacks
        """
        await self.browser.cpd_send_message('Network.enable')
        await self.browser.cpd_send_message('Page.enable')
        await self.browser.cpd_send_message('DOM.enable')
        await self.browser.cpd_send_message('Security.enable')
        await self.browser.cpd_send_message('Debugger.enable')
        await self.browser.cpd_send_message('Runtime.enable')

        # Enable callbacks
        self.browser.register_event("Page.frameNavigated", self._set_frame_navigated)
        self.browser.register_event("Network.requestWillBeSent", self._set_request_will_be_sent)
        self.browser.register_event("Network.requestServedFromCache", self._request_served_from_cache)
        self.browser.register_event("Network.responseReceived", self._response_received)
        self.browser.register_event("BackgroundService.backgroundServiceEventReceived",
                                    self._backgroundServiceEventReceived)


class Page:
    def __init__(self):
        self.request_log = []
        self.failed_request_log = []
        self.response_log = []

    def add_request(self, request):
        self.request_log.append(request)

    def add_failed_request(self, request):
        self.failed_request_log.append(request)

    def add_response(self, response):
        self.response_log.append(response)
        # for r in self.request_log:
        #    if r['id'] == requestId:
        #        if not r['responses']:
        #            r['responses'] = list()
        #        r['responses'].append(response)
