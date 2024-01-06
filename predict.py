import pickle
from sklearn.feature_extraction.text import CountVectorizer
import plotly.express as px
import pandas as pd
import re

class Predictor():

    def __init__(self):
        self.models = {}
        model_names = ['cEXT', 'cNEU', 'cAGR', 'cCON', 'cOPN']
        for name in model_names:
            model = pickle.load(open(f"data/models/{name}.p", "rb"))
            self.models[name] = model

        self.vectorizer_31 = pickle.load(open("data/models/vectorizer_31.p", "rb"))
        self.vectorizer_30 = pickle.load(open("data/models/vectorizer_30.p", "rb"))

    def predict_personality(self, text):
        sentences = re.split("(?<=[.!?]) +", text)
        text_vector_31 = self.vectorizer_31.transform(sentences)
        text_vector_30 = self.vectorizer_30.transform(sentences)

        result = {}
        for name, model in self.models.items():
            prediction = model.predict(text_vector_31)
            result[f'pred_prob_{name}'] = prediction[0]

        return result

if __name__ == '__main__':
    P = Predictor()
   
