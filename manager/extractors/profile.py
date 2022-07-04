import logs
from extractors.base import Extractor

from errors import ScannerError
logger = logs.get_logger('profile_extractor')


class ProfileExtractor(Extractor):
    async def extract_information(self):
        logger.info('extracting profile info')
        profile = await self.browser.cpd_send_message("Profiler.stop")
        if profile is None or profile['profile'] is None:
            raise ScannerError('profile is none! Was not started properly.')
        return {'profile': profile['profile']}
