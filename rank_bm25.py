"""
rank_bm25: BM25Okapi implementation for lexical keyword ranking.
================================================================
Provides standard BM25Okapi scoring over tokenized corpora.
"""

import math
from typing import List, Dict, Any, Optional, Callable


class BM25Okapi:
    """
    BM25Okapi probabilistic relevance scoring model.
    Score(D, Q) = sum_{t in Q} IDF(t) * (f(t, D) * (k1 + 1)) / (f(t, D) + k1 * (1 - b + b * (|D| / avgdl)))
    """

    def __init__(
        self,
        corpus: List[List[str]],
        tokenizer: Optional[Callable[[str], List[str]]] = None,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        self.tokenizer = tokenizer
        if tokenizer:
            self.corpus = [tokenizer(doc) if isinstance(doc, str) else doc for doc in corpus]
        else:
            self.corpus = corpus

        self.corpus_size = len(self.corpus)
        self.avgdl = sum(len(x) for x in self.corpus) / self.corpus_size if self.corpus_size > 0 else 0.0
        self.k1 = float(k1)
        self.b = float(b)
        self.epsilon = float(epsilon)

        self.doc_len = [len(x) for x in self.corpus]
        self.doc_freqs: List[Dict[str, int]] = []
        self.nd: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

        self._calc_idf()

    def _calc_idf(self):
        """Calculates Inverse Document Frequency (IDF) with BM25Okapi floor."""
        for doc in self.corpus:
            frequencies: Dict[str, int] = {}
            for word in doc:
                frequencies[word] = frequencies.get(word, 0) + 1
            self.doc_freqs.append(frequencies)
            for word in frequencies:
                self.nd[word] = self.nd.get(word, 0) + 1

        idf_sum = 0.0
        negative_idfs = []
        for word, freq in self.nd.items():
            # BM25Okapi formula: log((N - n + 0.5) / (n + 0.5) + 1)
            idf = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)
            self.idf[word] = idf
            idf_sum += idf
            if idf < 0:
                negative_idfs.append(word)

        average_idf = float(idf_sum) / len(self.idf) if self.idf else 0.0
        eps = self.epsilon * average_idf
        for word in negative_idfs:
            self.idf[word] = eps

    def get_scores(self, query: List[str]) -> List[float]:
        """Calculates BM25Okapi scores for all documents in the corpus given tokenized query."""
        scores = [0.0] * self.corpus_size
        if not self.corpus_size:
            return scores

        avg_len = self.avgdl if self.avgdl > 0 else 1.0

        for q in query:
            idf = self.idf.get(q, 0.0)
            if idf <= 0.0:
                continue

            for i in range(self.corpus_size):
                freq = self.doc_freqs[i].get(q, 0)
                if freq > 0:
                    numerator = freq * (self.k1 + 1.0)
                    denominator = freq + self.k1 * (1.0 - self.b + self.b * (self.doc_len[i] / avg_len))
                    if denominator > 0:
                        scores[i] += idf * (numerator / denominator)

        return scores

    def get_top_n(self, query: List[str], documents: List[Any], n: int = 5) -> List[Any]:
        """Returns the top n documents matching the query."""
        scores = self.get_scores(query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        return [documents[i] for i in top_indices]


__all__ = ["BM25Okapi"]

