"""
Diversity metrics for text datasets.

All metrics in one place - compression, duplicates, templates, n-grams, topics, style, distinct-n.
"""

import gzip
import math
import random
import hashlib
import warnings
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import Counter, defaultdict


# =============================================================================
# M1: Compression Ratio
# =============================================================================

def compression_ratio(texts: List[str], sample_size: int = None, seed: int = 42) -> dict:
    """
    Compression ratio as a proxy for dataset repetitiveness.
    
    compressed_bytes / raw_bytes:
    - Close to 0 = highly repetitive
    - Close to 1 = unique/random
    - Typical natural text: 0.3-0.5
    """
    if not texts:
        return {"compression_ratio": 1.0, "raw_bytes": 0, "compressed_bytes": 0}
    
    if sample_size and len(texts) > sample_size:
        random.seed(seed)
        texts = random.sample(texts, sample_size)
    
    combined = "\n---SEP---\n".join(t for t in texts if isinstance(t, str))
    raw_bytes = combined.encode('utf-8')
    
    if len(raw_bytes) == 0:
        return {"compression_ratio": 1.0, "raw_bytes": 0, "compressed_bytes": 0}
    
    compressed = gzip.compress(raw_bytes, compresslevel=6)
    ratio = len(compressed) / len(raw_bytes)
    
    return {
        "compression_ratio": round(ratio, 4),
        "raw_bytes": len(raw_bytes),
        "compressed_bytes": len(compressed),
    }


# =============================================================================
# M2: Near-Duplicate Detection (MinHash/LSH)
# =============================================================================

def _hash(data: bytes, seed: int) -> int:
    h = hashlib.md5(data + seed.to_bytes(4, 'big'))
    return int.from_bytes(h.digest()[:8], 'big')


def _shingles(text: str, n: int = 5) -> Set[str]:
    if not isinstance(text, str) or len(text) < n:
        return set()
    return {text[i:i+n] for i in range(len(text) - n + 1)}


def _minhash(shingles: Set[str], num_perms: int, seed: int = 42) -> List[int]:
    if not shingles:
        return [0] * num_perms
    
    sig = []
    for i in range(num_perms):
        min_h = float('inf')
        for s in shingles:
            h = _hash(s.encode('utf-8'), seed + i)
            if h < min_h:
                min_h = h
        sig.append(min_h)
    return sig


def _lsh_buckets(sig: List[int], bands: int) -> List[Tuple[int, int]]:
    rows = len(sig) // bands
    buckets = []
    for b in range(bands):
        start = b * rows
        buckets.append((b, hash(tuple(sig[start:start + rows]))))
    return buckets


