import sqlite3
from enum import Enum, auto

import click

from .sm2_plus import get_default_variables as get_default_sm2p
from .utils import app_data_path, debug_print, get_current_datetime, get_formatted_datetime

db_path = app_data_path / "tango.db"

reserved_tables = ["review_history", "sm2_plus"]

lang_fields = ["created", "headword", "pronunciation", "morphology", "definition", "example", "image_url",
               "image_base64", "notes"]


class Score(Enum):
    BAD = auto()
    OK = auto()
    GREAT = auto()


# We use regular dictionaries instead of Sqlite3.Row because they can be used with cursor.execute()
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Model:
    def __init__(self):
        self._db = sqlite3.connect(str(db_path))
        self._db.row_factory = dict_factory
        self._check_tables()

    def _check_tables(self):
        cursor = self._db.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = [t['name'] for t in tables]
        self._all_languages = [name for name in table_names if
                               not name.startswith('sqlite') and name not in reserved_tables]
        if "review_history" not in table_names:
            cursor.execute("""CREATE TABLE review_history (
                    id INTEGER PRIMARY KEY,
                    lang TEXT,
                    tango_id INTEGER,
                    timestamp TEXT,
                    score TEXT,
                    data TEXT
                )
            """)
            self._db.commit()
        if "sm2_plus" not in table_names:
            self._init_sm2p_table()

    def _init_sm2p_table(self):
        cursor = self._db.cursor()
        cursor.execute("""CREATE TABLE sm2_plus (
                lang TEXT,
                tango_id INTEGER,
                difficulty REAL,
                daysBetweenReviews REAL,
                dateLastReviewed TEXT,
                PRIMARY KEY  (lang, tango_id)
            )
        """)
        for tango in self.get_tango_for_language('all'):
            starting_vals = get_default_sm2p(tango)
            row_data = {**tango, **starting_vals}
            cursor.execute("""INSERT INTO sm2_plus
                (lang, tango_id, difficulty, daysBetweenReviews, dateLastReviewed)
                VALUES (:lang, :id, :difficulty, :daysBetweenReviews, :dateLastReviewed)
                """, row_data)
        self._db.commit()

    def get_sm2p_vars(self, tango):
        cursor = self._db.cursor()
        return cursor.execute("""SELECT * FROM sm2_plus
            WHERE lang=:lang AND tango_id=:id""", dict(tango)).fetchone()

    def update_sm2p_vars(self, tango, sm2p_vars):
        row_vars = {**tango, **sm2p_vars}
        cursor = self._db.cursor()
        self._db.cursor().execute('''
            INSERT OR REPLACE INTO sm2_plus (lang, tango_id, difficulty, daysBetweenReviews, dateLastReviewed) VALUES(:lang, :id, :difficulty, :daysBetweenReviews, :dateLastReviewed)''',
                                  row_vars)
        self._db.commit()

    def validate_language(self, lang):
        """Check if the given language is legal to use and create a new table for it if needed"""
        if lang.startswith("sqlite"):
            raise ValueError("Illegal language name: " + lang)
        if lang in self._all_languages:
            return True
        else:
            if click.confirm(f"No tango-cho for '{lang}' exists. Create?", default=False):
                self._db.cursor().execute(f"CREATE TABLE '{lang}' (" +
                                          "id INTEGER PRIMARY KEY AUTOINCREMENT," +
                                          ",".join([f"'{field}' TEXT" for field in lang_fields]) +
                                          ")"
                                          )
                self._db.commit()
                self._all_languages.extend(lang)
                return True
            else:
                return False

    def get_tango(self, lang, tango_id):
        if lang not in self._all_languages:
            raise ValueError("No such language: " + lang)
        return self._db.cursor().execute(
            f"SELECT *, '{lang}' as lang from '{lang}' WHERE id=:id", {"id": tango_id}).fetchone()

    def get_tango_for_language(self, lang):
        """Return a list of all of the tango for the given language. If lang is 'all', then
        all tango for all languages are returned."""

        def get_for_one_language(lang):
            return self._db.cursor().execute(f"SELECT *, '{lang}' as lang FROM '{lang}';").fetchall()

        if lang == 'all':
            entries = []
            for language in self._all_languages:
                entries.extend(get_for_one_language(language))
            return entries
        else:
            if lang not in self._all_languages:
                raise ValueError("No such language: " + lang)
            return get_for_one_language(lang)

    def add_tango(self, lang, tango):
        """Add the tango to the database and return the automatically created ID"""
        if lang not in self._all_languages:
            raise ValueError("No such language: " + lang)

        debug_print(f"Inserting {tango}")
        cursor = self._db.cursor()
        cursor.execute(f'''
            INSERT INTO {lang} (created, headword, pronunciation, morphology, definition, example, image_url, image_base64, notes)
            VALUES('{get_formatted_datetime(get_current_datetime())}', :headword, :pronunciation, :morphology, :definition, :example, :image_url, :image_base64, :notes)''',
                       tango)
        self._db.commit()
        return cursor.lastrowid

    def update_tango(self, lang, tango):
        if lang not in self._all_languages:
            raise ValueError("No such language: " + lang)
        self._db.cursor().execute(f'''
            UPDATE {lang} SET headword=:headword, pronunciation=:pronunciation, morphology=:morphology, definition=:definition, example=:example, image_url=:image_url, image_base64=:image_base64, notes=:notes
            WHERE id=:id''',
                                  tango)
        self._db.commit()

    def log_study(self, tango, score):
        cursor = self._db.cursor()
        date_now = get_formatted_datetime(get_current_datetime())
        debug_print(f'''
            INSERT INTO review_history (lang, tango_id, timestamp, score)
            VALUES(:lang, :id, '{date_now}', '{str(score)}')''')
        cursor.execute(f'''
            INSERT INTO review_history (lang, tango_id, timestamp, score)
            VALUES(:lang, :id, '{date_now}', '{str(score)}')''', tango)
        self._db.commit()


model_instance = Model()


def get_model():
    return model_instance
