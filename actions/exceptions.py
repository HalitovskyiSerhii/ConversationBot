class InvalidFileURL(Exception):
    def __init__(self, url):
        self.url = url
        self.message = f"Can't get file by url: {url}"
        super().__init__(self.message)
