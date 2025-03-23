import json
import re

def load_qald_questions(json_file):
    """
    Charge un fichier QALD-multilingual et retourne une liste d'entrées de questions (uniquement en anglais).
    Chaque entrée contient la question (string), le champ keywords et la requête SPARQL.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    questions = []
    for q in data.get("questions", []):
        # On ne garde que l'entrée en anglais
        for item in q.get("question", []):
            if item.get("language") == "en" and item.get("string"):
                entry = {
                    "question": item["string"],
                    "keywords": item.get("keywords", ""),  # Peut être vide
                    "sparql": q.get("query", {}).get("sparql", "")
                }
                questions.append(entry)
                break  # On ne prend qu'une version par question
    return questions

def extract_dbpedia_elements(sparql_query):
    """
    Extrait les éléments DBpedia de la requête SPARQL.
    Renvoie deux listes : ressources et propriétés.
    On recherche les patterns res:... ou dbr:... pour les ressources,
    et dbo:... pour les propriétés.
    """
    # Pattern pour ressources (res: ou dbr:)
    resource_pattern = r"(?:res:|dbr:)([A-Za-z0-9_]+)"
    # Pattern pour propriétés (dbo:)
    property_pattern = r"(?:dbo:)([A-Za-z0-9_]+)"
    
    resources = re.findall(resource_pattern, sparql_query)
    properties = re.findall(property_pattern, sparql_query)
    
    # On normalise (minuscule)
    resources = [r.lower() for r in resources]
    properties = [p.lower() for p in properties]
    
    return resources, properties

def build_dbr_dict(qald_files):
    """
    Parcourt la liste des fichiers QALD (filtrés pour l'anglais) et construit un dictionnaire
    qui associe les keywords aux éléments DBpedia correspondants extraits de la requête SPARQL.
    Avant d'ajouter une entrée, on vérifie qu'elle n'existe pas déjà.
    """
    dbr_dict = {}
    
    for file in qald_files:
        questions = load_qald_questions(file)
        for entry in questions:
            keywords_str = entry.get("keywords", "")
            sparql = entry.get("sparql", "")
            # On ne traite que si le champ keywords n'est pas vide
            if not keywords_str:
                continue
            # Séparer les keywords par virgule et nettoyer
            keywords = [kw.strip().lower() for kw in keywords_str.split(",") if kw.strip()]
            resources, properties = extract_dbpedia_elements(sparql)
            
            # Pour chaque keyword, on cherche si un élément extrait correspond (on peut utiliser 'in')
            for kw in keywords:
                # On regarde d'abord dans les ressources, puis dans les propriétés
                mapping = None
                for res in resources:
                    if kw in res or res in kw:
                        mapping = "dbr:" + res
                        break
                if mapping is None:
                    for prop in properties:
                        if kw in prop or prop in kw:
                            mapping = "dbo:" + prop
                            break
                # Si on a trouvé un mapping et qu'il n'est pas déjà présent, on l'ajoute
                if mapping is not None:
                    if kw not in dbr_dict:
                        dbr_dict[kw] = mapping
                    else:
                        # Optionnel : si le mapping diffère, on peut le signaler ou l'ignorer
                        if dbr_dict[kw] != mapping:
                            print(f"⚠️ Conflit pour '{kw}': déjà mappé à {dbr_dict[kw]}, tenté {mapping}.")
    return dbr_dict

if __name__ == "__main__":
    # Liste des fichiers QALD (supposons que vous avez déjà filtré pour l'anglais)
    qald_files = [
        "QALD_clean/qald-7-train-en.json",
        "QALD_clean/qald-7-test-en.json",
        "QALD_clean/qald-9-train-en.json",
        "QALD_clean/qald-9-test-en.json"
    ]
    
    dbr_dict = build_dbr_dict(qald_files)
    
    # Sauvegarder le dictionnaire dans un fichier JSON
    with open("dbr_dict.json", "w", encoding="utf-8") as f:
        json.dump(dbr_dict, f, ensure_ascii=False, indent=4)
    
    print("✅ dbr_dict.json généré avec succès !")
    print(json.dumps(dbr_dict, indent=4))
