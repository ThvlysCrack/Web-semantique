import spacy
from preprocessing_lemmatized import preprocess_question  # 📌 Importation du prétraitement

# Charger le modèle Transformer de SpaCy
nlp = spacy.load("en_core_web_trf")

def detect_relations(preprocessed_data):
    """
    Détecte les relations (`R`) et regroupe les relations multi-mots.
    """
    tokens = preprocessed_data["tokens"]
    pos_tags = preprocessed_data["pos_tags"]
    entities = preprocessed_data["entities"]

    classification = []
    grouped_relations = []
    current_relation = []

    # Reconstruire la phrase pour SpaCy
    sentence = " ".join(tokens)
    doc = nlp(sentence)  # Analyse avec le modèle Transformer

    for i, token in enumerate(doc):
        tag = "O"  # Par défaut, "O"

        # 📌 1️⃣ Détection des relations verbales (`R`) 
        if token.pos_ == "VERB" and token.dep_ in {"ROOT", "acl", "xcomp", "ccomp"}:
            tag = "R"
            current_relation.append(token.text)

        # 📌 2️⃣ Détection des relations nominales (`R`) (ex: "CEO", "father")
        elif token.pos_ == "NOUN" and token.dep_ in {"attr", "pobj", "nsubj"}:
            tag = "R"
            current_relation.append(token.text)

        # 📌 3️⃣ Détection des relations multi-mots (`R`) (ex: "father of", "CEO of", "currency used in")
        elif token.dep_ == "prep" and token.text in {"of", "by", "for", "in"}:
            if current_relation:
                tag = "R"
                current_relation.append(token.text)
            else:
                tag = "O"  # On évite de marquer "of" seul comme relation

        else:
            # Si on atteint un mot qui n'est pas `R`, on stocke la relation construite
            if current_relation:
                grouped_relations.append(" ".join(current_relation))
                current_relation = []

        classification.append((token.text, tag))

    # Ajout de la dernière relation trouvée (si elle existe)
    if current_relation:
        grouped_relations.append(" ".join(current_relation))

    return classification, grouped_relations

# 📌 Exemple de questions pour tester
questions = [
    "Who wrote Hamlet?",
    "What is the capital of France?",
    "Who is the father of Barack Obama?",
    "Who is the CEO of Apple?",
    "Who directed the movie Titanic?",
    "Who invented the telephone?",
    "What is the currency used in Canada?",
    "Who painted the Mona Lisa?",
]

# 📌 Tester plusieurs questions
for question in questions:
    preprocessed_output = preprocess_question(question)
    classified_output, grouped_relations = detect_relations(preprocessed_output)
    
    print(f"\n📌 Détection des relations pour : \"{question}\"")
    print("Relations détectées :", grouped_relations)
    for token, tag in classified_output:
        print(f"{token}: {tag}")
