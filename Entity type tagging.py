import spacy
from preprocessing_lemmatized import *

# Charger le modèle de spaCy
nlp = spacy.load("en_core_web_sm")

# Dictionnaire des relations connues (à enrichir)
RELATION_KEYWORDS = {"born", "capital", "author", "created", "married", "directed", "president", "CEO"}

# Liste de classes connues (à enrichir)
CLASS_KEYWORDS = {"book", "movie", "city", "country", "company", "person"}

def entity_type_tagging(preprocessed_data):
    """
    Fonction pour classifier les entités détectées en :
    - E (Entity)
    - R (Relation)
    - C (Class)
    """
    tokens = preprocessed_data["tokens"]
    entities = preprocessed_data["entities"]
    pos_tags = preprocessed_data["pos_tags"]

    tagged_entities = []

    for token, pos in pos_tags:
        tag = "N"  # Par défaut, "N" signifie Non pertinent

        # Vérification si c'est une entité nommée (E)
        for ent_text, ent_label in entities:
            if token in ent_text:
                tag = "E"  # Marqué comme Entité nommée
                break

        # Vérification si c'est une relation (R)
        if token.lower() in RELATION_KEYWORDS:
            tag = "R"

        # Vérification si c'est une classe (C)
        if token.lower() in CLASS_KEYWORDS:
            tag = "C"

        tagged_entities.append((token, tag))

    return tagged_entities

# Exemple de question
question = "Who is the daughter of Robert Kennedy married to?"
preprocessed_output = preprocess_question(question)
tagged_output = entity_type_tagging(preprocessed_output)

# Affichage des résultats
print("Étiquetage des entités :")
for token, tag in tagged_output:
    print(f"{token}: {tag}")
