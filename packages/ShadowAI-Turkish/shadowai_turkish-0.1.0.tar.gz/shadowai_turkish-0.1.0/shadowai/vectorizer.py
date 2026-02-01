class Vectorizer:
    """
    Metni sayısal vektöre çevirir.
    """
    def __init__(self):
        self.vocab = {}

    def encode(self, text):
        vec = {}
        for w in text.lower().split():
            if w not in self.vocab:
                self.vocab[w] = len(self.vocab) + 1
            vec[w] = vec.get(w, 0) + 1
        return vec
