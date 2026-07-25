import os
import re
import math
import json
from typing import List, Dict, Any, Optional
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


def tokenize(text: str) -> List[str]:
    """
    Splits text on non-alphanumeric characters, splits camelCase terms,
    lowercases all tokens, and filters empty strings.
    """
    if not text:
        return []
    # Split camelCase (e.g., UserService -> User Service)
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', text)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1)
    
    # Replace punctuation and special characters with spaces
    s3 = re.sub(r'[^a-zA-Z0-9]', ' ', s2)
    
    # Lowercase and split
    tokens = s3.lower().split()
    return tokens


class BM25Index:
    """
    Lexical BM25 Search Index for exact keyword and identifier matching.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = {}  # chunk_id -> document properties
        self.doc_frequencies = {}
        self.doc_lengths = {}
        self.avg_doc_len = 0.0
        self.total_docs = 0

    def fit(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Builds index mapping and counts IDF statistics from document chunks.
        """
        self.corpus = {}
        self.doc_frequencies = {}
        self.doc_lengths = {}
        
        total_len = 0
        for chunk in chunks:
            cid = chunk.get("chunk_id")
            content = chunk.get("content") or ""
            if not cid:
                continue
            
            tokens = tokenize(content)
            doc_len = len(tokens)
            total_len += doc_len
            self.doc_lengths[cid] = doc_len
            
            # Term frequencies in this document
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
                
            self.corpus[cid] = {
                "chunk_id": cid,
                "content": content,
                "file_path": chunk.get("file_path"),
                "class_name": chunk.get("class_name"),
                "method_name": chunk.get("method_name"),
                "start_line": chunk.get("start_line"),
                "end_line": chunk.get("end_line"),
                "chunk_type": chunk.get("chunk_type"),
                "tf": tf
            }
            
            # Document frequencies update
            for t in tf.keys():
                self.doc_frequencies[t] = self.doc_frequencies.get(t, 0) + 1
                
        self.total_docs = len(self.corpus)
        self.avg_doc_len = total_len / self.total_docs if self.total_docs > 0 else 0.0

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Calculates BM25 lexical relevance score and returns top-k documents.
        """
        logger.info("BM25 search started")
        query_tokens = tokenize(query)
        if not query_tokens or self.total_docs == 0:
            logger.warning("Empty lexical results")
            return []

        scores = {}
        for q in query_tokens:
            df = self.doc_frequencies.get(q, 0)
            if df == 0:
                continue
            # IDF calculation
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
            
            for cid, doc in self.corpus.items():
                tf = doc["tf"].get(q, 0)
                if tf == 0:
                    continue
                
                doc_len = self.doc_lengths[cid]
                # BM25 core term
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[cid] = scores.get(cid, 0.0) + idf * (numerator / denominator)

        if not scores:
            logger.warning("Empty lexical results")
            return []

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        results = []
        for cid, score in sorted_scores:
            doc = self.corpus[cid]
            results.append({
                "chunk_id": cid,
                "score": score,
                "content": doc["content"],
                "file_path": doc["file_path"],
                "class_name": doc["class_name"],
                "method_name": doc["method_name"],
                "start_line": doc["start_line"],
                "end_line": doc["end_line"],
                "chunk_type": doc["chunk_type"]
            })
        return results

    def save(self, filepath: str) -> None:
        """
        Persists current BM25 index state to a JSON file.
        """
        data = {
            "k1": self.k1,
            "b": self.b,
            "avg_doc_len": self.avg_doc_len,
            "total_docs": self.total_docs,
            "doc_lengths": self.doc_lengths,
            "doc_frequencies": self.doc_frequencies,
            "corpus": self.corpus
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str) -> None:
        """
        Loads BM25 index from a JSON file path.
        """
        if not os.path.exists(filepath):
            logger.error("BM25 index unavailable")
            raise FileNotFoundError(f"BM25 index file '{filepath}' not found.")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.k1 = data["k1"]
        self.b = data["b"]
        self.avg_doc_len = data["avg_doc_len"]
        self.total_docs = data["total_docs"]
        self.doc_lengths = data["doc_lengths"]
        self.doc_frequencies = data["doc_frequencies"]
        self.corpus = data["corpus"]
