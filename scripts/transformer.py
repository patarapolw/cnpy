# from sentence_transformers import SentenceTransformer, util

# from pathlib import Path
# from random import choice

# from cnpy.db import db

# # This requires model to be download first time, at runtime
# model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


# def check_meaning_similarity(s1: str, s2: str):
#     emb1 = model.encode(s1, convert_to_tensor=True)
#     emb2 = model.encode(s2, convert_to_tensor=True)

#     value = util.cos_sim(emb1, emb2).item()
#     correct = False
#     if value > 0.75:
#         correct = True
#     elif value > 0.65:
#         correct = None

#     return correct, value


# if __name__ == "__main__":
#     vlist = Path("user/vocab/vocab.txt").read_text("utf-8").splitlines()

#     while True:
#         v = choice(vlist)
#         entries = [
#             dict(r)
#             for r in db.execute(
#                 "SELECT * FROM cedict WHERE simp = ? OR trad = ?", (v, v)
#             )
#         ]

#         en = input(f"Meaning of {v}: ")
#         print(check_meaning_similarity("zh:" + v, en))
#         print(
#             sorted(
#                 entries,
#                 key=lambda r: check_meaning_similarity(en, r["english"]),
#                 reverse=True,
#             )
#         )
