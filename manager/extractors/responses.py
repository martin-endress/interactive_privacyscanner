import logging

import result
from extractors.base import Extractor

logger = logging.getLogger('response_extractor')


class ResponsesExtractor(Extractor):
    async def extract_information(self):
        responses = []
        for r in self.page.response_log:
            responses.append(await result.parse_response(r))

        return {'responses': responses}
