import base64
from pathlib import Path
import requests

f = open(Path.home() / "dic_lookups/debug.log", 'w+')

def debug_print(message):
    print(message, file=f, flush=True)

# Pretend to be a browser or some servers won't allow image access (lookin' at you, Etsy!)
REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def get_url_as_base64text(url):
    # handle data URLs, which for example Google image search gives for image URLs
    data_url_prefix = 'data:image/jpeg;base64,'
    if url.startswith(data_url_prefix):
        return url[len(data_url_prefix) + 1:]
    return base64.b64encode(requests.get(url, headers = REQUEST_HEADERS).content).decode('ascii')
