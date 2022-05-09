import logging

from chromedev.extractors.base import Extractor

logger = logging.getLogger('third_parties_extractor')


class ThirdParties(Extractor):
    # not used for now
    async def extract_information(self):
        third_parties = list()
        for entry in self.page.response_log:
            url = urlparse(entry['url'])
            if url.netloc != self.start_url_netloc:
                content_type = 'not specified'
                if 'Content-Type' in entry['headers']:
                    content_type = entry['headers']['Content-Type']
                third_parties.append(
                    {'url': url.netloc, 'Content-Type': content_type})
        return {'third_parties':third_parties}

