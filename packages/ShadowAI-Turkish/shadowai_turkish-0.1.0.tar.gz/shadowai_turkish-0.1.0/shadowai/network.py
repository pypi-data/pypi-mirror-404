import random
import math

class NeuralNetwork:
    """
    Online öğrenebilen basit sinir ağı.
    """
    def __init__(self, lr=0.01):
        self.lr = lr
        self.weights = {}

    def forward(self, vec):
        score = 0
        for k, v in vec.items():
            w = self.weights.get(k, random.uniform(-1, 1))
            score += w * v
            self.weights[k] = w
        return math.tanh(score)

    def learn(self, vec, target):
        output = self.forward(vec)
        error = target - output
        for k in vec:
            self.weights[k] += self.lr * error
