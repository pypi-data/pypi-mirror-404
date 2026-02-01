from .YtSearch import Search as YtSearch
from .Search import Search
from .Models import format_dur, process_video, extract_artist
from .Utils import parse_dur, format_ind, format_views

__version__ = "2026.2.01"
__author__ = "ABHISHEK THAKUR"

try:
    from .Startup import print_startup_message
    print_startup_message()
except Exception:
    pass
