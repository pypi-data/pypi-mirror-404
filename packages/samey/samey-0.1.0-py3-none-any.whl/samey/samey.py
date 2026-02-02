"""
Samey - Diversity scoring for text datasets.

Main class that handles the whole scoring flow. Similar to GReaT pattern.
"""

import json
from typing import Union, List, Optional, Dict, Any, Literal
from dataclasses import dataclass, field
from pathlib import Path

from samey.samey_metrics import (
    compression_ratio,
    duplicate_stats,
    template_stats,
    ngram_repetition,
    topic_coverage,
    style_diversity,
    semantic_diversity,
    distinct_n,
)
from samey.samey_utils import (
    apply_length_control,
    get_column,
    Report,
)


@dataclass
class Samey:
    """
    Samey - Dataset diversity scoring.
    
    Measures diversity, repetition, templating, and topic coverage
    of text datasets without LLMs or embeddings.
    
    Attributes:
        length_mode: How to handle text length ("truncate", "window", "none")
        max_chars: Maximum characters per text (default 512)
        shingle_size: Character shingle size for MinHash (default 5)
        lsh_threshold: Jaccard threshold for duplicates (default 0.85)
        max_sample: Max docs for expensive operations (default 50000)
        ngram_min: Minimum n-gram size for boilerplate detection (default 6)
        ngram_max: Maximum n-gram size for boilerplate detection (default 10)
        style_n_clusters: Number of style clusters (default 20)
        seed: Random seed (default 42)
    
    Example:
        >>> from samey import Samey
        >>> model = Samey()
        >>> report = model.score(df, text="prompt", topic="category")
        >>> print(report.summary)
    """
    
    # Length control
    length_mode: Literal["truncate", "window", "none"] = "truncate"
    max_chars: int = 512
    n_windows: int = 3
    
    # Duplicate detection
    shingle_size: int = 5
    minhash_perms: int = 128
    lsh_threshold: float = 0.85
    max_sample: int = 50_000
    
    # Template analysis
    top_k_skeletons: int = 10
    
    # N-gram repetition
    ngram_min: int = 6
    ngram_max: int = 10
    min_ngram_occurrences: int = 2
    top_k_ngrams: int = 20
    
    # Style diversity
    style_n_clusters: int = 20
    style_char_ngram_range: tuple = (3, 5)
    
    # Semantic diversity
    semantic_method: str = "tfidf"  # "tfidf" (fast) or "embedding" (better, needs sentence-transformers)
    semantic_model: str = "paraphrase-MiniLM-L3-v2"  # Only used if method="embedding"
    semantic_max_sample: int = 1000
    enable_semantic: bool = True
    
    # General
    seed: int = 42
    
    def score(
        self,
        data,
        text: Union[str, List[str]] = "text",
        topic: Optional[str] = None,
    ) -> Report:
        """
        Score dataset diversity.
        
        Args:
            data: pandas DataFrame, dict of lists, or list of dicts
            text: Column name(s) containing text to analyze
            topic: Optional column for topic coverage analysis
            
        Returns:
            Report with all diversity metrics
            
        Example:
            >>> report = model.score(df, text="prompt")
            >>> print(report.summary)
            >>> report.to_json("report.json")
        """
        # Normalize text columns
        text_columns = [text] if isinstance(text, str) else list(text)
        
        # Get topic data
        topics = None
        if topic is not None:
            topics = get_column(data, topic)
        
        # Score each column
        all_metrics = {}
        all_debug = {}
        all_length_stats = {}
        
        for col in text_columns:
            texts = get_column(data, col)
            metrics, debug, length_stats = self._score_column(texts, topics, col)
            all_metrics[col] = metrics
            all_debug[col] = debug
            all_length_stats[col] = length_stats
        
        # Aggregate overall
        overall = self._aggregate(all_metrics)
        
        return Report(
            columns=all_metrics,
            overall=overall,
            length_stats=all_length_stats,
            debug=all_debug,
            config=self._config_dict(),
        )
    
    def score_dpo(
        self,
        data,
        prompt: str = "prompt",
        chosen: str = "chosen",
        rejected: str = "rejected",
        topic: Optional[str] = None,
    ) -> Report:
        """
        Score DPO/preference dataset diversity.
        
        Convenience wrapper for datasets with prompt/chosen/rejected columns.
        
        Args:
            data: Input data
            prompt: Prompt column name
            chosen: Chosen response column name
            rejected: Rejected response column name
            topic: Optional topic column
            
        Returns:
            Report with per-column and overall metrics
        """
        return self.score(data, text=[prompt, chosen, rejected], topic=topic)
    
    def _score_column(
        self,
        texts: List[str],
        topics: Optional[List[Any]],
        column_name: str,
    ) -> tuple:
        """Score a single text column."""
        
        # Apply length control
        processed, length_stats = apply_length_control(
            texts,
            mode=self.length_mode,
            max_chars=self.max_chars,
            n_windows=self.n_windows,
            seed=self.seed,
        )
        
        metrics = {}
        debug = {}
        
        # M1: Compression
        comp = compression_ratio(processed, seed=self.seed)
        metrics['compression_ratio'] = comp['compression_ratio']
        metrics['raw_bytes'] = comp['raw_bytes']
        metrics['compressed_bytes'] = comp['compressed_bytes']
        
        # M2: Duplicates
        dups = duplicate_stats(
            processed,
            shingle_size=self.shingle_size,
            num_perms=self.minhash_perms,
            threshold=self.lsh_threshold,
            max_sample=self.max_sample,
            seed=self.seed,
        )
        metrics['near_duplicate_rate'] = dups['near_duplicate_rate']
        metrics['n_duplicate_clusters'] = dups['n_duplicate_clusters']
        metrics['largest_cluster_size'] = dups['largest_cluster_size']
        metrics['largest_cluster_fraction'] = dups['largest_cluster_fraction']
        
        # M3: Templates
        tmpl = template_stats(processed, top_k=self.top_k_skeletons)
        metrics['n_unique_skeletons'] = tmpl['n_unique_skeletons']
        metrics['skeleton_diversity'] = tmpl['skeleton_diversity']
        metrics['top_skeleton_share'] = tmpl['top_skeleton_share']
        metrics['skeleton_gini'] = tmpl['skeleton_gini']
        debug['top_skeletons'] = tmpl.get('top_skeletons', [])
        
        # M4: N-gram repetition
        ngrams = ngram_repetition(
            processed,
            ngram_min=self.ngram_min,
            ngram_max=self.ngram_max,
            min_occurrences=self.min_ngram_occurrences,
            top_k=self.top_k_ngrams,
        )
        metrics['repeated_ngram_rate'] = ngrams['repeated_ngram_rate']
        metrics['n_unique_repeated_ngrams'] = ngrams['n_unique_repeated_ngrams']
        metrics['avg_ngram_occurrences'] = ngrams['avg_ngram_occurrences']
        debug['top_repeated_ngrams'] = ngrams.get('top_repeated_ngrams', [])
        
        # M5: Topic coverage
        if topics is not None:
            topic_stats = topic_coverage(topics, top_k=self.top_k_skeletons)
            metrics['n_unique_topics'] = topic_stats['n_unique_topics']
            metrics['topic_entropy'] = topic_stats['topic_entropy']
            metrics['topic_gini'] = topic_stats['topic_gini']
            metrics['top_topic_share'] = topic_stats['top_topic_share']
            metrics['has_topics'] = topic_stats['has_topics']
            debug['top_topics'] = topic_stats.get('top_topics', [])
        
        # M6: Style diversity
        style = style_diversity(
            processed,
            n_clusters=self.style_n_clusters,
            char_ngram_range=self.style_char_ngram_range,
            max_sample=self.max_sample,
            seed=self.seed,
        )
        metrics['largest_style_cluster_fraction'] = style['largest_cluster_fraction']
        metrics['style_cluster_gini'] = style['style_cluster_gini']
        metrics['n_style_clusters_used'] = style['n_clusters_used']
        metrics['sklearn_available'] = style['sklearn_available']
        
        # M7: Semantic diversity (TF-IDF or embedding-based)
        if self.enable_semantic:
            sem = semantic_diversity(
                processed,
                method=self.semantic_method,
                model_name=self.semantic_model,
                max_sample=self.semantic_max_sample,
                seed=self.seed,
            )
            # Get the score key based on method
            if self.semantic_method == "embedding":
                metrics['semantic_diversity_score'] = sem.get('embedding_diversity_score', 0.0)
            else:
                metrics['semantic_diversity_score'] = sem.get('tfidf_diversity_score', 0.0)
            metrics['avg_pairwise_distance'] = sem['avg_pairwise_distance']
            metrics['centroid_distance'] = sem['centroid_distance']
            metrics['semantic_method'] = sem.get('method', self.semantic_method)
            if 'error' in sem:
                debug['semantic_error'] = sem['error']
        
        # M8: Distinct-N
        dist = distinct_n(processed)
        metrics['distinct_1'] = dist['distinct_1']
        metrics['distinct_2'] = dist['distinct_2']
        metrics['distinct_3'] = dist['distinct_3']
        metrics['vocab_size'] = dist['vocab_size']
        metrics['avg_distinct'] = dist['avg_distinct']
        
        # Metadata
        metrics['n_texts'] = len(texts)
        metrics['n_texts_processed'] = len(processed)
        
        return metrics, debug, length_stats
    
    def _aggregate(self, column_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate metrics across columns."""
        if not column_metrics:
            return {}
        
        mean_keys = [
            'compression_ratio', 'near_duplicate_rate', 'largest_cluster_fraction',
            'skeleton_diversity', 'top_skeleton_share', 'skeleton_gini',
            'repeated_ngram_rate', 'topic_entropy', 'topic_gini',
            'largest_style_cluster_fraction', 'style_cluster_gini',
            'semantic_diversity_score', 'avg_pairwise_distance', 'centroid_distance',
            'distinct_1', 'distinct_2', 'distinct_3', 'avg_distinct',
        ]
        
        sum_keys = ['n_texts', 'n_texts_processed', 'raw_bytes', 'compressed_bytes']
        
        overall = {}
        
        for key in mean_keys:
            values = [m[key] for m in column_metrics.values() if key in m]
            if values:
                overall[key] = round(sum(values) / len(values), 4)
        
        for key in sum_keys:
            values = [m[key] for m in column_metrics.values() if key in m]
            if values:
                overall[key] = sum(values)
        
        return overall
    
    def _config_dict(self) -> Dict[str, Any]:
        """Get config as dict."""
        return {
            "length_mode": self.length_mode,
            "max_chars": self.max_chars,
            "n_windows": self.n_windows,
            "shingle_size": self.shingle_size,
            "minhash_perms": self.minhash_perms,
            "lsh_threshold": self.lsh_threshold,
            "max_sample": self.max_sample,
            "ngram_min": self.ngram_min,
            "ngram_max": self.ngram_max,
            "style_n_clusters": self.style_n_clusters,
            "semantic_method": self.semantic_method,
            "semantic_model": self.semantic_model,
            "semantic_max_sample": self.semantic_max_sample,
            "enable_semantic": self.enable_semantic,
            "seed": self.seed,
        }
    
    def save(self, path: str):
        """
        Save Samey configuration.
        
        Args:
            path: Directory path to save config
        """
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        
        config = self._config_dict()
        with open(p / "config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "Samey":
        """
        Load Samey from saved config.
        
        Args:
            path: Directory path containing config.json
            
        Returns:
            Samey instance with loaded config
        """
        p = Path(path)
        with open(p / "config.json") as f:
            config = json.load(f)
        
        return cls(**config)


# Convenience functions for quick one-liner usage
def score(
    data,
    text: Union[str, List[str]] = "text",
    topic: Optional[str] = None,
    **kwargs,
) -> Report:
    """
    Quick scoring function.
    
    Example:
        >>> import samey as sl
        >>> report = sl.score(df, text="prompt")
    """
    model = Samey(**kwargs)
    return model.score(data, text=text, topic=topic)


def score_dpo(
    data,
    prompt: str = "prompt",
    chosen: str = "chosen",
    rejected: str = "rejected",
    topic: Optional[str] = None,
    **kwargs,
) -> Report:
    """
    Quick DPO scoring function.
    
    Example:
        >>> import samey as sl
        >>> report = sl.score_dpo(df)
    """
    model = Samey(**kwargs)
    return model.score_dpo(data, prompt=prompt, chosen=chosen, rejected=rejected, topic=topic)
