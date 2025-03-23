from flair.models import TextClassifier
from classify_questions import *
from entity_mapping import *
from preprocessing_lemmatized_new import *
from entity_type_tagging import *
from verif_template import * 
from test_sparql_queries import *
from sparql import *

model = TextClassifier.load("template_classifier_model/best-model.pt")

if __name__ == "__main__":
    # Charger le dictionnaire DBpedia depuis "dbr_dict.json"
    dbr_dict = load_json("dbr_dict.json")
    
    # Demander à l'utilisateur de saisir la requête
    question = input("Veuillez saisir votre requête : ")

    payload = {
        "question": question,
        "entity_tagging": [],
        "template_id": "",
        "mapping": {},
        "executed": True  # Valeur par défaut ; elle sera mise à jour après exécution
    }

    # Appel à la fonction de tagging qui retourne un dictionnaire
    data = tag_entities_with_bilstm("model/best-model.pt", [question])
    # Transformation de la sortie en une liste de dictionnaires
    output_data = {}
    for q, token_tuples in data.items():
        output_data[q] = [{"token": token, "tag": tag} for token, tag in token_tuples]
    if question in output_data:
        payload["entity_tagging"] = output_data[question]
    
    # Mapping des entités
    payload["mapping"] = perform_entity_mapping(payload["question"], payload["entity_tagging"], dbr_dict)
    
    # Attribution du template
    payload["template_id"] = predict_template(payload["question"], model)
    payload["template_id"] = predire_template(payload)

    # Exécution de la requête selon le template détecté
    if payload["template_id"] == 'unknown':
        result = process_single_question(payload["question"])
    else:
        result = process_single_query(payload)
    
    # Si la requête a échoué (ex: executed == False), on passe en mode "ChatGPT"
    if not result.get("executed", True):
        print("La requête a échoué. Passage en mode ChatGPT pour la génération de la question en langage naturel.")
        result = process_single_question(payload["question"])
    
    print(result)
