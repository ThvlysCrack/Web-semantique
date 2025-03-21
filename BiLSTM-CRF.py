import flair
from flair.data import Corpus, Sentence
from flair.datasets import ColumnCorpus
from flair.embeddings import WordEmbeddings, FlairEmbeddings, StackedEmbeddings
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

# 📌 1️⃣ Définition des colonnes pour le fichier CoNLL
columns = {0: "text", -1: "ner"}  # La dernière colonne est toujours la bonne étiquette

data_folder = "data"
# 📌 2️⃣ Chargement des fichiers d'entraînement
# 📌 Dossier où se trouvent `train.conll`, `dev.conll`, `test.conll`
corpus: Corpus = ColumnCorpus(data_folder, columns,
                              train_file="train.conll",
                              dev_file="dev.conll",
                              test_file="test.conll")

# 📌 3️⃣ Définition des étiquettes (O, R-B, R-I, C-B, C-I, V-B, etc.)
tag_type = "ner"
tag_dictionary = corpus.make_tag_dictionary(tag_type=tag_type)

# 📌 4️⃣ Embeddings utilisés pour l'entraînement
embedding_types = [
    WordEmbeddings("glove"),
    FlairEmbeddings("news-forward"),
    FlairEmbeddings("news-backward"),
]

embeddings = StackedEmbeddings(embeddings=embedding_types)

# 📌 5️⃣ Définition du modèle BiLSTM-CRF
tagger = SequenceTagger(hidden_size=256,
                        embeddings=embeddings,
                        tag_dictionary=tag_dictionary,
                        tag_type=tag_type,
                        use_crf=True)

# 📌 6️⃣ Entraînement du modèle
trainer = ModelTrainer(tagger, corpus)

trainer.train("model",
              learning_rate=0.1,
              mini_batch_size=32,
              max_epochs=50)

# 📌 7️⃣ Chargement du modèle et test sur une phrase
model = SequenceTagger.load("model/best-model.pt")

test_sentence = Sentence("Who is the CEO of Apple?")
model.predict(test_sentence)

print("📝 Résultats de la prédiction :")
print(test_sentence.to_tagged_string())
