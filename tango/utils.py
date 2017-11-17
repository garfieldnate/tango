import base64
from pathlib import Path
import requests
from string import Template
from urllib.parse import quote as url_quote

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

# TODO: make language-agnostic
IMAGE_SEARCH_URL = Template("https://www.bing.de/images/search?&cc=$lang%2c$lang&setmkt=$lang-$lang&setlang=$lang-$lang&q=$word")
def get_image_search_url(lang, word):
    return IMAGE_SEARCH_URL.substitute(lang=lang, word=url_quote(word))

WIKTIONARY_URL = Template("https://$lang.wiktionary.org/wiki/$word")
def get_wiktionary_url(lang, word):
    return WIKTIONARY_URL.substitute(lang=lang, word=url_quote(word))

TATOEBA_LANGS = {'de': 'deu','fr':'fra','vi':'vie','en':'eng', 'zh':'cmn','jp':'jpn'}
EXAMPLE_SEARCH_URL = Template("https://tatoeba.org/eng/sentences/search?from=$lang&to=und&query=$word")
def get_tatoeba_url(lang, word):
    return EXAMPLE_SEARCH_URL.substitute(lang=lang, word = url_quote(word))
