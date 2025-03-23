import json
import spacy
import numpy as np
from collections import Counter

def cosine_similarity(vec1, vec2):
    """Calcule la similarité cosinus entre deux vecteurs numpy."""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def load_template_map(filepath):
    """Charge le fichier template_map.json."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def get_dependency_distribution(text, nlp):
    """
    Extrait la distribution des étiquettes de dépendance pour une phrase.
    Retourne un Counter sous forme de dictionnaire {dep_label: count}.
    """
    doc = nlp(text)
    dep_labels = [token.dep_ for token in doc]
    return Counter(dep_labels)

def counter_to_vector(counter, vocabulary):
    """Convertit un Counter en vecteur numpy selon l'ordre du vocabulaire."""
    return np.array([counter.get(label, 0) for label in vocabulary], dtype=float)

def compute_structure_similarity(text1, text2, nlp):
    """
    Calcule la similarité entre la structure syntaxique de deux textes
    en comparant la distribution de leurs étiquettes de dépendance.
    """
    dist1 = get_dependency_distribution(text1, nlp)
    dist2 = get_dependency_distribution(text2, nlp)
    vocabulary = set(dist1.keys()).union(set(dist2.keys()))
    vocabulary = sorted(vocabulary)
    vec1 = counter_to_vector(dist1, vocabulary)
    vec2 = counter_to_vector(dist2, vocabulary)
    return cosine_similarity(vec1, vec2)

def predict_template_with_confidence(entity_tagging, question_text, nlp):
    """
    Prédit le template de la question et renvoie un score de confiance selon les règles heuristiques.
    
    Règles appliquées :
      - Si la question est booléenne (commence par "is", "are", "was", "were"), renvoyer ("D", 1.0).
      - Filtrer les tokens dont le tag n'est pas "N" (considérant V, E, C, R).
      - Regrouper ces tokens par continuité.
         Si plusieurs groupes sont détectés, la question est ambiguë → ("unknown", None).
      - Dans le groupe unique, repérer le premier token de type "V" et le premier token de type "E".
         * Si le token "V" apparaît avant le token "E", renvoyer ("A", 0.9).
         * Sinon, renvoyer ("B", 0.9).
      - Si l'un des types "V" ou "E" est absent, renvoyer ("unknown", None).
    """
    lower_q = question_text.lower().strip()
    if lower_q.startswith(("is ", "are ", "was ", "were ")):
        return ("D", 1.0)
    
    # Conserver uniquement les tokens dont le tag commence par V, E, C, ou R
    filtered = [(idx, token_info.get("tag", "")[0])
                for idx, token_info in enumerate(entity_tagging)
                if token_info.get("tag", "") and token_info.get("tag", "")[0] in {"V", "E", "C", "R"}]
    
    if not filtered:
        return ("unknown", None)
    
    # Regrouper par continuité : si la différence entre deux indices consécutifs > 1, c'est un nouveau groupe
    groups = []
    current_group = [filtered[0]]
    for current in filtered[1:]:
        if current[0] == current_group[-1][0] + 1:
            current_group.append(current)
        else:
            groups.append(current_group)
            current_group = [current]
    groups.append(current_group)
    
    if len(groups) != 1:
        return ("unknown", None)
    
    # Dans le groupe unique, rechercher le premier token de type V et E
    group = groups[0]
    first_v = None
    first_e = None
    for idx, tag in group:
        if first_v is None and tag == "V":
            first_v = idx
        if first_e is None and tag == "E":
            first_e = idx
        if first_v is not None and first_e is not None:
            break
    
    if first_v is None or first_e is None:
        return ("unknown", None)
    elif first_v < first_e:
        return ("A", 0.9)
    else:
        return ("B", 0.9)

def select_best_template_using_structure(test_question, template_map, nlp):
    """
    Compare la structure syntaxique de la question test avec celle de l'exemple de chaque template
    du template_map (via la distribution des dépendances) et retourne le template avec le meilleur score.
    """
    best_template = None
    best_score = -1.0
    for template_id, info in template_map.items():
        example = info.get("example", "")
        score = compute_structure_similarity(test_question, example, nlp)
        if score > best_score:
            best_score = score
            best_template = template_id
    return best_template, best_score

if __name__ == "__main__":
    # Charger le modèle transformer en_core_web_trf
    nlp = spacy.load("en_core_web_trf")
    
    # Charger le template_map.json
    with open("template_map.json", "r", encoding="utf-8") as f:
        template_map = json.load(f)
    
    # Exemple de question test
    test_question = "Who is the CEO of Apple?"
    # Exemple d'annotation entity_tagging pour cette question
    tagging_example = [
        {"token": "Who", "tag": "V-B"},
        {"token": "is", "tag": "R-B"},
        {"token": "the", "tag": "N"},
        {"token": "CEO", "tag": "C-B"},
        {"token": "of", "tag": "R-B"},
        {"token": "Apple", "tag": "E-B"},
        {"token": "?", "tag": "N"}
    ]
    
    tpl_pred, conf_pred = predict_template_with_confidence(tagging_example, test_question, nlp)
    print(f"Règles heuristiques : Template prédit = {tpl_pred}, Score = {conf_pred}")
    
    best_tpl, score = select_best_template_using_structure(test_question, template_map, nlp)
    print(f"Comparaison structurelle : Template choisi = {best_tpl} avec un score de {score:.2f}")
