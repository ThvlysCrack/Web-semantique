import flair
from flair.data import Corpus, Sentence
from flair.datasets import ColumnCorpus
from flair.embeddings import WordEmbeddings, FlairEmbeddings, StackedEmbeddings
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

# 1️⃣ Définir les colonnes du CoNLL (token, tag)
columns = {0: "text", -1: "ner"}  # "ner" est le tag sans BIO

# 2️⃣ Dossier contenant les fichiers train.conll, dev.conll, test.conll
data_folder = "data"

# 3️⃣ Charger le corpus
corpus: Corpus = ColumnCorpus(
    data_folder,
    columns,
    train_file="train.conll",
    dev_file="dev.conll",
    test_file="test.conll"
)

# 4️⃣ Créer le dictionnaire des étiquettes (V, R, E, C, etc.)
tag_type = "ner"
tag_dictionary = corpus.make_tag_dictionary(tag_type=tag_type)

# 5️⃣ Définir les embeddings
embedding_types = [
    WordEmbeddings("glove"),
    FlairEmbeddings("news-forward"),
    FlairEmbeddings("news-backward"),
]
embeddings = StackedEmbeddings(embeddings=embedding_types)

# 6️⃣ Créer le modèle (CRF optionnel ici)
tagger = SequenceTagger(
    hidden_size=256,
    embeddings=embeddings,
    tag_dictionary=tag_dictionary,
    tag_type=tag_type,
    use_crf=True  # facultatif dans le format plat, tu peux mettre False aussi
)

# 7️⃣ Entraînement du modèle
trainer = ModelTrainer(tagger, corpus)
trainer.train(
    "model",
    learning_rate=0.001,            # 👈 Ajusté selon le tableau
    mini_batch_size=8,              # 👈 Batch size = 8
    max_epochs=100,                 # 👈 100 epochs comme spécifié
    embeddings_storage_mode='none',
    patience=100,                   # 👈 Forcer les 100 epochs
)

