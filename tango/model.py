import json
from pathlib import Path
import sqlite3

from .utils import app_data_path, debug_print

class Model:
    def __init__(self):
        self._db = sqlite3.connect(str(app_data_path / "tango.db"))
        self._db.row_factory = sqlite3.Row

    def get_all_languages(self):
        cursor = self._db.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = [t['name'] for t in tables]
        languages = [name for name in table_names if not name.startswith('sqlite')]
        return languages

    def validate_language(self, lang):
        """Check if the given lang is legal to use and create a new table for it if needed"""
        if lang.startswith("sqlite"):
            raise ValueError("Illegal language name: " + lang)
        languages = self.get_all_languages()
        if lang in languages:
            return True
        else:
            if click.confirm(f"No tango-cho for {lang} exists. Create?", default=False):
                get_db().cursor().execute(f"CREATE TABLE {lang} (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT," +
                    ",".join([f"{field} TEXT" for field in db_fields]) +
                    ")"
                    )
                return True
            else:
                return False

    def get_tango(self, lang, tango_id):
        return self._db.cursor().execute(
            f"SELECT * from {lang} WHERE id=:id", {"id": tango_id}).fetchone()

    def get_tango_for_language(self, lang):
        """Return a list of all of the tango for the given language. If lang is 'all', then
        all tango for all languages are returned."""

        def get_for_one_language(lang):
            return self._db.cursor().execute(f"SELECT * FROM {lang};").fetchall()

        if lang == 'all':
            languages = get_model().get_all_languages()
            entries = []
            for language in languages:
                entries.extend(get_for_one_language(language))
            return entries
        else:
            return get_for_one_language(lang)

    def add_tango(self, lang, tango):
        """Add the tango to the database and return the automatically created ID"""
        cursor = self._db.cursor()
        cursor.execute(f'''
            INSERT INTO {lang} (created, headword, morphology, definition, example, image_url, image_base64, notes)
            VALUES(:created, :headword, :morphology, :definition, :example, :image_url, :image_base64, :notes)''',
            tango)
        self._db.commit()
        debug_print(tango)
        return cursor.lastrowid

    def update_tango(self, lang, tango):
        self._db.cursor().execute(f'''
            UPDATE {lang} SET headword=:headword, morphology=:morphology, definition=:definition, example=:example, image_url=:image_url, image_base64=:image_base64, notes=:notes
            WHERE id=:id''',
            tango)
        self._db.commit()

model_instance = Model()

def get_model():
    return model_instance
