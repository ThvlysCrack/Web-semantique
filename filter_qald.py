import json

def filter_english_questions(input_file, output_file):
    """
    Charge un fichier QALD-multilingual et conserve uniquement la question en anglais pour chaque entrée.
    Le résultat est sauvegardé dans un nouveau fichier JSON.
    """
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Nouveau dictionnaire qui contiendra uniquement les questions en anglais
    filtered_data = {"questions": []}
    
    for q_item in data.get("questions", []):
        # Créer une copie de l'entrée avec son identifiant (si présent)
        new_entry = {}
        if "id" in q_item:
            new_entry["id"] = q_item["id"]
        # Conserver uniquement la version en anglais dans le tableau "question"
        english_questions = [q for q in q_item.get("question", []) if q.get("language") == "en"]
        if english_questions:
            new_entry["question"] = english_questions
            # Si d'autres clés existent (query, answers, etc.), on peut aussi les copier
            for key in q_item:
                if key not in ["question", "id"]:
                    new_entry[key] = q_item[key]
            filtered_data["questions"].append(new_entry)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Fichier filtré sauvegardé dans : {output_file}")

'''
filter_english_questions("qald-7-train-multilingual.json", "qald-7-train-en.json")
filter_english_questions("qald-9-train-multilingual.json", "qald-9-train-en.json")
filter_english_questions("qald-7-test-multilingual.json", "qald-7-test-en.json")
filter_english_questions("qald-9-test-multilingual.json", "qald-9-test-en.json")'''