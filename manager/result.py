import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import utils
from errors import ScannerInitError
from utils import DirectoryFileHandler


class Result(object):
    '''
    see https://github.com/PrivacyScore/privacyscanner/blob/master/privacyscanner/result.py
    '''

    def __init__(self, result_dict, result_file):
        self._result_dict = result_dict
        self._result_file = result_file
        self._file_handler = DirectoryFileHandler(result_file.parent)
        self._updated_keys = set()

    def add_debug_file(self, filename, contents=None):
        self._file_handler.add_file(
            filename, self._get_file_contents(filename, contents), debug=True)

    def add_file(self, filename, contents):
        self._file_handler.add_file(
            filename, self._get_file_contents(filename, contents), debug=False)

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
        try:
            with self._result_file.open("w") as f:
                json.dump(self.get_results(),
                          f, indent=2, sort_keys=True)
                f.write("\n")
        except IOError as e:
            raise ScannerInitError(
                "Could not write result JSON: {}".format(e)) from e


def init_from_scanner(url):
    site_parsed = urlparse(url)
    if site_parsed.scheme not in ("http", "https"):
        raise ScannerInitError("Invalid site url: {}".format(url))
    # TODO add ability to override this in options
    results_dir = get_result_path(site_parsed.netloc)
    if results_dir.exists() or results_dir.is_file():
        raise ScannerInitError("Folder already exists." + str(results_dir))
    try:
        results_dir.mkdir(parents=True)
    except IOError as e:
        raise ScannerInitError("Could not create results directory: {}".format(e)) from e

    result_file = results_dir / "results.json"
    result_json = {"site_url": url,
                   #   "scan_start": datetime.utcnow(),
                   "interaction": []}
    try:
        with result_file.open("w") as f:
            json.dump(result_json, f, indent=2)
            f.write("\n")
    except IOError as e:
        raise ScannerInitError(
            "Could not write result JSON: {}".format(e)) from e

    return Result(result_json, result_file)


def get_result_path(netloc):
    now = datetime.now().strftime("%y-%m-%d_%H-%M")
    dir_name = "%s_%s" % (utils.slugify(netloc), now)
    return (Path("results") / dir_name).resolve()
