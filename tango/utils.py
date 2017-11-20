import base64
import datetime
import json
import logging
from pathlib import Path
import requests
from string import Template
import sqlite3
from urllib.parse import quote as url_quote

import click

app_data_path = Path.home() / '.tangocho'

db_fields = ["created", "headword", "pronunciation", "morphology", "definition", "example", "image_url", "image_base64", "notes", "review_data"]

logger = logging.getLogger(__name__)
fh = logging.FileHandler(str(app_data_path / "debug.log"))
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)
def debug_print(message):
    """Print message to log file (colocated with dictionary files) and flush immediately"""
    logger.debug(message)
    logger.handlers[0].flush()

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
    return EXAMPLE_SEARCH_URL.substitute(lang=TATOEBA_LANGS[lang], word=url_quote(word))

LEO_LANGS = {'de': "deutsch"}
LEO_URL = Template("https://dict.leo.org/englisch-$lang/$word")
def get_dictionary_url(lang, word):
    return LEO_URL.substitute(lang=LEO_LANGS[lang], word=url_quote(word))

def get_formatted_datetime():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %H:%M:%S %Z %Y")

# Data-related functions

def save_tango(lang, tango):
    output_file = app_data_path / (lang + '.txt')
    with open(output_file, 'a') as f:
        print(json.dumps(tango), file=f)