def duplicate_stats(
    texts: List[str],
    shingle_size: int = 5,
    num_perms: int = 128,
    threshold: float = 0.85,
    max_sample: int = 50_000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Near-duplicate detection using MinHash/LSH.
    
    Returns:
        near_duplicate_rate: fraction of texts that are near-duplicates
        n_duplicate_clusters: number of clusters with >1 member
        largest_cluster_size: size of largest duplicate cluster
    """
    if not texts:
        return {
            "near_duplicate_rate": 0.0,
            "n_duplicate_clusters": 0,
            "largest_cluster_size": 1,
            "largest_cluster_fraction": 0.0,
        }
    
    if len(texts) > max_sample:
        random.seed(seed)
        indices = random.sample(range(len(texts)), max_sample)
        texts = [texts[i] for i in indices]
    
    n = len(texts)
    
    # Compute signatures
    sigs = []
    for t in texts:
        sh = _shingles(t, shingle_size)
        sigs.append(_minhash(sh, num_perms, seed))
    
    # LSH bucketing
    bands = max(4, num_perms // 4)
    buckets: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for idx, sig in enumerate(sigs):
        for key in _lsh_buckets(sig, bands):
            buckets[key].append(idx)
    
    # Find candidate pairs
    pairs: Set[Tuple[int, int]] = set()
    for bucket_items in buckets.values():
        if len(bucket_items) > 1:
            for i in range(len(bucket_items)):
                for j in range(i + 1, len(bucket_items)):
                    pairs.add((min(bucket_items[i], bucket_items[j]),
                              max(bucket_items[i], bucket_items[j])))
    
    # Union-Find for clustering
    parent = list(range(n))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    # Verify pairs
    for i, j in pairs:
        matches = sum(1 for a, b in zip(sigs[i], sigs[j]) if a == b)
        if matches / num_perms >= threshold:
            union(i, j)
    
    # Count clusters
    cluster_sizes: Dict[int, int] = defaultdict(int)
    for i in range(n):
        cluster_sizes[find(i)] += 1
    
    clusters_gt1 = [s for s in cluster_sizes.values() if s > 1]
    dup_rate = sum(clusters_gt1) / n if n > 0 else 0.0
    largest = max(cluster_sizes.values()) if cluster_sizes else 1
    
    return {
        "near_duplicate_rate": round(dup_rate, 4),
        "n_duplicate_clusters": len(clusters_gt1),
        "largest_cluster_size": largest,
        "largest_cluster_fraction": round(largest / n, 4) if n > 0 else 0.0,
    }


# =============================================================================
# M3: Template/Skeleton Detection
# =============================================================================

import re

_URL = re.compile(r'https?://\S+|www\.\S+')
_EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
_NUM = re.compile(r'\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b')
_CODE = re.compile(r'```[\s\S]*?```|`[^`]+`')
_QUOTE = re.compile(r'"[^"]*"|\'[^\']*\'')
_WS = re.compile(r'\s+')


def _skeletonize(text: str) -> str:
    """Replace volatile spans with tags, then normalize."""
    if not isinstance(text, str):
        return ""
    text = _CODE.sub('<CODE>', text)
    text = _URL.sub('<URL>', text)
    text = _EMAIL.sub('<EMAIL>', text)
    text = _QUOTE.sub('<QUOTE>', text)
    text = _NUM.sub('<NUM>', text)
    text = text.lower()
    text = _WS.sub(' ', text).strip()
    return text


def _gini(values: List[int]) -> float:
    if not values or len(values) == 1:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    cumsum = 0
    for i, v in enumerate(sorted_vals):
        cumsum += (2 * (i + 1) - n - 1) * v
    return cumsum / (n * total)


def template_stats(texts: List[str], top_k: int = 10) -> Dict[str, Any]:
    """
    Template detection via skeletonization.
    
    Returns skeleton diversity and top skeleton share.
    """
    if not texts:
        return {
            "n_unique_skeletons": 0,
            "skeleton_diversity": 1.0,
            "top_skeleton_share": 0.0,
            "skeleton_gini": 0.0,
            "top_skeletons": [],
        }
    
    skeletons = [_skeletonize(t) for t in texts]
    n = len(skeletons)
    counts = Counter(skeletons)
    
    top_count = counts.most_common(1)[0][1] if counts else 0
    
    top_skeletons = []
    for skel, count in counts.most_common(top_k):
        display = skel[:200] + "..." if len(skel) > 200 else skel
        top_skeletons.append({
            "skeleton": display,
            "count": count,
            "share": round(count / n, 4),
        })
    
    return {
        "n_unique_skeletons": len(counts),
        "skeleton_diversity": round(len(counts) / n, 4) if n > 0 else 1.0,
        "top_skeleton_share": round(top_count / n, 4) if n > 0 else 0.0,
        "skeleton_gini": round(_gini(list(counts.values())), 4),
        "top_skeletons": top_skeletons,
    }


# =============================================================================
# M4: N-gram Repetition (Boilerplate Detection)
# =============================================================================

def _tokenize(text: str) -> List[str]:
    if not isinstance(text, str):
        return []
    return re.findall(r"\b\w+(?:'\w+)?\b", text.lower())


def ngram_repetition(
    texts: List[str],
    ngram_min: int = 6,
    ngram_max: int = 10,
    min_occurrences: int = 2,
    top_k: int = 20,
) -> Dict[str, Any]:
    """
    Detect boilerplate via repeated n-grams across rows.
    """
    if not texts:
        return {
            "repeated_ngram_rate": 0.0,
            "n_unique_repeated_ngrams": 0,
            "avg_ngram_occurrences": 0.0,
            "top_repeated_ngrams": [],
        }
    
    n_texts = len(texts)
    ngram_rows: Dict[Tuple[str, ...], Set[int]] = defaultdict(set)
    
    for row_idx, text in enumerate(texts):
        tokens = _tokenize(text)
        if len(tokens) < ngram_min:
            continue
        
        seen: Set[Tuple[str, ...]] = set()
        for n in range(ngram_min, min(ngram_max + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                ng = tuple(tokens[i:i + n])
                if ng not in seen:
                    seen.add(ng)
                    ngram_rows[ng].add(row_idx)
    
    repeated = {ng: rows for ng, rows in ngram_rows.items() if len(rows) >= min_occurrences}
    
    rows_with_repeated: Set[int] = set()
    for rows in repeated.values():
        rows_with_repeated.update(rows)
    
    rate = len(rows_with_repeated) / n_texts if n_texts > 0 else 0.0
    
    top_ngrams = []
    for ng, rows in sorted(repeated.items(), key=lambda x: -len(x[1]))[:top_k]:
        ng_str = " ".join(ng)
        if len(ng_str) > 150:
            ng_str = ng_str[:150] + "..."
        top_ngrams.append({"ngram": ng_str, "count": len(rows)})
    
    return {
        "repeated_ngram_rate": round(rate, 4),
        "n_unique_repeated_ngrams": len(repeated),
        "avg_ngram_occurrences": round(sum(len(r) for r in repeated.values()) / len(repeated), 2) if repeated else 0.0,
        "top_repeated_ngrams": top_ngrams,
    }


# =============================================================================
# M5: Topic Coverage
# =============================================================================

def _entropy(counts: List[int]) -> float:
    if not counts or len(counts) <= 1:
        return 0.0
    total = sum(counts)
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    
    max_entropy = math.log2(len(counts))
    return entropy / max_entropy if max_entropy > 0 else 0.0


def topic_coverage(topics: List[Any], top_k: int = 10) -> Dict[str, Any]:
    """
    Topic distribution analysis.
    
    Returns normalized entropy (0=skewed, 1=uniform) and gini coefficient.
    """
    valid = [t for t in topics if t is not None and t == t]  # t != t catches NaN
    
    if not valid:
        return {
            "n_unique_topics": 0,
            "topic_entropy": 0.0,
            "topic_gini": 0.0,
            "top_topic_share": 0.0,
            "top_topics": [],
            "has_topics": False,
        }
    
    n = len(valid)
    counts = Counter(valid)
    count_list = list(counts.values())
    
    top_count = counts.most_common(1)[0][1] if counts else 0
    
    top_topics = []
    for topic, count in counts.most_common(top_k):
        top_topics.append({
            "topic": str(topic),
            "count": count,
            "share": round(count / n, 4),
        })
    
    return {
        "n_unique_topics": len(counts),
        "topic_entropy": round(_entropy(count_list), 4),
        "topic_gini": round(_gini(count_list), 4),
        "top_topic_share": round(top_count / n, 4) if n > 0 else 0.0,
        "top_topics": top_topics,
        "has_topics": True,
    }


# =============================================================================
# M6: Style Diversity (Character n-gram clustering)
# =============================================================================

def style_diversity(
    texts: List[str],
    n_clusters: int = 20,
    char_ngram_range: tuple = (3, 5),
    max_sample: int = 50_000,
    max_features: int = 5000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Style diversity via character n-gram TF-IDF clustering.
    
    Requires sklearn. Returns largest cluster fraction and gini.
    """
    if not texts:
        return {
            "largest_cluster_fraction": 0.0,
            "style_cluster_gini": 0.0,
            "n_clusters_used": 0,
            "sklearn_available": False,
        }
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import MiniBatchKMeans
    except ImportError:
        return {
            "largest_cluster_fraction": 0.0,
            "style_cluster_gini": 0.0,
            "n_clusters_used": 0,
            "sklearn_available": False,
            "error": "sklearn not installed",
        }
    
    if len(texts) > max_sample:
        random.seed(seed)
        texts = random.sample(texts, max_sample)
    
    valid = [t for t in texts if isinstance(t, str) and len(t.strip()) > 0]
    
    if len(valid) < n_clusters:
        return {
            "largest_cluster_fraction": 1.0 if valid else 0.0,
            "style_cluster_gini": 0.0,
            "n_clusters_used": min(len(valid), 1),
            "sklearn_available": True,
        }
    
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vec = TfidfVectorizer(
                analyzer='char',
                ngram_range=char_ngram_range,
                max_features=max_features,
                lowercase=True,
            )
            X = vec.fit_transform(valid)
        
        actual_k = min(n_clusters, len(valid))
        km = MiniBatchKMeans(
            n_clusters=actual_k,
            random_state=seed,
            batch_size=min(1024, len(valid)),
            n_init=3,
        )
        labels = km.fit_predict(X)
        
        cluster_sizes = sorted(Counter(labels).values(), reverse=True)
        largest = cluster_sizes[0] if cluster_sizes else 0
        
        return {
            "largest_cluster_fraction": round(largest / len(valid), 4) if valid else 0.0,
            "style_cluster_gini": round(_gini(cluster_sizes), 4),
            "n_clusters_used": len(cluster_sizes),
            "sklearn_available": True,
        }
    except Exception as e:
        return {
            "largest_cluster_fraction": 0.0,
            "style_cluster_gini": 0.0,
            "n_clusters_used": 0,
            "sklearn_available": True,
            "error": str(e),
        }


# =============================================================================
# M7: Semantic Diversity (TF-IDF based - fast, no extra deps)
# =============================================================================

def semantic_diversity_tfidf(
    texts: List[str],
    max_sample: int = 2000,
    max_features: int = 5000,
    n_pairs: int = 10000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Semantic diversity via TF-IDF vectors.
    
    Fast, uses only sklearn. Measures how lexically diverse the texts are
    based on word-level TF-IDF representations.
    
    Args:
        texts: List of texts to analyze
        max_sample: Maximum texts to vectorize
        max_features: Max TF-IDF features
        n_pairs: Number of random pairs for distance calculation
        seed: Random seed
        
    Returns:
        avg_pairwise_distance: Average cosine distance (0-1, higher=more diverse)
        centroid_distance: Average distance from centroid
        tfidf_diversity_score: Normalized 0-1 score
    """
    if not texts:
        return {
            "avg_pairwise_distance": 0.0,
            "centroid_distance": 0.0,
            "tfidf_diversity_score": 0.0,
            "method": "tfidf",
            "sklearn_available": False,
        }
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
    except ImportError:
        return {
            "avg_pairwise_distance": 0.0,
            "centroid_distance": 0.0,
            "tfidf_diversity_score": 0.0,
            "method": "tfidf",
            "sklearn_available": False,
            "error": "sklearn not installed",
        }
    
    # Filter valid texts
    valid = [t for t in texts if isinstance(t, str) and len(t.strip()) > 0]
    
    if len(valid) < 2:
        return {
            "avg_pairwise_distance": 0.0,
            "centroid_distance": 0.0,
            "tfidf_diversity_score": 0.0,
            "method": "tfidf",
            "sklearn_available": True,
            "n_texts": len(valid),
        }
    
    # Sample if too large
    random.seed(seed)
    if len(valid) > max_sample:
        valid = random.sample(valid, max_sample)
    
    try:
        # TF-IDF vectorization (word-level)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vec = TfidfVectorizer(
                max_features=max_features,
                lowercase=True,
                stop_words='english',
                ngram_range=(1, 2),  # Unigrams + bigrams
            )
            X = vec.fit_transform(valid)
        
        # Convert to dense for distance calculations (sample if too large)
        n = X.shape[0]
        
        # 1. Average pairwise cosine distance (sample pairs)
        np.random.seed(seed)
        actual_pairs = min(n_pairs, n * (n - 1) // 2)
        idx1 = np.random.randint(0, n, actual_pairs)
        idx2 = np.random.randint(0, n, actual_pairs)
        mask = idx1 != idx2
        idx1, idx2 = idx1[mask], idx2[mask]
        
        if len(idx1) > 0:
            # Cosine similarity for sparse matrices
            # For normalized TF-IDF, cosine_sim = dot product
            sims = np.array([X[i].dot(X[j].T).toarray()[0, 0] for i, j in zip(idx1, idx2)])
            distances = 1 - sims
            avg_distance = float(np.mean(distances))
        else:
            avg_distance = 0.0
        
        # 2. Centroid distance
        centroid = np.asarray(X.mean(axis=0)).flatten()
        centroid_norm = np.linalg.norm(centroid)
        if centroid_norm > 0:
            centroid = centroid / centroid_norm
        
        # Sample for centroid distance calculation
        sample_idx = np.random.choice(n, min(500, n), replace=False)
        centroid_dists = []
        for i in sample_idx:
            row = np.asarray(X[i].todense()).flatten()
            row_norm = np.linalg.norm(row)
            if row_norm > 0:
                row = row / row_norm
            sim = np.dot(row, centroid)
            centroid_dists.append(1 - sim)
        avg_centroid_distance = float(np.mean(centroid_dists))
        
        # 3. Diversity score (normalized)
        diversity_score = min(1.0, (avg_distance + avg_centroid_distance) / 1.5)
        
        return {
            "avg_pairwise_distance": round(avg_distance, 4),
            "centroid_distance": round(avg_centroid_distance, 4),
            "tfidf_diversity_score": round(diversity_score, 4),
            "method": "tfidf",
            "sklearn_available": True,
            "n_texts": len(valid),
            "n_features": X.shape[1],
        }
        
    except Exception as e:
        return {
            "avg_pairwise_distance": 0.0,
            "centroid_distance": 0.0,
            "tfidf_diversity_score": 0.0,
            "method": "tfidf",
            "sklearn_available": True,
            "error": str(e),
        }


def semantic_diversity_embedding(
    texts: List[str],
    model_name: str = "paraphrase-MiniLM-L3-v2",
    max_sample: int = 1000,
    n_pairs: int = 5000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Semantic diversity via sentence embeddings.
    
    Uses a fast sentence transformer model. Better at catching
    paraphrases and synonyms, but slower and requires extra dependency.
    
    Args:
        texts: List of texts to analyze
        model_name: Sentence transformer model
        max_sample: Maximum texts to embed
        n_pairs: Number of random pairs
        seed: Random seed
    """
    if not texts:
        return {
            "avg_pairwise_distance": 0.0,
            "centroid_distance": 0.0,
            "embedding_diversity_score": 0.0,
            "method": "embedding",
            "sentence_transformers_available": False,
        }
    
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        return {
            "avg_pairwise_distance": 0.0,
            "centroid_distance": 0.0,
            "embedding_diversity_score": 0.0,
            "method": "embedding",
            "sentence_transformers_available": False,
            "error": "sentence-transformers not installed",
        }
    
    valid = [t for t in texts if isinstance(t, str) and len(t.strip()) > 0]
    
    if len(valid) < 2:
        return {
            "avg_pairwise_distance": 0.0,
            "centroid_distance": 0.0,
            "embedding_diversity_score": 0.0,
            "method": "embedding",
            "sentence_transformers_available": True,
            "n_texts": len(valid),
        }
    
    random.seed(seed)
    if len(valid) > max_sample:
        valid = random.sample(valid, max_sample)
    
    try:
        import numpy as np
        model = SentenceTransformer(model_name)
        embeddings = model.encode(valid, show_progress_bar=False, convert_to_numpy=True)
        
        # Normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = embeddings / norms
        
        # Pairwise distance
        n = len(embeddings)
        np.random.seed(seed)
        idx1 = np.random.randint(0, n, n_pairs)
        idx2 = np.random.randint(0, n, n_pairs)
        mask = idx1 != idx2
        idx1, idx2 = idx1[mask], idx2[mask]
        
        if len(idx1) > 0:
            cosine_sim = np.sum(embeddings[idx1] * embeddings[idx2], axis=1)
            avg_distance = float(np.mean(1 - cosine_sim))
        else:
            avg_distance = 0.0
        
        # Centroid distance
        centroid = np.mean(embeddings, axis=0)
        centroid = centroid / np.linalg.norm(centroid)
        centroid_dists = 1 - np.dot(embeddings, centroid)
        avg_centroid_distance = float(np.mean(centroid_dists))
        
        diversity_score = min(1.0, (avg_distance + avg_centroid_distance) / 1.2)
        
        return {
            "avg_pairwise_distance": round(avg_distance, 4),
            "centroid_distance": round(avg_centroid_distance, 4),
            "embedding_diversity_score": round(diversity_score, 4),
            "method": "embedding",
            "sentence_transformers_available": True,
            "n_texts": len(valid),
            "model_name": model_name,
        }
        
    except Exception as e:
        return {
            "avg_pairwise_distance": 0.0,
            "centroid_distance": 0.0,
            "embedding_diversity_score": 0.0,
            "method": "embedding",
            "sentence_transformers_available": True,
            "error": str(e),
        }


def semantic_diversity(
    texts: List[str],
    method: str = "tfidf",  # "tfidf" (fast) or "embedding" (better)
    model_name: str = "paraphrase-MiniLM-L3-v2",
    max_sample: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Semantic diversity - dispatcher for TF-IDF or embedding method.
    
    Args:
        texts: List of texts
        method: "tfidf" (fast, sklearn only) or "embedding" (better, needs sentence-transformers)
        model_name: Model for embedding method
        max_sample: Max texts to analyze
        seed: Random seed
    """
    if method == "embedding":
        return semantic_diversity_embedding(texts, model_name, max_sample, seed=seed)
    else:
        return semantic_diversity_tfidf(texts, max_sample, seed=seed)


# =============================================================================
# M8: Distinct-N (Lexical Diversity)
# =============================================================================

def distinct_n(texts: List[str], max_n: int = 3) -> Dict[str, Any]:
    """
    Distinct-n ratios for lexical diversity.
    
    distinct-n = unique_ngrams / total_ngrams
    """
    if not texts:
        return {
            "distinct_1": 0.0,
            "distinct_2": 0.0,
            "distinct_3": 0.0,
            "vocab_size": 0,
            "total_tokens": 0,
            "avg_distinct": 0.0,
        }
    
    all_tokens = []
    for t in texts:
        all_tokens.extend(_tokenize(t))
    
    total = len(all_tokens)
    if total == 0:
        return {
            "distinct_1": 0.0,
            "distinct_2": 0.0,
            "distinct_3": 0.0,
            "vocab_size": 0,
            "total_tokens": 0,
            "avg_distinct": 0.0,
        }
    
    results = {"total_tokens": total, "vocab_size": len(set(all_tokens))}
    distinct_vals = []
    
    for n in range(1, max_n + 1):
        if len(all_tokens) < n:
            results[f"distinct_{n}"] = 0.0
            continue
        
        ngrams = [tuple(all_tokens[i:i + n]) for i in range(len(all_tokens) - n + 1)]
        if ngrams:
            d = len(set(ngrams)) / len(ngrams)
            results[f"distinct_{n}"] = round(d, 4)
            distinct_vals.append(d)
        else:
            results[f"distinct_{n}"] = 0.0
    
    results["avg_distinct"] = round(sum(distinct_vals) / len(distinct_vals), 4) if distinct_vals else 0.0
    
    return results
