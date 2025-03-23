from flair.data import Sentence

def predict_template(question, classifier_model):
    """
    Prédit le template associé à une question en utilisant le modèle de template classifier.

    Args:
        question (str): La question en langage naturel.
        classifier_model (TextClassifier): Le modèle Flair entraîné pour la classification des templates.

    Returns:
        str: Le template prédit (par exemple "A", "B", "D" ou "unknown").
    """
    # Créer l'objet Sentence à partir de la question
    sentence = Sentence(question)
    
    # Appliquer le modèle pour prédire le template
    classifier_model.predict(sentence)
    
    # Récupérer le label "template" prédit
    labels = sentence.get_labels("template")
    if labels:
        return labels[0].value
    else:
        return "unknown"
