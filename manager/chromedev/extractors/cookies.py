from chromedev.extractors.base import Extractor


class CookiesExtractor(Extractor):
    async def extract_information(self):
        print('extracting cookie info')
        cookies = await self.target.Network.getAllCookies()
        cookies = cookies['cookies']
        #timestamp = int(self.page.scan_start.timestamp())
        # for cookie in cookies:
        #     if cookie['session'] or cookie['expires'] is None:
        #         cookie['lifetime'] = -1
        #     else:
        #         cookie['lifetime'] = cookie['expires'] - timestamp
        self.result['cookies'] = cookies
