import json

from os import listdir
from os.path import isfile, join

from ..utils import get_db, dic_path
from .. import utils

fields = ["created", "headword", "pronunciation", "morphology", "definition", "example", "image_url", "image_base64", "notes", "review_data"]
def migrate():
    db = get_db()
    dic_files = [dic_path / f for f in listdir(dic_path) if isfile(dic_path / f) and f.endswith('.txt')]
    for file in dic_files:
        lang = str(file)[-6:-4]
        db.cursor().execute(f"CREATE TABLE IF NOT EXISTS {lang} (" +
                "id INTEGER PRIMARY KEY AUTOINCREMENT," +
                ",".join([f"{field} TEXT" for field in fields]) +
                ")"
                )
        with open(file) as f:
            for line in f:
                tango = json.loads(line)
                for field in fields:
                    if field not in tango:
                        tango[field] = ""
                # was using "image" in text format, now want to use "image_base64"
                tango["image_base64"] = tango.pop("image", "")
                db.cursor().execute(f"INSERT INTO {lang}(" +
                    ",".join(fields) + ") VALUES(" + ",".join(f":{field}" for field in fields) + ")",
                    tango
                )

        db.commit()
