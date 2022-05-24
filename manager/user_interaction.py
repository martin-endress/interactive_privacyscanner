import json

from errors import ScannerError


class UserInteraction:
    def __init__(self, action, selector):
        self.action = action
        self.selector = selector

    def perform(self):
        pass


def from_json(json_str):
    try:
        interaction = json.loads(json_str)
    except Exception as e:
        raise ScannerError(e)

    if 'action' not in interaction or 'selector' not in interaction:
        raise ScannerError('Action could not be parsed.')
    return UserInteraction(interaction['action'], interaction['selector'])
