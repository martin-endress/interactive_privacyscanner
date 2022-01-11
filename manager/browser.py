import shutil
import subprocess
import tempfile
import json
import asyncio

from chromedev import Browser
from pathlib import Path


# See https://github.com/GoogleChrome/chrome-launcher/blob/master/docs/chrome-flags-for-tools.md
# and https://peter.sh/experiments/chromium-command-line-switches/
CHROME_OPTIONS = [
    "--disable-background-networking",
    "--disable-sync",
    "--metrics-recording-only",
    "--disable-default-apps",
    "--mute-audio",
    "--no-first-run",
    "--disable-background-timer-throttling",
    "--disable-client-side-phishing-detection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--enable-automation",
    "--password-store=basic",
    "--use-mock-keychain",
    "--disable-component-update",
    "--autoplay-policy=no-user-gesture-required",
    "--disable-notifications",
    "--disable-hang-monitor"
    # Allows running insecure content (HTTP content on HTTPS sites)
    # TODO: Discuss if we want this (might include more cookies etc.)
    # '--allow-running-insecure-content',
]


PREFS = {
    "profile": {
        "content_settings": {
            "exceptions": {
                # Allow flash for all sites
                "plugins": {"http://*,*": {"setting": 1}, "https://*,*": {"setting": 1}}
            }
        }
    },
    "session": {
        "restore_on_startup": 4,  # 4 = Use startup_urls
        "startup_urls": ["about:blank"],
    },
}


class ChromeBrowserStartupError(Exception):
    pass


class ChromeBrowser:
    def __init__(self, debugging_port=9222, chrome_executable=None):
        self._debugging_port = debugging_port
        self._browser_ip = "localhost"
        if chrome_executable is None:
            self._chrome_executable = find_chrome_executable()

    async def __aenter__(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        temp_dirname = self._temp_dir.name
        user_data_dir = Path(temp_dirname) / "chrome-profile"
        user_data_dir.mkdir()
        default_dir = user_data_dir / "Default"
        default_dir.mkdir()
        with (default_dir / "Preferences").open("w") as f:
            json.dump(PREFS, f)
        return await self._start_chrome(user_data_dir)

    async def _start_chrome(self, user_data_dir):
        extra_opts = [
            "--remote-debugging-port={}".format(self._debugging_port),
            "--user-data-dir={}".format(user_data_dir),
        ]
        command = [self._chrome_executable] + CHROME_OPTIONS + extra_opts
        self._p = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        self.browser = Browser(
            debugger_url="http://{}:{}".format(self._browser_ip, self._debugging_port),
            debug=True,
        )
        await self.browser.start()
        return self.browser

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser.close()
        self._temp_dir.cleanup()


def find_chrome_executable():
    chrome_executable = shutil.which("google-chrome")
    if chrome_executable is None:
        macos_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if Path(macos_chrome).exists():
            chrome_executable = macos_chrome
    if chrome_executable is None:
        chrome_executable = shutil.which("chromium")
    if chrome_executable is None:
        chrome_executable = shutil.which("chromium-browser")
    if chrome_executable is None:
        raise ChromeBrowserStartupError("Could not find google-chrome or chromium.")
    return chrome_executable
