import json
import random
from preprocessing_lemmatized import preprocess_question  # 📌 Importer le prétraitement existant

# 📌 Fichiers JSON QALD-7
train_file = "qald-7-train-multilingual.json"
test_file = "qald-7-test-multilingual.json"

# 📌 Fonction pour extraire les questions en anglais depuis un fichier JSON
def extract_questions(json_file):
    """
    Charge un fichier QALD-7 et extrait les questions en anglais.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = []
    
    for question_data in data["questions"]:
        for question in question_data.get("question", []):  # Utilisation de `.get()` pour éviter KeyError
            if "language" in question and question["language"] == "en":
                questions.append(question["string"])
    
    return questions

# 📌 Fonction pour convertir une question en format BIO
def convert_to_bio(preprocessed_data):
    tokens = preprocessed_data["tokens"]
    pos_tags = preprocessed_data["pos_tags"]
    entities = preprocessed_data["entities"]

    bio_tags = ["O"] * len(tokens)

    for ent_text, ent_label in entities:
        ent_tokens = ent_text.split()
        for i in range(len(tokens)):
            if tokens[i] == ent_tokens[0]:
                bio_tags[i] = f"B-E"  # `E` pour les entités
                for j in range(1, len(ent_tokens)):
                    if i + j < len(tokens) and tokens[i + j] == ent_tokens[j]:
                        bio_tags[i + j] = f"I-E"

    return "\n".join([f"{tokens[i]} {pos_tags[i][1]} {bio_tags[i]}" for i in range(len(tokens))]) + "\n\n"

# 📌 Extraire les questions en anglais
train_questions = extract_questions(train_file)
test_questions = extract_questions(test_file)

# 📌 Vérifier que des questions ont bien été extraites
if not train_questions or not test_questions:
    print("❌ Erreur : Aucune question trouvée dans les fichiers JSON.")
    exit()

# 📌 Diviser `qald-7-train-multilingual.json` en `train.conll` (80%) et `dev.conll` (20%)
random.shuffle(train_questions)
train_set = train_questions[:int(0.8 * len(train_questions))]  # 80% pour l'entraînement
dev_set = train_questions[int(0.8 * len(train_questions)):]  # 20% pour la validation

# 📌 Générer les données en format BIO
train_data = "\n".join([convert_to_bio(preprocess_question(q)) for q in train_set])
dev_data = "\n".join([convert_to_bio(preprocess_question(q)) for q in dev_set])
test_data = "\n".join([convert_to_bio(preprocess_question(q)) for q in test_questions])

# 📌 Sauvegarder les fichiers `.conll`
with open("data/train.conll", "w", encoding="utf-8") as f:
    f.write(train_data)

with open("data/dev.conll", "w", encoding="utf-8") as f:
    f.write(dev_data)

with open("data/test.conll", "w", encoding="utf-8") as f:
    f.write(test_data)

print("✅ Fichiers `train.conll`, `dev.conll`, `test.conll` générés avec succès ! 🚀")
