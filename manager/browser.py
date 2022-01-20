from chromedev import Browser


class ChromeBrowser:
    def __init__(self, debugging_port=9222):
        self._debugging_port = debugging_port
        self._browser_ip = "localhost"

    async def __aenter__(self):
        self.browser = Browser(
            debugger_url="http://{}:{}".format(self._browser_ip, self._debugging_port),
            debug=True,
        )
        await self.browser.start()
        return self.browser

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser.close()
