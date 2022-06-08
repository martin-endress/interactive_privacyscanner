import asyncio
import json
import time
from threading import Thread
from urllib.parse import urlparse

import janus

import logs
import podman_container
import result
from browser import Browser
from errors import ScannerInitError, ScannerError
from extractors import CookiesExtractor, RequestsExtractor, ResponsesExtractor
from result import Result, ResultKey
from scanner_messages import ScannerMessage, MessageType

EXTRACTOR_CLASSES = [CookiesExtractor, RequestsExtractor, ResponsesExtractor]
SCANNER_KEY = 'SCANNER_INTERACTION'

logger = logs.get_logger('scanner')


class InteractiveScanner(Thread):
    def __init__(self, url, debugging_port, container_id, options, socket, reference_scan_id=None):
        super().__init__()
        # Mark this thread as daemon
        self.daemon = True

        self.logger = logs.get_logger('cdp_controller_%s' % self.name)

        # Init Message Queue
        self.event_loop = asyncio.new_event_loop()
        init_queue_task = self.event_loop.create_task(self._init_queue())
        self.event_loop.run_until_complete(init_queue_task)

        # Set socket
        self.client_socket = socket

        # Init Scanner
        self.url = url
        self.start_url_netloc = urlparse(url).netloc
        self.initial_scan = reference_scan_id is None
        self.result = self._init_result() if self.initial_scan else self._load_result(reference_scan_id)
        self.debugging_port = debugging_port
        self.container_id = container_id
        self.options = options
        self._extractors = []
        self._page = Page()

    def _init_result(self):
        site_parsed = urlparse(self.url)
        if site_parsed.scheme not in ("http", "https"):
            raise ScannerInitError("Invalid site url: {}".format(self.url))
        result_json = {ResultKey.SITE_URL: self.url, ResultKey.INTERACTION: []}
        result_id = result.get_result_id(site_parsed.netloc)
        return Result(result_json, result_id, self.initial_scan)

    def _load_result(self, reference_scan_id):
        result_json = {ResultKey.SITE_URL: self.url, ResultKey.INTERACTION: []}
        return Result(result_json, reference_scan_id, self.initial_scan)

    async def _init_queue(self):
        self._queue = janus.Queue()

    def run(self):
        self.event_loop.run_until_complete(self._start_scanner())
        self.event_loop.close()

    def put_msg(self, msg):
        logger.debug(f'Scanner message {msg} added to Queue.')
        if not isinstance(msg, ScannerMessage):
            raise ScannerError('Element is not a Scanner Message.')
        if self._queue is None:
            raise ScannerInitError('Queue not correctly initialized.')
        self._queue.sync_q.put(msg)

    async def _start_scanner(self):
        files_path = self.result.get_files_path()
        async with Browser(self.debugging_port, files_path) as browser:
            self.browser = browser
            while True:
                self.logger.info("Waiting for scanner message.")
                message = await self._queue.async_q.get()
                try:
                    rec_poison_pill = await self._process_message(message)
                    if rec_poison_pill:
                        self.logger.info('Scan complete, terminating thread.')
                        break
                except ScannerError as e:
                    error_msg = str(e)
                    self.logger.error(error_msg)
                    self.result[ResultKey.ERROR] = error_msg
                    self.result.store_result()
                    break
        # Stop container after disconnecting from browser
        podman_container.stop_container(self.container_id)
        self.send_socket_msg({"ScanComplete": ""})

    async def _process_message(self, message):
        self.logger.info(f'processing message {message}')
        match message:
            case ScannerMessage(message_type=MessageType.StartScan):
                await self._start_scan()
            case ScannerMessage(message_type=MessageType.RegisterInteraction):
                await self._register_interaction()
            case ScannerMessage(message_type=MessageType.ClearCookies):
                await self._clear_cookies()
            case ScannerMessage(message_type=MessageType.TakeScreenshot):
                await self._take_screenshot()
            case ScannerMessage(message_type=MessageType.PerformUserInteraction):
                await self._perform_user_interaction(message.content)
            case ScannerMessage(message_type=MessageType.StopScan):
                await self._stop_scan(message.content)
                # send poison pill
                return True
            case unknown_command:
                raise ScannerError(f"Unknown command '{unknown_command}' ignored.")
        return False

    # Socket Communication

    def send_socket_msg(self, msg):
        msg_json = json.dumps(msg)
        if self.client_socket is None:
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
        await self._record_information(ResultKey.INITIAL_SCAN)
        await self.browser.ignore_inputs(False)
        self.send_socket_msg({"ScanComplete": ""})

    async def _navigate_to_page(self):
        self.logger.info("Navigating to Start URL.")
        await self.browser.navigate_url(self.url)
        await self.browser.cpd_send_message("BackgroundService.startObserving", service="backgroundFetch")

    async def _record_information(self, reason):
        target_info = await self.browser.cpd_send_message('Target.getTargetInfo')
        url = target_info["targetInfo"]["url"]
        url_parsed = urlparse(url)
        if not self.start_url_netloc == url_parsed.netloc:
            self.logger.info("Site exited or forwarded..")

        intermediate_result = {ResultKey.URL: url, ResultKey.EVENT: reason, ResultKey.TIMESTAMP: self._page.scan_time,
                               ResultKey.SCREENSHOTS: self._page.screenshots,
                               ResultKey.USER_INTERACTION: self._page.user_interaction}
        self._extractors.clear()
        for extractor_class in EXTRACTOR_CLASSES:
            self._extractors.append(extractor_class(self.browser, self._page, self.options))

        for extractor in self._extractors:
            extractor_info = await extractor.extract_information()
            # append result
            intermediate_result = intermediate_result | extractor_info.copy()
        self._page = Page()
        self.result[ResultKey.INTERACTION].append(intermediate_result.copy())

    async def _perform_user_interaction(self, user_interaction):
        if self.initial_scan:
            logger.error('Illegal State. Recorded interactions only available in replay mode.')
        else:
            await self.browser.perform_user_interaction(user_interaction)

    async def _register_interaction(self):
        await self.browser.ignore_inputs(True)
        await self._record_information(ResultKey.MANUAL_INTERACTION)
        await self.browser.ignore_inputs(False)
        self.send_socket_msg({"ScanComplete": ""})

    async def _clear_cookies(self):
        await self.browser.ignore_inputs(True)
        await self._record_information(ResultKey.DELETE_COOKIES)
        await self.browser.clear_cookies()
        await self.browser.ignore_inputs(False)
        self.send_socket_msg({"ScanComplete": ""})
        self.send_socket_msg({"Log": "Cookies deleted."})

    async def _take_screenshot(self):
        path = self.result.get_files_path() / f'screenshot_{self.result.num_screenshots}.jpeg'
        self._page.add_screenshot_path(path)
        await self.browser.take_screenshot(path)
        self.result.num_screenshots += 1
        self.send_socket_msg({"Log": "Screenshot saved."})

    async def _stop_scan(self, note):
        await self.browser.ignore_inputs(True)
        await self._record_information(ResultKey.END_SCAN)
        self.result.store_result(note=note)

    # Callback Functions

    async def _request_sent(self, request):
        self._page.add_request(request)

    async def _response_received(self, response):
        self._page.add_response(response)

    async def _frame_navigated(self, frame):
        logger.debug(frame)
        frame = frame['frame']
        logger.debug(f"Frame navigated. (type: {frame['type']})")
        if frame['url'] != 'about:blank':
            url = urlparse(frame['url'])
            url_str = f"{url.scheme}://{url.netloc}/..."
            self.send_socket_msg({"URLChanged": url_str})

    async def _console_msg_received(self, console_message):
        msg_text = console_message.text
        if msg_text.startswith(SCANNER_KEY):
            interaction_json = json.loads(msg_text[len(SCANNER_KEY):])
            self._page.add_interaction(interaction_json)
        else:
            logger.debug('console message: ' + msg_text)
            pass  # ignore other messages

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
        self.browser.register_page_event("request", self._request_sent)
        self.browser.register_page_event("response", self._response_received)
        # self.browser.register_page_event("framenavigated", self._frame_navigated)
        self.browser.register_page_event("console", self._console_msg_received)


class Page:
    def __init__(self):
        self.scan_time = int(time.time())
        self.request_log = []
        self.failed_request_log = []
        self.response_log = []
        self.screenshots = []
        self.user_interaction = []

    def add_request(self, request):
        self.request_log.append(request)

    def add_failed_request(self, request):
        self.failed_request_log.append(request)

    def add_response(self, response):
        self.response_log.append(response)

        # for r in self.request_log:  #    if r['id'] == requestId:  #        if not r['responses']:  #            r['responses'] = list()  #        r['responses'].append(response)

    def add_screenshot_path(self, path):
        self.screenshots.append(str(path))

    def add_interaction(self, interaction):
        self.user_interaction.append(interaction)
