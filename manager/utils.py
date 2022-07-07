import asyncio
import base64
import hashlib
import hmac
import secrets
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
