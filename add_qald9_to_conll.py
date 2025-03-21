import json
import os
from preprocessing_lemmatized import preprocess_question

# 📁 Chemins vers les fichiers QALD-9
qald9_train_file = "qald-9-train-multilingual.json"
qald9_test_file = "qald-9-test-multilingual.json"

# 📁 Chemins vers les fichiers `.conll` existants
train_conll_path = "data/train.conll"
test_conll_path = "data/test.conll"

# 📌 Fonction pour extraire les questions en anglais
def extract_questions(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = []
    for q in data["questions"]:
        for item in q.get("question", []):
            if item.get("language") == "en":
                questions.append(item["string"])
    return questions

# 📌 Fonction pour convertir une question en BIO (uniquement avec entités `E`)
def convert_to_bio(preprocessed_data):
    tokens = preprocessed_data["tokens"]
    entities = preprocessed_data["entities"]

    bio_tags = ["O"] * len(tokens)

    # Pour chaque entité détectée (ex: "Brad Pitt")
    for ent_text, ent_label in entities:
        ent_words = ent_text.split()
        ent_len = len(ent_words)

        # Balayer la phrase token par token pour chercher une correspondance exacte
        for i in range(len(tokens) - ent_len + 1):
            window = tokens[i:i + ent_len]
            if window == ent_words:
                bio_tags[i] = "E-B"
                for j in range(1, ent_len):
                    bio_tags[i + j] = "E-I"
                break  # Ne tague qu'une fois par entité

    return "\n".join([f"{tokens[i]} {bio_tags[i]}" for i in range(len(tokens))]) + "\n\n"

# 📌 Ajouter les questions au bon fichier `.conll`
def append_to_conll_file(filepath, questions):
    with open(filepath, "a", encoding="utf-8") as f:
        for question in questions:
            processed = preprocess_question(question)
            conll_block = convert_to_bio(processed)
            f.write(conll_block)

# 📌 Extraction
qald9_train_questions = extract_questions(qald9_train_file)
qald9_test_questions = extract_questions(qald9_test_file)

# 📌 Ajout aux fichiers existants
append_to_conll_file(train_conll_path, qald9_train_questions)
append_to_conll_file(test_conll_path, qald9_test_questions)

print("✅ Questions QALD-9 ajoutées avec succès à train.conll et test.conll !")
