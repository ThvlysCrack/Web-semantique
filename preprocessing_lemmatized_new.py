import spacy

# Charger le modèle NLP de spaCy
nlp = spacy.load("en_core_web_trf")

def correct_pos(token, context):
    """
    Corrige les erreurs courantes de POS-tags en fonction du contexte global.
    """
    if token.text in ["Where", "When"]:
        return "ADV"  # "Where" et "When" sont toujours des adverbes interrogatifs
    if token.text in ["Who", "What"]:
        return "PRON"  # "Who" et "What" sont des pronoms
    if token.text in ["Which"] and context[token.i + 1].pos_ == "NOUN":
        return "DET"  # "Which" est un déterminant avant un nom
    return token.pos_  # Sinon, garder le POS d'origine

def preprocess_question(question):
    """
    Prétraitement avancé des questions :
    - Tokenisation et lemmatisation
    - Étiquetage grammatical (POS-tagging)
    - Correction automatique des POS-tags
    La fusion des entités multi-mots et la liste des entités ne sont plus appliquées.
    """
    doc = nlp(question)

    tokens = []
    lemmas = []
    pos_tags = []

    for token in doc:
        tokens.append(token.text)
        lemmas.append(token.lemma_)
        corrected_pos = correct_pos(token, doc)
        pos_tags.append((token.text, corrected_pos))

    return {
        "question": question,
        "tokens": tokens,
        "lemmas": lemmas,
        "pos_tags": pos_tags
    }
'''
# Exemple d'utilisation
if __name__ == "__main__":
    question = "Who is the CEO of Apple?"
    result = preprocess_question(question)
    print("Tokens:", result["tokens"])
    print("Lemmas:", result["lemmas"])
    print("POS-tags:", result["pos_tags"])

# 📌 Liste de 10 questions générales pour tester
questions = [
    "Where is Fort Knox located?",
    "Who composed the music for Star Wars?",
    "What is the population of Germany?",
    "Which river flows through Paris?",
    "Who discovered penicillin?",
    "When was the Eiffel Tower built?",
    "What is the tallest mountain in the world?",
    "Which city is the capital of Japan?",
    "Who wrote the book The Catcher in the Rye?",
    "What is the currency used in Canada?"
]

# 📌 Exécuter le prétraitement sur chaque question
for i, question in enumerate(questions):
    print(f"\n📝 Question {i+1}: {question}")
    result = preprocess_question(question)
    
    for key, value in result.items():
        print(f"{key}: {value}")
'''