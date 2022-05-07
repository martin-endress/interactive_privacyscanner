class Extractor:
    def __init__(self, target, page, options):
        self.target = target
        self.page = page
        self.options = options

    async def extract_information(self):
        raise NotImplementedError('You have to implement extract_information() in {}'.format(
            self.__class__.__name__))

    def receive_log(self, log_type, message, call_stack):
        pass

    def register_javascript(self):
        pass
