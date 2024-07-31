from cjpy import cedict, db


def load_db():
    cedict.load_db()
    return db.db
