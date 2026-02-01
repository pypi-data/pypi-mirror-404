from .vectorizer import Vectorizer
from .network import NeuralNetwork

class ShadowAI:
    """
    ShadowAI – öğrenen, sana ait yapay zeka.

    Metotlar:
    - ask(text)
    - teach(text, positive=True)
    """
    def __init__(self):
        self.vectorizer = Vectorizer()
        self.brain = NeuralNetwork()

    def ask(self, text):
        vec = self.vectorizer.encode(text)
        score = self.brain.forward(vec)

        if score > 0.5:
            return "Bu konuda bilgiliyim."
        elif score > 0:
            return "Biraz bilgim var."
        else:
            return "Bunu öğrenmem gerekiyor."

    def teach(self, text, positive=True):
        vec = self.vectorizer.encode(text)
        self.brain.learn(vec, 1 if positive else -1)
