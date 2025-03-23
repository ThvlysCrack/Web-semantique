import json
import random
from collections import defaultdict

from flair.data import Sentence, Corpus
from flair.embeddings import WordEmbeddings, FlairEmbeddings, StackedEmbeddings, DocumentPoolEmbeddings
from flair.models.text_classification_model import TextClassifier
from flair.trainers import ModelTrainer

def load_template_data(json_file):
    """
    Charge le fichier JSON contenant les questions annotées avec leur template_id.
    Seules les questions dont le template_id n'est pas vide sont retenues.
    Chaque question est transformée en un objet Sentence auquel on ajoute le label "template".
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    sentences = []
    for item in data:
        if item.get("template_id", "") != "":
            s = Sentence(item["question"])
            s.add_label("template", item["template_id"])
            sentences.append(s)
    return sentences

def stratified_split(sentences, train_ratio=0.8, dev_ratio=0.1, test_ratio=0.1, seed=42):
    """
    Répartit les phrases en ensembles train/dev/test en conservant la distribution des classes.
    """
    random.seed(seed)
    class_to_sentences = defaultdict(list)

    for s in sentences:
        label = s.get_labels("template")[0].value
        class_to_sentences[label].append(s)

    train_set, dev_set, test_set = [], [], []

    for label, sents in class_to_sentences.items():
        random.shuffle(sents)
        n = len(sents)
        n_train = int(train_ratio * n)
        n_dev = int(dev_ratio * n)

        train_set.extend(sents[:n_train])
        dev_set.extend(sents[n_train:n_train + n_dev])
        test_set.extend(sents[n_train + n_dev:])

    return train_set, dev_set, test_set

# --- Chargement des données et split stratifié
all_sentences = load_template_data("mapped_classified_questions.json")
train_sentences, dev_sentences, test_sentences = stratified_split(all_sentences)
corpus = Corpus(train=train_sentences, dev=dev_sentences, test=test_sentences)

def print_label_distribution(split_name, sentences):
    from collections import Counter
    labels = [s.get_labels("template")[0].value for s in sentences]
    counts = Counter(labels)
    print(f"📊 Distribution des classes dans {split_name} :", dict(counts))

print_label_distribution("train", train_sentences)
print_label_distribution("dev", dev_sentences)
print_label_distribution("test", test_sentences)

# --- Embeddings
embedding_types = [
    WordEmbeddings("glove"),
    FlairEmbeddings("news-forward"),
    FlairEmbeddings("news-backward")
]
stacked_embeddings = StackedEmbeddings(embeddings=embedding_types)
document_embeddings = DocumentPoolEmbeddings([stacked_embeddings])

# --- Création du classifieur
label_dictionary = corpus.make_label_dictionary(label_type="template")
classifier = TextClassifier(embeddings=document_embeddings, 
                            label_type="template", 
                            label_dictionary=label_dictionary)
classifier.multi_label = False

# --- Entraînement
trainer = ModelTrainer(classifier, corpus)
trainer.train("template_classifier_model",
              learning_rate=0.1,
              mini_batch_size=16,
              max_epochs=50,
              embeddings_storage_mode='none')

# --- Chargement du modèle entraîné
model_path = "template_classifier_model/best-model.pt"
try:
    model = TextClassifier.load(model_path)
except Exception:
    model = TextClassifier.load("template_classifier_model/final-model.pt")

# --- Inférence exemple
test_sentence = Sentence("Who is the CEO of Apple?")
model.predict(test_sentence)
print("📝 Résultat de la prédiction pour une question test :")
print(test_sentence.to_tagged_string())
