import spacy

# Charger le modèle NLP de spaCy
nlp = spacy.load("en_core_web_trf")

def correct_pos(token, context):
    """
    Corrige les erreurs courantes de POS-tags en fonction du contexte global.
    """
    if token.text in ["Where", "When"]:
        return "ADV"  # "Where" et "When" sont toujours des adverbes interrogatifs
    if token.text in ["Who", "What"]:
        return "PRON"  # "Who" et "What" sont des pronoms
    if token.text in ["Which"] and context[token.i + 1].pos_ == "NOUN":
        return "DET"  # "Which" est un déterminant avant un nom
    return token.pos_  # Sinon, garder le POS d'origine

def preprocess_question(question):
    """
    Prétraitement avancé des questions :
    - Tokenisation et lemmatisation
    - Fusion des entités multi-mots automatiquement
    - Étiquetage grammatical (POS-tagging)
    - Détection des entités nommées
    - Correction automatique des POS-tags et des entités mal classées
    """
    doc = nlp(question)

    # 📌 Fusion des entités multi-mots détectées par spaCy
    entity_dict = {ent.text: ent.label_ for ent in doc.ents}

    # 📌 Fusion des noms propres adjacents (ex: "Star Wars", "New York")
    merged_tokens = []
    merged_lemmas = []
    merged_pos_tags = []
    merged_entities = []
    
    i = 0
    while i < len(doc):
        token = doc[i]
        found_entity = False

        # 📌 Vérifier si ce token appartient à une entité multi-mots
        for ent_text in entity_dict:
            ent_words = ent_text.split()
            if doc[i:i+len(ent_words)].text == ent_text:
                merged_tokens.append(ent_text)
                merged_lemmas.append(ent_text)  # Pas de lemmatisation pour les entités
                merged_pos_tags.append((ent_text, "PROPN"))  # Une entité est toujours PROPN
                merged_entities.append((ent_text, entity_dict[ent_text]))  # Ajouter en tant qu'entité
                i += len(ent_words)  # Sauter les mots déjà fusionnés
                found_entity = True
                break

        # 📌 Fusion automatique des noms propres adjacents (ex: "Star Wars")
        if not found_entity and token.pos_ == "PROPN" and i + 1 < len(doc) and doc[i + 1].pos_ == "PROPN":
            entity_text = token.text + " " + doc[i + 1].text
            merged_tokens.append(entity_text)
            merged_lemmas.append(entity_text)
            merged_pos_tags.append((entity_text, "PROPN"))
            merged_entities.append((entity_text, "WORK_OF_ART"))  # Suppose qu'un nom propre fusionné est une entité
            i += 2
            continue

        if not found_entity:
            merged_tokens.append(token.text)
            merged_lemmas.append(token.lemma_)
            
            # 📌 Appliquer la correction des POS-tags contextuellement
            corrected_pos = correct_pos(token, doc)
            merged_pos_tags.append((token.text, corrected_pos))
            
            i += 1

    return {
        "tokens": merged_tokens,
        "lemmas": merged_lemmas,
        "pos_tags": merged_pos_tags,
        "entities": merged_entities
    }

# 📌 Liste de 10 questions générales pour tester
questions = [
    "Where is Fort Knox located?",
    "Who composed the music for Star Wars?",
    "What is the population of Germany?",
    "Which river flows through Paris?",
    "Who discovered penicillin?",
    "When was the Eiffel Tower built?",
    "What is the tallest mountain in the world?",
    "Which city is the capital of Japan?",
    "Who wrote the book The Catcher in the Rye?",
    "What is the currency used in Canada?"
]

# 📌 Exécuter le prétraitement sur chaque question
for i, question in enumerate(questions):
    print(f"\n📝 Question {i+1}: {question}")
    result = preprocess_question(question)
    
    for key, value in result.items():
        print(f"{key}: {value}")
