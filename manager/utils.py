import asyncio
import base64
import hashlib
import hmac
import secrets
import json
import string
from contextlib import suppress
from pathlib import Path


class DirectoryFileHandler:
    def __init__(self, result_dir):
        result_dir = Path(result_dir).absolute()
        self._files_dir = result_dir / 'files'
        self._debug_files_dir = result_dir / 'debug_files'
        self._files_dir.mkdir(parents=True)
        self._debug_files_dir.mkdir(parents=True)

    def get_files_path(self):
        return self._files_dir

    def add_file(self, filename, contents, debug):
        output_dir = self._debug_files_dir if debug else self._files_dir
        with (output_dir / filename).open('wb') as f:
            f.write(contents)

    def add_image(self, filename, contents, debug):
        output_dir = self._files_dir
        with (self._files_dir / filename).open("wb") as f:
            f.write(base64.urlsafe_b64decode(contents))


class NoOpFileHandler:
    def add_file(self, filename, contents, debug):
        pass


def slugify(somestr):
    allowed_chars = string.ascii_lowercase + string.digits + '.-'
    return ''.join(x for x in somestr.lower() if x in allowed_chars)


class SessionManager:
    def __init__(self):
        # api session master key
        self.api_master_key = secrets.token_hex().encode()
        self.sessions = dict()

    def create_session(self, container_id, vnc_port):
        m = container_id + str(vnc_port).encode()
        h = hmac.new(self.api_master_key, m, hashlib.sha256).hexdigest()
        self.sessions[h] = {'c_id': container_id, 'vnc_port': vnc_port}
        return h

    def get_session(self, session_key):
        if session_key in self.sessions:
            return self.sessions[session_key]
        else:
            raise ValueError('Invalid session key.')


async def event_wait(evt, timeout):
    """
    see https://stackoverflow.com/questions/49622924/wait-for-timeout-or-event-being-set-for-asyncio-event

    suppress TimeoutError because we'll return False in case of timeout
    """
    with suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


def extend_result():
    path = Path("/home/martin/git/interactive_privacyscanner/study/data/")
    for f in path.iterdir():
        print(f'node app {f / "first_scan/analysis_before"}')
        print(f'node app {f / "first_scan/analysis_after"}')


def translate_result(path):
    scan_path = path / "first_scan"
    result_file = scan_path / "result.json"

    analysis_before = scan_path / "analysis_before"
    analysis_before.mkdir(exist_ok=True)

    analysis_after = scan_path / "analysis_after"
    analysis_after.mkdir(exist_ok=True)

    with open(result_file, "r") as f:
        result = json.load(f)
        interaction = result["interaction"]
        if len(interaction) != 2:
            print(f'ERROR, check {path}')
            return

        url = result['site url']
        before = interaction[0]
        store_analysis(url, before, analysis_before)

        after = interaction[1]
        store_analysis(url, after, analysis_after)


def store_analysis(url, interaction, path):
    cookies = interaction['cookies']
    fp_cookies = interaction['fp_cookies']
    cookies_tp = calc_tp_cookies(cookies, fp_cookies)
    requests = interaction['requests']
    function_calls = interaction['profile']['nodes']
    website = {"landingWebsite": url}

    store_json(path / 'cookies.json', cookies)
    store_json(path / 'thirdPartyCookies.json', cookies_tp)
    store_json(path / 'requests.json', requests)
    store_json(path / 'functions.json', function_calls)
    store_json(path / 'website.json', website)


def calc_tp_cookies(cookies, cookies_fp):
    # Source: from Consent Guard crawler (scrapers/cookie.js)
    tp_cookies = list()
    for c in cookies:
        if not next((x for x in cookies_fp if compare_cookies(c, x)), None):
            tp_cookies.append(c)
    return tp_cookies


def compare_cookies(c1, c2):
    return c1['name'] == c2['name'] and \
           c1['value'] == c2['value'] and \
           c1['domain'] == c2['domain'] and \
           c1['path'] == c2['path']


def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def store_json(file_path, json_object):
    with open(file_path, "w") as f:
        f.write(json.dumps(json_object, indent=2, sort_keys=True))
