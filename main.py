from flair.models import TextClassifier
from classify_questions import *
from entity_mapping import *

model = TextClassifier.load("template_classifier_model/best-model.pt")
result = predict_template("is antonella the wife of Lionel Messi?", model)
print("Template prédit :", result)

if __name__ == "__main__":
    # Charger le dictionnaire DBpedia depuis "dbr_dict.json"
    dbr_dict = load_json("dbr_dict.json")
    
    # Exemple de question et son entity_tagging issu du prétraitement
    question = "Who wrote the Hunger Games?"
    entity_tagging = [
        {"token": "Who", "tag": "V-B"},
        {"token": "wrote", "tag": "R-B"},
        {"token": "the", "tag": "N"},
        {"token": "Hunger", "tag": "E-B"},
        {"token": "Games", "tag": "E-I"},
        {"token": "?", "tag": "N"}
    ]
    
    mapping_result = perform_entity_mapping(question, entity_tagging, dbr_dict)
    print("Entity Mapping:", mapping_result)
