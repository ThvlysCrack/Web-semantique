import json

# 📁 Fichiers contenant les questions prétraitées
train_file = "data/train.conll"
dev_file = "data/dev.conll"
test_file = "data/test.conll"

# 📁 Fichier de sortie
output_json = "classified_questions.json"

def parse_conll_file(filepath):
    """
    Lit un fichier CoNLL et retourne une liste de dictionnaires
    contenant la question, son annotation et un champ `template_id` vide.
    """
    questions = []
    current_question = {"question": "", "entity_tagging": [], "template_id": ""}

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            if not line:
                # Nouvelle question trouvée, on sauvegarde la précédente
                if current_question["question"]:
                    questions.append(current_question)
                current_question = {"question": "", "entity_tagging": [], "template_id": ""}
                continue

            # Lecture du token et du tag
            parts = line.split()
            if len(parts) < 2:
                continue  # Évite les lignes mal formatées

            token, tag = parts[0], parts[-1]  # Dernière colonne = tag

            # Ajout du token à la question
            current_question["question"] += f" {token}" if current_question["question"] else token

            # Ajout du token et son tag dans la structure
            current_question["entity_tagging"].append({"token": token, "tag": tag})

    return questions

# 📌 Charger toutes les questions
train_questions = parse_conll_file(train_file)
dev_questions = parse_conll_file(dev_file)
test_questions = parse_conll_file(test_file)

# 📌 Fusionner toutes les questions
all_questions = train_questions + dev_questions + test_questions

# 📌 Sauvegarde au format JSON **avec tokens et tags sur une seule ligne**
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(all_questions, f, ensure_ascii=False, indent=4)

print(f"✅ Fichier `{output_json}` généré avec {len(all_questions)} questions ! 🚀")
