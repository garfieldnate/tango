import json
from pathlib import Path
import sqlite3

from .utils import app_data_path, debug_print

db_path = app_data_path / "tango.db"

class Model:
    def __init__(self):
        self._db = sqlite3.connect(str(db_path))
        self._db.row_factory = sqlite3.Row
        self._check_tables()

    def _check_tables(self):
        cursor = self._db.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = [t['name'] for t in tables]
        if "review" not in table_names:
            cursor.execute("""CREATE TABLE review (
                    id INTEGER PRIMARY KEY,
                    lang TEXT,
                    tango_id INTEGER,
                    timestamp TEXT,
                    score INTEGER,
                    data TEXT
                )
            """)
        self._all_languages = [name for name in table_names if not name.startswith('sqlite') and name != "review"]

    def validate_language(self, lang):
        """Check if the given language is legal to use and create a new table for it if needed"""
        if lang.startswith("sqlite"):
            raise ValueError("Illegal language name: " + lang)
        if lang in self._all_languages:
            return True
        else:
            if click.confirm(f"No tango-cho for {lang} exists. Create?", default=False):
                self._db.cursor().execute(f"CREATE TABLE {lang} (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT," +
                    ",".join([f"{field} TEXT" for field in db_fields]) +
                    ")"
                    )
                self._all_languages.extend(lang)
                return True
            else:
                return False

    def get_tango(self, lang, tango_id):
        if lang not in self._all_languages:
            raise ValueError("No such language: " + lang)
        return self._db.cursor().execute(
            f"SELECT * from {lang} WHERE id=:id", {"id": tango_id}).fetchone()

    def get_tango_for_language(self, lang):
        """Return a list of all of the tango for the given language. If lang is 'all', then
        all tango for all languages are returned."""

        def get_for_one_language(lang):
            return self._db.cursor().execute(f"SELECT * FROM {lang};").fetchall()

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
        cursor = self._db.cursor()
        cursor.execute(f'''
            INSERT INTO {lang} (created, headword, morphology, definition, example, image_url, image_base64, notes)
            VALUES(:created, :headword, :morphology, :definition, :example, :image_url, :image_base64, :notes)''',
            tango)
        self._db.commit()
        debug_print(tango)
        return cursor.lastrowid

    def update_tango(self, lang, tango):
        if lang not in self._all_languages:
            raise ValueError("No such language: " + lang)
        self._db.cursor().execute(f'''
            UPDATE {lang} SET headword=:headword, morphology=:morphology, definition=:definition, example=:example, image_url=:image_url, image_base64=:image_base64, notes=:notes
            WHERE id=:id''',
            tango)
        self._db.commit()

    def record_study(self, lang, tango_id):
        pass

model_instance = Model()

def get_model():
    return model_instance
