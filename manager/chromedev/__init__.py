import asyncio
import logging
import os
import sys
from collections import defaultdict

import aiohttp
import websockets

logger = logging.getLogger('chrome_devtools_api')

try:
    import orjson as json

    is_orjson = True
except ImportError:
    is_orjson = False
    import json


class MethodCallError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


class ConnectionError(Exception):
    pass


class MethodCallProxy:
    __slots__ = ("_name", "_browser", "_session_id")

    def __init__(self, name, browser, session_id):
        self._name = name
        self._browser = browser
        self._session_id = session_id

    def __call__(self, *args, **kwargs):
        if args:
            raise TypeError(
                "%s must be called with keyword arguments." % self._name)
        return self._browser.call_method(self._name, kwargs, self._session_id)

    def register(self, callback):
        self._browser.register_event(self._name, callback, self._session_id)

    def unregister(self, callback=None):
        self._browser.unregister_event(self._name, callback, self._session_id)


class MethodGroupProxy:
    def __init__(self, group_name, browser, session_id=None):
        self._group_name = group_name
        self._browser = browser
        self._session_id = session_id

    def __getattr__(self, func_name):
        method_name = "%s.%s" % (self._group_name, func_name)
        proxy = MethodCallProxy(method_name, self._browser, self._session_id)
        self.__dict__[func_name] = proxy
        return proxy


class _SessionStore:
    def __init__(self):
        self.results = {}
        self.event_callbacks = defaultdict(list)


class Session:
    def __init__(self, session_id, browser):
        self._session_id = session_id
        self._browser = browser

    async def call_method(self, method_name, params=None, **kwargs):
        return await self._browser.call_method(
            method_name, params, self._session_id, **kwargs
        )

    def register_event(self, event_name, callback):
        return self._browser.register_event(event_name, callback, self._session_id)

    def unregister_event(self, event_name, callback):
        return self._browser.unregister_event(event_name, callback, self._session_id)

    def __getattr__(self, name: str):
        if not name.istitle():
            logger.warning("\"" + name + "\"is not a title, using it anyways...")
        proxy = MethodGroupProxy(name, self._browser, self._session_id)
        self.__dict__[name] = proxy
        return proxy


class Target(Session):
    def __init__(self, session_id, target_id, browser):
        super().__init__(session_id, browser)
        self._target_id = target_id

    async def close(self):
        return await self.Target.closeTarget(targetId=self._target_id)


class Browser:
    def __init__(self, debugger_url, debug=None):
        loop = asyncio.get_event_loop()
        if debug is None:
            debug = os.environ.get("DEBUG") == "1"
        self._debugger_url = debugger_url
        self._loop = loop
        self._debug = debug
        self._websocket_debugger_url = None
        self._conn = None
        self._recv_task = None
        self._id_counter = 0
        self._results = {}
        self._event_callbacks = defaultdict(list)
        self._failed_events = []

    async def _await_browser(self, timeout=5):
        logger.info('awaiting browser')
        await asyncio.sleep(3)

    async def start(self, timeout=None):
        await self._await_browser()
        url = "%s/json/version" % self._debugger_url
        logger.info('connecting to websocket %s' % url)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    info = await response.json()
                    logger.info('debugger URL: %s' % info)
            except aiohttp.ClientConnectionError as e:
                raise ConnectionError(e)
            else:
                self._websocket_debugger_url = info["webSocketDebuggerUrl"]
        self._conn = await websockets.connect(self._websocket_debugger_url, ping_interval=None, ping_timeout=None)
        if self._debug:
            logger.info("! Websocket connected")
        self._recv_task = self._loop.create_task(self._recv_loop())

    async def _send_raw(self, json_msg):
        if self._debug:
            logger.info("> %s" % json_msg)
        msg = json.dumps(json_msg).decode() if is_orjson else json.dumps(json_msg)
        await self._conn.send(msg)

    async def call_method(self, method_name, params=None, session_id=None):
        self._id_counter += 1
        msg_id = self._id_counter
        self._results[msg_id] = self._loop.create_future()
        msg = {"method": method_name, "params": params, "id": msg_id}
        if session_id is not None:
            msg["sessionId"] = session_id
        await self._send_raw(msg)
        try:
            return await self._results[msg_id]
        finally:
            del self._results[msg_id]

    def register_event(self, event_name, callback, session_id=None):
        self._event_callbacks[(session_id, event_name)].append(callback)

    def unregister_event(self, event_name, callback=None, session_id=None):
        callbacks = self._event_callbacks[(session_id, event_name)]
        if callback is None:
            callbacks[event_name].clear()
        else:
            callbacks[event_name].remove(callback)

    async def _recv_loop(self):
        while True:
            try:
                msg = json.loads(await self._conn.recv())
            except websockets.ConnectionClosed:
                if self._debug:
                    logger.info("! Closed websocket connection.")
                break
            if self._debug:
                if "sessionId" in msg and \
                        "method" in msg and \
                        msg["method"] not in ["Debugger.paused", "Inspector.detached"]:
                    logger.info("< method: %s, sessionId: %s" % (msg["method"], msg["sessionId"]))
                else:
                    logger.info("< %s" % msg)
            if "id" in msg:
                future = self._results[msg["id"]]
                if "error" in msg:
                    error = msg["error"]
                    message = "%s: %s" % (msg["message"], msg["data"])
                    exc = MethodCallError(message, error["code"])
                    future.set_exception(exc)
                else:
                    future.set_result(msg["result"])
            else:
                session_id = msg.get("sessionId")
                event_index = (session_id, msg["method"])
                if event_index in self._event_callbacks:
                    for callback in self._event_callbacks[event_index]:
                        task = self._loop.create_task(
                            callback(**msg["params"]))
                        task.add_done_callback(self._event_callback_done)
        await self._conn.close()

    def _event_callback_done(self, task):
        if task.exception() is not None:
            self._failed_events.append(task)
            task.print_stack(file=sys.stderr)

    async def close(self):
        await self._conn.close()
        await self._recv_task

    def get_session(self, session_id):
        return Session(session_id, self)

    async def new_target(self, url="about:blank"):
        target = await self.Target.createTarget(url=url)
        session = await self.Target.attachToTarget(
            targetId=target["targetId"],
            flatten=True,
        )
        return Target(session["sessionId"], target["targetId"], self)

    def get_failed_events(self):
        return self._failed_events

    def __getattr__(self, name: str):
        if not name.istitle():
            raise AttributeError(
                "%s object has no attribute %r" % (
                    self.__class__.__name__, name)
            )
        proxy = MethodGroupProxy(name, self)
        self.__dict__[name] = proxy
        return proxy

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
