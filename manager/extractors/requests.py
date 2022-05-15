import logging

import result
from extractors.base import Extractor

logger = logging.getLogger('requests_extractor')


class RequestsExtractor(Extractor):
    async def extract_information(self):
        requests = []
        for r in self.page.request_log:
            requests.append(await result.parse_request(r))
        return {'requests': requests}
