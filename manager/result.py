import json
from datetime import datetime
from pathlib import Path

import logs
import utils
from errors import ScannerInitError, ScannerError
from utils import DirectoryFileHandler

INITIAL_SCAN = 'initial scan'
MANUAL_INTERACTION = 'manual interaction'
DELETE_COOKIES = 'delete cookies'
END_SCAN = 'end scan'

FIRST_SCAN = 'first_scan'
RECORDED_SCAN_PREFIX = 'recorded_scan_'

RESULT_FILENAME = 'result.json'

RESULT_PATH = "results"

logger = logs.get_logger('results')


class Result(object):
    """
    see https://github.com/PrivacyScore/privacyscanner/blob/master/privacyscanner/result.py
    """

    def __init__(self, result_dict, result_id, initial_scan):
        self._result_dict = result_dict
        self._result_path = (Path(RESULT_PATH) / result_id).resolve()
        self._current_scan_path = self.get_current_scan_path(initial_scan)
        self._file_handler = DirectoryFileHandler(self._current_scan_path)
        self._updated_keys = set()
        self.num_screenshots = 0
        self.store_result()

    def get_current_scan_path(self, initial_scan):
        if initial_scan and self._result_path.exists():
            raise ScannerInitError('Result folder already exists.')

        if initial_scan:
            return self._result_path / FIRST_SCAN
        else:
            recording_id = 0
            next_recorded_path = (self._result_path / (RECORDED_SCAN_PREFIX + str(recording_id)))
            while next_recorded_path.exists():
                recording_id += 1
                next_recorded_path = (self._result_path / (RECORDED_SCAN_PREFIX + str(recording_id)))
            return next_recorded_path

    def get_files_path(self):
        return self._file_handler.get_files_path()

    def add_debug_file(self, filename, contents=None):
        self._file_handler.add_file(
            filename, self._get_file_contents(filename, contents), debug=True)

    def add_file(self, filename, contents):
        self._file_handler.add_file(
            filename, self._get_file_contents(filename, contents), debug=False)

    def add_image(self, filename, contents):
        self._file_handler.add_image(filename, contents, debug=False)

    def _get_file_contents(self, filename, contents=None):
        if contents is None:
            with open(filename, 'rb') as f:
                return f.read()
        if hasattr(contents, 'read'):
            contents = contents.read()
        return contents

    def __getitem__(self, key):
        return self._result_dict[key]

    def __setitem__(self, key, value):
        self.mark_dirty(key)
        self._result_dict[key] = value

    def __contains__(self, key):
        return key in self._result_dict

    def get(self, key, d=None):
        return self._result_dict.get(key, d)

    def keys(self):
        return self._result_dict.keys()

    def values(self):
        return self._result_dict.items()

    def items(self):
        return self._result_dict.items()

    def update(self, d, **kwargs):
        if isinstance(d, dict):
            for key in d:
                self.mark_dirty(key)
        else:
            for key, _value in d:
                self.mark_dirty(key)
        for key in kwargs:
            self.mark_dirty(key)
        return self._result_dict.update(d, **kwargs)

    def setdefault(self, key, d):
        self.mark_dirty(key)
        return self._result_dict.setdefault(key, d)

    def mark_dirty(self, key):
        self._updated_keys.add(key)

    def get_updates(self):
        return {key: self._result_dict[key] for key in self._updated_keys}

    def get_results(self):
        return self._result_dict

    def store_result(self):
        result_file = self._current_scan_path / RESULT_FILENAME
        try:
            with result_file.open("w") as f:
                json.dump(self._result_dict, f, indent=2, sort_keys=True)
                f.write("\n")
                logger.debug(json.dumps(self._result_dict, indent=1, sort_keys=True))
        except IOError as e:
            raise ScannerInitError(
                "Could not write result JSON: {}".format(e)) from e


def get_result_id(netloc):
    now = datetime.now().strftime("%y-%m-%d_%H-%M")
    return "%s_%s" % (utils.slugify(netloc), now)


async def parse_request(request):
    return {"url": request.url,
            "method": request.method,
            "headers": await request.all_headers(),
            "post_data": request.post_data}


async def parse_response(response):
    return {"url": response.url,
            "request": await parse_request(response.request),
            "headers": await response.all_headers(),
            "status": response.status,
            "security": await response.security_details()}


def get_result_dict(id, shorten=False):
    result_path = (Path("results") / id).resolve()
    if not result_path.exists() or not result_path.is_dir():
        raise ScannerError(f"Result folder {str(result_path)} does not exist.")
    json_path = result_path / "result.json"
