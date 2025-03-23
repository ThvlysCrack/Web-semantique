def predire_template(question_obj):
    """
    Cette fonction retourne le template "D" si la question commence par l'un des mots :
    "did", "is", "were", "was" ou "are" (sans tenir compte de la casse).
    Dans le cas contraire, elle retourne le template initialement attribué (contenu dans "template_id").
    """
    question_text = question_obj.get("question", "").strip().lower()
    if question_text.startswith(("did ","does ", "is ", "were ", "was ", "are ")):
        return "D"
    else:
        return question_obj.get("template_id", "unknown")

# # Exemple d'utilisation :
# question_obj = {
#     "question": "what is the capital of France?",
#     "template_id": "A",
#     "entity_tagging": [
#         {"token": "What", "tag": "V-B"},
#         {"token": "is", "tag": "R-B"},
#         {"token": "the", "tag": "N"},
#         {"token": "capital", "tag": "C-B"},
#         {"token": "of", "tag": "R-B"},
#         {"token": "France", "tag": "E-B"},
#         {"token": "?", "tag": "N"}
#     ]
# }

# template_attribue = predire_template(question_obj)
# print("Template attribué :", template_attribue)
