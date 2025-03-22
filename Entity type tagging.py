from flair.data import Sentence
from flair.models import SequenceTagger

def tag_entities_with_bilstm(model_path, questions):
    """
    Applique un modèle BiLSTM-CRF Flair à une liste de questions et retourne l'annotation token/tag.
    
    Args:
        model_path (str): Chemin vers le modèle entraîné (.pt).
        questions (list): Liste de chaînes de questions.
        
    Returns:
        dict: Un dictionnaire avec la question en clé et la liste des (token, tag) en valeur.
    """
    model = SequenceTagger.load(model_path)
    results = {}

    for question in questions:
        sentence = Sentence(question)
        model.predict(sentence)
        token_tags = []

        for token in sentence:
            label = token.get_labels(model.tag_type)[0].value if token.get_labels(model.tag_type) else "O"
            token_tags.append((token.text, label))

        results[question] = token_tags

    return results
