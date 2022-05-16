import logs
import result
from extractors.base import Extractor

logger = logs.get_logger('requests_extractor')


class RequestsExtractor(Extractor):
    async def extract_information(self):
        requests = []
        for r in self.page.request_log:
            requests.append(await result.parse_request(r))
        return {'requests': requests}
