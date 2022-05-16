import logs
import result
from extractors.base import Extractor

logger = logs.get_logger('response_extractor')


class ResponsesExtractor(Extractor):
    async def extract_information(self):
        responses = []
        for r in self.page.response_log:
            responses.append(await result.parse_response(r))

        return {'responses': responses}
