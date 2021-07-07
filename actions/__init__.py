from .config import Settings
from .file_downloader import _Downloader
from .storage import _Storage

downloader = _Downloader()
storage = _Storage()