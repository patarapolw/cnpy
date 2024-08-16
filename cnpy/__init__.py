from cnpy import cedict, quiz, tatoeba, db


def load_db():
    quiz.load_db()
    cedict.load_db()
    tatoeba.load_db()

    return db.db
