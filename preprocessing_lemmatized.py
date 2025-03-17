import spacy

# Charger le modèle de langue anglais de spaCy
nlp = spacy.load("en_core_web_sm")

def preprocess_question(question):
    """
    Fonction de prétraitement de la question.
    - Tokenisation
    - Lemmatisation
    - Étiquetage grammatical
    - Reconnaissance des entités nommées (NER)
    """
    doc = nlp(question)
    
    # Tokenisation et Lemmatisation
    tokens = [token.text for token in doc]
    lemmas = [token.lemma_ for token in doc]

    # Étiquetage grammatical (POS-tagging)
    pos_tags = [(token.text, token.pos_) for token in doc]

    # Reconnaissance des entités nommées
    entities = [(ent.text, ent.label_) for ent in doc.ents]

    return {
        "tokens": tokens,
        "lemmas": lemmas,
        "pos_tags": pos_tags,
        "entities": entities
    }

# Exemple d'utilisation
question = "Who is the author of the book written by J.K. Rowling?"
preprocessed_output = preprocess_question(question)

# Afficher les résultats
for key, value in preprocessed_output.items():
    print(f"{key}: {value}")
