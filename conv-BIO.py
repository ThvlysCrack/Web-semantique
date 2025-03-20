import json
import random
from preprocessing_lemmatized import preprocess_question  # 📌 Importer le prétraitement existant

# 📌 Charger le fichier JSON de QALD-7
qald_file = "qald-7-train-multilingual.json"

# 📌 Fonction pour extraire les questions en anglais
def extract_questions(json_file):
    """
    Charge le fichier QALD-7 et extrait les questions en anglais.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = []
    for question_data in data["questions"]:
        for question in question_data["question"]:
            if question["@language"] == "en":  # Sélectionner uniquement l'anglais
                questions.append(question["string"])
    
    return questions

# 📌 Fonction pour convertir une question prétraitée en format BIO
def convert_to_bio(preprocessed_data):
    """
    Convertit les données prétraitées en format BIO.
    """
    tokens = preprocessed_data["tokens"]
    pos_tags = preprocessed_data["pos_tags"]
    entities = preprocessed_data["entities"]

    bio_tags = ["O"] * len(tokens)  # Par défaut, chaque mot est en dehors (O)

    # 📌 Marquer les entités en `B-ENTITY` et `I-ENTITY`
    for ent_text, ent_label in entities:
        ent_tokens = ent_text.split()
        for i in range(len(tokens)):
            if tokens[i] == ent_tokens[0]:  # Début de l'entité
                bio_tags[i] = f"B-{ent_label}"
                for j in range(1, len(ent_tokens)):  # Tokens suivants en I-ENTITY
                    if i + j < len(tokens) and tokens[i + j] == ent_tokens[j]:
                        bio_tags[i + j] = f"I-{ent_label}"

    # 📌 Formater les lignes en `token POS BIO`
    bio_lines = [f"{tokens[i]} {pos_tags[i][1]} {bio_tags[i]}" for i in range(len(tokens))]

    return "\n".join(bio_lines) + "\n\n"  # Ajouter une ligne vide après chaque phrase

# 📌 Extraire les questions en anglais depuis QALD-7
questions = extract_questions(qald_file)

# 📌 Mélanger les données et diviser en `train`, `dev`, `test`
random.shuffle(questions)
train_set = questions[:int(0.7 * len(questions))]  # 70% pour l'entraînement
dev_set = questions[int(0.7 * len(questions)):int(0.9 * len(questions))]  # 20% pour la validation
test_set = questions[int(0.9 * len(questions)):]  # 10% pour le test

# 📌 Générer le texte au format BIO
train_data = "\n".join([convert_to_bio(preprocess_question(q)) for q in train_set])
dev_data = "\n".join([convert_to_bio(preprocess_question(q)) for q in dev_set])
test_data = "\n".join([convert_to_bio(preprocess_question(q)) for q in test_set])

# 📌 Sauvegarder les fichiers `.conll`
with open("train.conll", "w", encoding="utf-8") as f:
    f.write(train_data)

with open("dev.conll", "w", encoding="utf-8") as f:
    f.write(dev_data)

with open("test.conll", "w", encoding="utf-8") as f:
    f.write(test_data)

print("✅ Fichiers `train.conll`, `dev.conll`, `test.conll` générés avec succès ! 🚀")
