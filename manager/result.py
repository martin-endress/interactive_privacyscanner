import json
import shutil
from datetime import datetime
from pathlib import Path

import logs
import utils
from errors import ScannerInitError, ScannerError
from utils import DirectoryFileHandler


class ResultKey:
    # interaction types
    INITIAL_SCAN = 'initial scan'
    MANUAL_INTERACTION = 'manual interaction'
    DELETE_COOKIES = 'delete cookies'
    END_SCAN = 'end scan'

    # interaction
    INTERACTION = 'interaction'

    # interaction entries
    SITE_URL = 'site url'
    URL = 'url'
    EVENT = 'event'
    TIMESTAMP = 'timestamp'
    SCREENSHOTS = 'screenshots'
    USER_INTERACTION = 'user interaction'
    ERROR = 'error'


# filename format
FIRST_SCAN = 'first_scan'
RECORDED_SCAN_PREFIX = 'recorded_scan_'

# file / folder names
RESULT_FILENAME = 'result.json'
RESULT_PATH = Path('results')
DOWNLOAD_PATH = Path('download')

logger = logs.get_logger('results')


class Result:
    """
    see https://github.com/PrivacyScore/privacyscanner/blob/master/privacyscanner/result.py
    """

    def __init__(self, result_dict, result_id, initial_scan):
        self._result_dict = result_dict
        self.result_id = result_id
        self._result_path = (RESULT_PATH / result_id).resolve()
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

    def store_result(self, note=None):
        if note:
            self['user_note'] = note
        result_file = self._current_scan_path / RESULT_FILENAME
        try:
            with result_file.open("w") as f:
                json.dump(self._result_dict, f, indent=2, sort_keys=True)
                f.write("\n")
        except IOError as e:
            raise ScannerInitError("Could not write result JSON: {}".format(e)) from e


def get_scan_info(result_id):
    """
    Returns the filtered result of the first scan.
    :param result_id: result id referencing the result root folder
    :return: result json containing urls, events and user interaction of the first scan
    """
    result_path = (Path("results") / result_id / FIRST_SCAN / RESULT_FILENAME).resolve()
    if not result_path.exists() or result_path.is_dir():
        raise ScannerError(f"Result file {str(result_path)} does not exist.")
    with open(result_path) as f:
        first_result = json.load(f)
        interaction_filtered = list(map(filter_entry, first_result[ResultKey.INTERACTION]))
        return {ResultKey.SITE_URL: first_result[ResultKey.SITE_URL], ResultKey.INTERACTION: interaction_filtered}


def filter_entry(e):
    interaction_filter = [ResultKey.URL,
                          ResultKey.EVENT,
                          ResultKey.USER_INTERACTION]
    return filter_dict(e, interaction_filter)


def get_all_scans():
    scans = []
    for p in RESULT_PATH.iterdir():
        current_scan = {'id': p.name, 'replays': []}
        if not p.is_dir():
            # .gitignore file
            continue
        for scan in p.iterdir():
            if not scan.is_dir():
                # e.g. result zip files
                continue
            logger.debug(scan)
            success = scan_successful(scan)
            if scan.name == FIRST_SCAN:
                current_scan['initial'] = {'success': success}
            else:
                current_scan['replays'].append({'success': success})
        scans.append(current_scan)
    return scans


def archive_result(scan_id):
    if not is_scan_id(scan_id):
        # prevent path traversal
        raise ScannerError(f'Download failed, {scan_id} is not a scan id.')
    # store result inside folder
    shutil.make_archive(DOWNLOAD_PATH / scan_id, 'zip', RESULT_PATH / scan_id)
    return f'{scan_id}.zip'


def archive_all_results():
    time_str = datetime.now().strftime("%d-%m-%Y_%H-%M")
    filename = 'results_' + time_str
    shutil.make_archive(DOWNLOAD_PATH / filename, "zip", RESULT_PATH)
    return filename + '.zip'


def is_scan_id(scan_id):
    scan_path = RESULT_PATH
    for s in scan_path.iterdir():
        if s.name == scan_id:
            return True
    return False


def scan_successful(path):
    with open(path / RESULT_FILENAME) as f:
        r = json.load(f)
        return not (ResultKey.ERROR in r)


def filter_dict(d, keys):
    return {k: d[k] for k in d.keys() & keys}


def get_result_id(netloc):
    now = datetime.now().strftime("%y-%m-%d_%H-%M-%S")
    return f"{utils.slugify(netloc)}_{now}"


async def parse_request(request):
    post_data = "decoding of post data failed"
    try:
        post_data = request.post_data
    except UnicodeDecodeError as e:
        logger.warning(e, exc_info=True)

    return {"url": request.url,
            "method": request.method,
            "headers": await request.all_headers(),
            "post_data": post_data,
            "document_url": request.frame.url}


async def parse_response(response):
    return {"url": response.url,
            "request": await parse_request(response.request),
            "headers": await response.all_headers(),
            "status": response.status,
            "security": await response.security_details()}
