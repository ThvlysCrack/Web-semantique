import spacy

# Charger le modèle NLP de spaCy
nlp = spacy.load("en_core_web_sm")

# 📌 Correction manuelle des POS-tags pour les entités et les mots-clés courants
POS_CORRECTIONS = {
    "Where": "ADV",  # Correction pour "Where"
    "Who": "PRON",   # Correction pour "Who"
    "What": "PRON",  # Correction pour "What"
    "Which": "DET",  # Correction pour "Which"
}

def preprocess_question(question):
    """
    Fonction de prétraitement avancé :
    - Tokenisation avancée
    - Fusion automatique des entités multi-mots
    - Lemmatisation
    - Étiquetage grammatical (POS-tagging)
    - Détection des entités nommées
    - Correction des POS-tags pour assurer la cohérence
    """
    doc = nlp(question)

    # 📌 Étape 1 : Extraire les entités détectées par spaCy
    entity_dict = {ent.text: ent.label_ for ent in doc.ents}

    # 📌 Étape 2 : Fusionner les entités multi-mots détectées
    merged_tokens = []
    merged_lemmas = []
    merged_pos_tags = []
    merged_entities = []
    
    i = 0
    while i < len(doc):
        token = doc[i]
        found_entity = False

        # Vérifier si ce token appartient à une entité multi-mots
        for ent_text in entity_dict:
            ent_words = ent_text.split()
            if doc[i:i+len(ent_words)].text == ent_text:
                merged_tokens.append(ent_text)
                merged_lemmas.append(ent_text)  # Pas de lemmatisation pour les entités
                
                # 📌 Correction manuelle des POS-tags si nécessaire
                corrected_pos = POS_CORRECTIONS.get(ent_text, "PROPN")
                merged_pos_tags.append((ent_text, corrected_pos))
                merged_entities.append((ent_text, entity_dict[ent_text]))  # Ajouter en tant qu'entité
                i += len(ent_words)  # Sauter les mots déjà fusionnés
                found_entity = True
                break

        if not found_entity:
            merged_tokens.append(token.text)
            merged_lemmas.append(token.lemma_)
            
            # 📌 Appliquer une correction si le token a une mauvaise classification POS
            corrected_pos = POS_CORRECTIONS.get(token.text, token.pos_)
            merged_pos_tags.append((token.text, corrected_pos))
            
            i += 1

    return {
        "tokens": merged_tokens,
        "lemmas": merged_lemmas,
        "pos_tags": merged_pos_tags,
        "entities": merged_entities
    }

# 📌 Test du prétraitement avec une phrase
question = "Where Fort Knox located?"
preprocessed_output = preprocess_question(question)

# 📌 Affichage des résultats
for key, value in preprocessed_output.items():
    print(f"{key}: {value}")
