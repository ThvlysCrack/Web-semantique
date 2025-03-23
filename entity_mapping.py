import json
import re

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_text(text):
    """
    Normalise le texte en minuscules et en supprimant les espaces superflus.
    """
    return text.strip().lower()

def default_mapping(group_tokens, tag_type):
    """
    Génère une valeur de mapping par défaut pour un groupe de tokens.
    Si tag_type est "E", retourne "dbr:" suivi des tokens avec la première lettre en majuscule, joints par des underscores.
    Sinon (pour "C" ou "R"), retourne "dbo:" suivi de la même manière.
    """
    tokens_cap = [token.capitalize() for token in group_tokens]
    joined = "_".join(tokens_cap)
    if tag_type == "E":
        return "dbr:" + joined
    else:
        return "dbo:" + joined

def group_tokens_by_category(entity_tagging):
    """
    Regroupe les tokens consécutifs dont le tag commence par l'une des lettres E, C ou R.
    Retourne une liste de tuples : (group_text, tag_type)
    Par exemple, pour une annotation sur ["Alec", tag "E-B"], ["Guinness", tag "E-I"],
    retourne [("Alec Guinness", "E")].
    """
    groups = []
    current_group = []
    current_type = None  # "E", "C" ou "R"
    
    for entry in entity_tagging:
        token = entry["token"]
        tag = entry["tag"]
        if tag.startswith(("E", "C", "R")):
            t_type = tag[0]
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
            if current_group:
                groups.append((" ".join(current_group), current_type))
                current_group = []
                current_type = None
    if current_group:
        groups.append((" ".join(current_group), current_type))
    return groups

def perform_entity_mapping(question, entity_tagging, dbr_dict):
    """
    Réalise l'entity mapping sur une question en se basant sur ses annotations.
    
    Args:
        question (str): La question en texte brut (pour information).
        entity_tagging (list): Liste de dictionnaires avec "token" et "tag".
        dbr_dict (dict): Dictionnaire DBpedia associant des keywords à leurs URI.
    
    Returns:
        dict: Un dictionnaire de mapping sous la forme { groupe d'entités : URI }.
    """
    mapping = {}
    groups = group_tokens_by_category(entity_tagging)
    for group_text, tag_type in groups:
        normalized = normalize_text(group_text)
        if normalized in dbr_dict:
            mapping[group_text] = dbr_dict[normalized]
        else:
            mapping[group_text] = default_mapping(group_text.split(), tag_type)
    return mapping

