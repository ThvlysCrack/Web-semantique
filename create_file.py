import spacy
from preprocessing_lemmatized import preprocess_question  # 📌 Importation du prétraitement

# Charger le modèle Transformer de SpaCy
nlp = spacy.load("en_core_web_trf")

def detect_classes(preprocessed_data):
    """
    Détecte les classes (`C`) dans une phrase et regroupe les classes multi-mots.
    """
    tokens = preprocessed_data["tokens"]
    pos_tags = preprocessed_data["pos_tags"]
    entities = preprocessed_data["entities"]

    classification = []
    grouped_classes = []
    current_class = []

    # Reconstruire la phrase pour SpaCy
    sentence = " ".join(tokens)
    doc = nlp(sentence)  # Analyse avec le modèle Transformer

    for i, token in enumerate(doc):
        tag = "O"  # Par défaut, "O"

        # 📌 1️⃣ Détection des classes (`NOUN`) qui sont des concepts généraux
        if token.pos_ == "NOUN":
            tag = "C"
            current_class.append(token.text)

        # 📌 2️⃣ Regrouper les noms composés (`compound`) pour des classes multi-mots (ex: "video game", "capital city")
        elif token.dep_ == "compound":
            current_class.append(token.text)

        else:
            # 📌 Stocker la classe détectée
            if current_class:
                class_text = " ".join(current_class)
                grouped_classes.append(class_text)
                current_class = []

        classification.append((token.text, tag))

    # Ajout de la dernière classe trouvée (si elle existe)
    if current_class:
        class_text = " ".join(current_class)
        grouped_classes.append(class_text)

    return classification, grouped_classes

# 📌 Exemple de questions pour tester
questions = [
    "Which city is the capital of France?",
    "Who is the president of the United States?",
    "What is the largest company in the world?",
    "Which movie won an Oscar in 2020?",
    "Who is the author of The Catcher in the Rye?",
    "Which scientist developed the theory of relativity?",
    "What is the most famous painting by Leonardo da Vinci?",
    "What video game was created by Nintendo?",
]

# 📌 Tester plusieurs questions
for question in questions:
    preprocessed_output = preprocess_question(question)
    classified_output, grouped_classes = detect_classes(preprocessed_output)
    
    print(f"\n📌 Détection des classes pour : \"{question}\"")
    print("Classes détectées :", grouped_classes)
    for token, tag in classified_output:
        print(f"{token}: {tag}")
