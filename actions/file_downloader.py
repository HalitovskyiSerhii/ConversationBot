import io
import logging
import re
from typing import List

from requests import Session

from .exceptions import InvalidFileURL

logger = logging.getLogger(__name__)

class _Downloader:

    def __init__(self):
        self.session = Session()
        self.downloaded_urls = set()

    def _download(self, links: List):
        urls = set(links).difference(self.downloaded_urls) if self.downloaded_urls else set(links)

        for url in urls:
            try:
                response = self.session.get(url)
                if response.status_code // 100 == 2:
                    content = io.BytesIO(response.content)

                    matches = re.findall("filename=(.+)", response.headers['content-disposition'])
                    if matches:
                        content.name = matches[0]
                    else:
                        content.name = 'unknown'
                    self.downloaded_urls.add(url)

                    yield content
                else:
                    self.downloaded_urls.add(url)
                    raise InvalidFileURL(url)

            except Exception as e:
                logger.error(e)
                self.downloaded_urls.add(url)
                raise InvalidFileURL(url)

        self.downloaded_urls = set()

    def __call__(self, *, urls, **kwargs):
        return self._download(urls)
