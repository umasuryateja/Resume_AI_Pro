"""
Pure-Python ML Module
TF-IDF vectorizer + cosine similarity + Multinomial Naive Bayes — zero compiled DLL dependencies.
"""

import math
import re
from collections import Counter, defaultdict


# ─────────────────────────────────────────────────────────────────────────────
# Tokenization helpers
# ─────────────────────────────────────────────────────────────────────────────

STOP_WORDS = {
    "i","me","my","myself","we","our","ours","ourselves","you","your","yours",
    "yourself","he","him","his","himself","she","her","hers","herself","it","its",
    "itself","they","them","their","theirs","themselves","what","which","who",
    "whom","this","that","these","those","am","is","are","was","were","be","been",
    "being","have","has","had","having","do","does","did","doing","a","an","the",
    "and","but","if","or","because","as","until","while","of","at","by","for",
    "with","about","against","between","into","through","during","before","after",
    "above","below","to","from","up","down","in","out","on","off","over","under",
    "again","further","then","once","here","there","when","where","why","how","all",
    "both","each","few","more","most","other","some","such","no","nor","not","only",
    "own","same","so","than","too","very","s","t","can","will","just","don","should",
    "now","d","ll","m","o","re","ve","y","ain","aren","couldn","didn","doesn",
    "hadn","hasn","haven","isn","ma","mightn","mustn","needn","shan","shouldn",
    "wasn","weren","won","wouldn","also","may","might","must","shall","would","could",
}


def tokenize(text: str, ngrams: int = 1) -> list:
    """Tokenize text into unigrams (and optionally bigrams)."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = [t for t in text.split() if t not in STOP_WORDS and len(t) > 2]
    result = list(tokens)
    if ngrams >= 2:
        bigrams = [tokens[i] + '_' + tokens[i+1] for i in range(len(tokens)-1)]
        result.extend(bigrams)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TF-IDF (in-memory, pure Python)
# ─────────────────────────────────────────────────────────────────────────────

class TFIDFVectorizer:
    def __init__(self, max_features: int = 8000, ngrams: int = 2):
        self.max_features = max_features
        self.ngrams = ngrams
        self.vocab: dict = {}          # token -> index
        self.idf: list = []            # idf scores indexed by vocab index
        self._fitted = False

    def fit(self, corpus: list):
        N = len(corpus)
        tokenized = [tokenize(doc, self.ngrams) for doc in corpus]
        # Document frequency
        df: Counter = Counter()
        for tokens in tokenized:
            df.update(set(tokens))
        # Filter by max_features (top by df)
        top_tokens = [tok for tok, _ in df.most_common(self.max_features)]
        self.vocab = {tok: i for i, tok in enumerate(top_tokens)}
        # IDF: log((N+1)/(df+1)) + 1  (sklearn-style smooth)
        self.idf = [
            math.log((N + 1) / (df[tok] + 1)) + 1
            for tok in top_tokens
        ]
        self._fitted = True
        return self

    def transform(self, corpus: list) -> list:
        """Return list of sparse dicts {vocab_idx: tfidf_weight}"""
        vectors = []
        for doc in corpus:
            tokens = tokenize(doc, self.ngrams)
            tf = Counter(tokens)
            total = sum(tf.values()) or 1
            vec: dict = {}
            for tok, cnt in tf.items():
                if tok in self.vocab:
                    idx = self.vocab[tok]
                    tfidf = (cnt / total) * self.idf[idx]
                    vec[idx] = tfidf
            # L2 normalise
            norm = math.sqrt(sum(v*v for v in vec.values())) or 1.0
            vec = {k: v/norm for k, v in vec.items()}
            vectors.append(vec)
        return vectors

    def fit_transform(self, corpus: list) -> list:
        self.fit(corpus)
        return self.transform(corpus)


def cosine_sim(vec_a: dict, vec_b: dict) -> float:
    """Cosine similarity between two sparse TF-IDF vectors."""
    dot = sum(vec_a.get(k, 0) * v for k, v in vec_b.items())
    # Both are already L2-normalised, so magnitudes = 1
    return min(dot, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# Multinomial Naive Bayes (log-probability, Laplace smoothing)
# ─────────────────────────────────────────────────────────────────────────────

class NaiveBayesClassifier:
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.classes_: list = []
        self._log_prior: dict = {}
        self._log_cond: dict = {}   # class -> {feat_idx: log_prob}
        self._vocab_size: int = 0

    def fit(self, X_vecs: list, y: list, vocab_size: int):
        """X_vecs: list of sparse dicts from TFIDFVectorizer.transform"""
        self._vocab_size = vocab_size
        self.classes_ = sorted(set(y))
        N = len(y)
        class_counts: Counter = Counter(y)

        for cls in self.classes_:
            self._log_prior[cls] = math.log(class_counts[cls] / N)
            # Accumulate feature sums for this class
            feat_sum: defaultdict = defaultdict(float)
            total = 0.0
            for vec, label in zip(X_vecs, y):
                if label == cls:
                    for idx, val in vec.items():
                        feat_sum[idx] += val
                        total += val
            # Log conditional probabilities with Laplace smoothing
            denom = math.log(total + self.alpha * vocab_size)
            self._log_cond[cls] = {
                idx: math.log(val + self.alpha) - denom
                for idx, val in feat_sum.items()
            }
            # Store default log-prob for unseen features
            self._log_cond[cls]['__default__'] = math.log(self.alpha) - denom

        return self

    def predict_proba(self, X_vecs: list) -> list:
        results = []
        for vec in X_vecs:
            scores = {}
            for cls in self.classes_:
                score = self._log_prior[cls]
                default = self._log_cond[cls].get('__default__', -20)
                for idx, val in vec.items():
                    lp = self._log_cond[cls].get(idx, default)
                    score += val * lp
                scores[cls] = score
            # Softmax to convert log-scores to probabilities
            max_s = max(scores.values())
            exp_s = {c: math.exp(s - max_s) for c, s in scores.items()}
            total = sum(exp_s.values())
            proba = {c: v/total for c, v in exp_s.items()}
            results.append(proba)
        return results

    def predict(self, X_vecs: list) -> list:
        probas = self.predict_proba(X_vecs)
        return [max(p, key=p.get) for p in probas]


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline wrapper
# ─────────────────────────────────────────────────────────────────────────────

class ResumeClassifierPipeline:
    def __init__(self):
        self.vectorizer = TFIDFVectorizer(max_features=8000, ngrams=2)
        self.classifier = NaiveBayesClassifier(alpha=0.5)
        self.classes_: list = []

    def fit(self, texts: list, labels: list):
        X = self.vectorizer.fit_transform(texts)
        vocab_size = len(self.vectorizer.vocab)
        self.classifier.fit(X, labels, vocab_size)
        self.classes_ = self.classifier.classes_
        return self

    def predict(self, texts: list) -> list:
        X = self.vectorizer.transform(texts)
        return self.classifier.predict(X)

    def predict_proba_dict(self, texts: list) -> list:
        X = self.vectorizer.transform(texts)
        return self.classifier.predict_proba(X)


def compute_similarity(text1: str, text2: str) -> float:
    """Compute cosine similarity between two raw texts (pure Python)."""
    if not text1.strip() or not text2.strip():
        return 0.0
    vect = TFIDFVectorizer(max_features=5000, ngrams=2)
    vecs = vect.fit_transform([text1, text2])
    return cosine_sim(vecs[0], vecs[1])
