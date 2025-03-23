import json
import re

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def normalize_text(text):
    """
    Normalise le texte en minuscules et en supprimant les espaces superflus.
    """
    return text.strip().lower()

def default_mapping(group_tokens, tag_type):
    """
    Génère une valeur de mapping par défaut pour un groupe de tokens.
    Si tag_type est "E", on retourne "dbr:" suivi de chaque token capitalisé et joints par des underscores.
    Si tag_type est "C" ou "R", on retourne "dbo:" suivi de chaque token capitalisé et joints par des underscores.
    """
    # Capitaliser chaque token
    tokens_cap = [token.capitalize() for token in group_tokens]
    joined = "_".join(tokens_cap)
    if tag_type == "E":
        return "dbr:" + joined
    else:
        return "dbo:" + joined

def group_tokens_by_category(entity_tagging):
    """
    Parcourt la liste entity_tagging et regroupe les tokens contigus ayant le même préfixe
    parmi {"E", "C", "R"}.
    
    Retourne une liste de tuples : (group_text, tag_type)
    Exemple : Pour l'annotation sur "Alec Guinness" avec tags "E-B" et "E-I", 
    retourne [("Alec Guinness", "E")].
    """
    groups = []
    current_group = []
    current_type = None  # "E", "C" ou "R"
    
    for entry in entity_tagging:
        token = entry["token"]
        tag = entry["tag"]
        # On ne traite que les tags qui commencent par E, C ou R
        if tag.startswith(("E", "C", "R")):
            t_type = tag[0]  # le premier caractère (E, C, ou R)
            if current_type is None:
                current_type = t_type
                current_group.append(token)
            else:
                if t_type == current_type:
                    current_group.append(token)
                else:
                    groups.append((" ".join(current_group), current_type))
                    current_group = [token]
                    current_type = t_type
        else:
            # Si le token n'appartient pas à E, C ou R et un groupe est en cours, on le termine.
            if current_group:
                groups.append((" ".join(current_group), current_type))
                current_group = []
                current_type = None
    # Ajouter le groupe restant s'il existe
    if current_group:
        groups.append((" ".join(current_group), current_type))
    return groups

def add_entity_mapping(questions, dbr_dict):
    """
    Pour chaque question de la liste, regroupe les tokens pour former les entités (ou classes, ou relations)
    et ajoute une clé "mapping" dans le dictionnaire de la question.
    
    Le mapping associe le groupe (tel qu'il apparaît dans la question) à la valeur présente dans dbr_dict (si trouvée),
    sinon à une valeur par défaut générée automatiquement.
    """
    for q in questions:
        mapping = {}
        # Regrouper les tokens pour les tags E, C et R
        groups = group_tokens_by_category(q.get("entity_tagging", []))
        for group_text, tag_type in groups:
            normalized = normalize_text(group_text)
            if normalized in dbr_dict:
                mapping[group_text] = dbr_dict[normalized]
            else:
                mapping[group_text] = default_mapping(group_text.split(), tag_type)
        q["mapping"] = mapping
    return questions

if __name__ == "__main__":
    # Charger le fichier des questions préclassifiées (par exemple, classified_questions.json)
    questions = load_json("classified_questions.json")
    # Charger le dictionnaire DBpedia (dbr_dict.json)
    dbr_dict = load_json("dbr_dict.json")
    
    # Ajouter le mapping pour chaque question
    mapped_questions = add_entity_mapping(questions, dbr_dict)
    
    # Sauvegarder le résultat dans un nouveau fichier
    save_json(mapped_questions, "mapped_classified_questions.json")
    print("✅ Le fichier 'mapped_classified_questions.json' a été généré avec succès !")
