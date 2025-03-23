from flair.models import TextClassifier
from classify_questions import *

model = TextClassifier.load("template_classifier_model/best-model.pt")
result = predict_template("is antonella the wife of Lionel Messi?", model)
print("Template prédit :", result)
