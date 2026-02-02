"""
Utility functions for Samey.

Preprocessing, length normalization, and helpers.
"""

import re
import json
import random
from typing import List, Tuple, Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np


# =============================================================================
# Text Preprocessing
# =============================================================================

_WS = re.compile(r'\s+')


def normalize(text: str, lowercase: bool = True) -> str:
    """Normalize text: lowercase and collapse whitespace."""
    if not isinstance(text, str):
        return ""
    if lowercase:
        text = text.lower()
    return _WS.sub(' ', text).strip()


def truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, trying to break at word boundaries."""
    if not isinstance(text, str) or len(text) <= max_chars:
        return text if isinstance(text, str) else ""
    
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]
    return truncated


def random_windows(text: str, window_size: int, n_windows: int, seed: int = None) -> List[str]:
    """Extract random windows from text."""
    if not isinstance(text, str) or len(text) <= window_size:
        return [text] if isinstance(text, str) else [""]
    
    if seed is not None:
        random.seed(seed)
    
    max_start = len(text) - window_size
    return [text[random.randint(0, max_start):random.randint(0, max_start) + window_size] 
            for _ in range(n_windows)]


def apply_length_control(
    texts: List[str],
    mode: Literal["truncate", "window", "none"],
    max_chars: int = 512,
    n_windows: int = 3,
    seed: int = 42
) -> Tuple[List[str], dict]:
    """
    Apply length normalization.
    
    Returns (processed_texts, length_stats)
    """
    lengths_before = [len(t) if isinstance(t, str) else 0 for t in texts]
    
    if mode == "none":
        processed = [t if isinstance(t, str) else "" for t in texts]
    elif mode == "truncate":
        processed = [truncate(t, max_chars) for t in texts]
    elif mode == "window":
        processed = []
        for i, t in enumerate(texts):
            windows = random_windows(t, max_chars, n_windows, seed + i)
            processed.extend(windows)
    else:
        raise ValueError(f"Unknown length_mode: {mode}")
    
    lengths_after = [len(t) for t in processed]
    
    stats = {
        "avg_chars_before": float(np.mean(lengths_before)) if lengths_before else 0,
        "avg_chars_after": float(np.mean(lengths_after)) if lengths_after else 0,
        "median_chars_before": float(np.median(lengths_before)) if lengths_before else 0,
        "median_chars_after": float(np.median(lengths_after)) if lengths_after else 0,
    }
    
    return processed, stats


# =============================================================================
# Data Extraction
# =============================================================================

def get_column(df, column: str) -> List[str]:
    """Extract text data from a dataframe column."""
    try:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            return df[column].astype(str).tolist()
    except ImportError:
        pass
    
    if isinstance(df, dict):
        return [str(x) for x in df[column]]
    elif hasattr(df, '__iter__'):
        return [str(row.get(column, '')) for row in df]
    
    raise ValueError(f"Cannot extract column '{column}' from data")


# =============================================================================
# Report Container
# =============================================================================

@dataclass
class Report:
    """
    Diversity report container.
    
    Holds all metrics and provides export methods.
    """
    columns: Dict[str, Dict[str, Any]]
    overall: Dict[str, Any]
    length_stats: Dict[str, Dict[str, float]]
    debug: Dict[str, Any]
    config: Dict[str, Any]
    
    @property
    def summary(self) -> Dict[str, Any]:
        """Key metrics for quick inspection."""
        summary = {}
        
        if self.overall:
            summary.update({
                f"overall_{k}": v 
                for k, v in self.overall.items()
                if isinstance(v, (int, float, str, bool))
            })
        
        for col, metrics in self.columns.items():
            for key in ['compression_ratio', 'near_duplicate_rate', 
                       'top_skeleton_share', 'repeated_ngram_rate',
                       'topic_entropy', 'largest_cluster_fraction',
                       'distinct_1', 'distinct_2', 'distinct_3', 'avg_distinct']:
                if key in metrics:
                    summary[f"{col}_{key}"] = metrics[key]
        
        return summary
    
    @property
    def diversity_score(self) -> Dict[str, Any]:
        """
        Aggregated diversity score (0-100).
        
        Combines multiple metrics into a single score using:
        1. Normalization to 0-1 (1 = best)
        2. Calibrated against healthy thresholds
        3. Weighted geometric mean (one bad metric tanks the score)
        
        Returns dict with:
            - score: Overall 0-100 score
            - breakdown: Per-metric normalized scores
            - issues: List of detected problems
        """
        # Get metrics from first column (or overall)
        if self.columns:
            col = list(self.columns.keys())[0]
            m = self.columns[col]
        else:
            m = self.overall
        
        if not m:
            return {"score": 0, "breakdown": {}, "issues": []}
        
        # Metric definitions: (key, direction, healthy_threshold, weight)
        # direction: "lower" means lower is better, "higher" means higher is better
        metric_specs = [
            # Core repetition metrics (most important)
            ("compression_ratio", "target", 0.4, 1.5),      # Target ~0.4, penalty both ways
            ("near_duplicate_rate", "lower", 0.1, 2.0),     # Very important
            ("top_skeleton_share", "lower", 0.1, 1.5),      # Template detection
            ("repeated_ngram_rate", "lower", 0.2, 1.2),     # Boilerplate
            
            # Lexical diversity
            ("distinct_2", "higher", 0.5, 1.0),             # Vocabulary richness
            ("distinct_3", "higher", 0.6, 0.8),
            
            # Semantic diversity
            ("semantic_diversity_score", "higher", 0.5, 1.0),
            
            # Topic coverage (if available)
            ("topic_entropy", "higher", 0.8, 1.0),
        ]
        
        breakdown = {}
        issues = []
        weighted_scores = []
        total_weight = 0
        
        for key, direction, threshold, weight in metric_specs:
            if key not in m:
                continue
            
            value = m[key]
            if not isinstance(value, (int, float)):
                continue
            
            # Normalize to 0-1 where 1 = best
            if direction == "lower":
                # Lower is better: 0 at threshold, 1 at 0
                # Use sigmoid-like curve for smooth transition
                if value <= 0:
                    norm = 1.0
                elif value >= threshold * 3:
                    norm = 0.0
                else:
                    # Score decreases as value increases past threshold
                    norm = max(0, 1 - (value / threshold))
                    
            elif direction == "higher":
                # Higher is better: 0 at 0, 1 at threshold+
                if value >= threshold:
                    norm = 1.0
                elif value <= 0:
                    norm = 0.0
                else:
                    norm = value / threshold
                    
            elif direction == "target":
                # Target value (compression): best at threshold, worse both ways
                if value < 0.1:
                    norm = value / 0.1 * 0.5  # Very low compression = repetitive
                elif value < threshold:
                    norm = 0.5 + (value - 0.1) / (threshold - 0.1) * 0.5
                elif value <= 0.6:
                    norm = 1.0
                else:
                    norm = max(0, 1 - (value - 0.6) / 0.4)  # Too high = random
            
            norm = max(0, min(1, norm))  # Clamp to 0-1
            breakdown[key] = round(norm, 3)
            
            # Track issues
            if norm < 0.5:
                severity = "severe" if norm < 0.25 else "warning"
                issues.append({
                    "metric": key,
                    "value": round(value, 4),
                    "normalized": round(norm, 3),
                    "severity": severity,
                    "threshold": threshold,
                })
            
            weighted_scores.append((norm, weight))
            total_weight += weight
        
        if not weighted_scores:
            return {"score": 0, "breakdown": {}, "issues": []}
        
        # Geometric mean (penalizes outliers more than arithmetic mean)
        # Add small epsilon to avoid log(0)
        import math
        log_sum = sum(w * math.log(max(s, 0.001)) for s, w in weighted_scores)
        geom_mean = math.exp(log_sum / total_weight)
        
        # Scale to 0-100
        score = round(geom_mean * 100, 1)
        
        # Sort issues by severity
        issues.sort(key=lambda x: (0 if x["severity"] == "severe" else 1, x["normalized"]))
        
        return {
            "score": score,
            "breakdown": breakdown,
            "issues": issues,
            "n_metrics": len(weighted_scores),
        }
    
    def print_score(self):
        """Print a formatted diversity score report."""
        ds = self.diversity_score
        
        print("=" * 50)
        print(f"DIVERSITY SCORE: {ds['score']}/100")
        print("=" * 50)
        
        print("\nMetric Breakdown (1.0 = best):")
        for key, norm in sorted(ds['breakdown'].items(), key=lambda x: x[1]):
            bar = "█" * int(norm * 20) + "░" * (20 - int(norm * 20))
            status = "✓" if norm >= 0.7 else ("⚠" if norm >= 0.4 else "✗")
            print(f"  {key:30s} {bar} {norm:.2f} {status}")
        
        if ds['issues']:
            print("\nIssues Detected:")
            for issue in ds['issues']:
                icon = "🔴" if issue['severity'] == "severe" else "🟡"
                print(f"  {icon} {issue['metric']}: {issue['value']:.4f} (threshold: {issue['threshold']})")
        else:
            print("\n✅ No significant issues detected!")
        
        return ds
    
    @property
    def table(self):
        """Get metrics as pandas DataFrame."""
        import pandas as pd
        
        all_keys = set()
        for metrics in self.columns.values():
            all_keys.update(k for k, v in metrics.items() 
                          if isinstance(v, (int, float, str, bool)))
        
        data = {}
        for col, metrics in self.columns.items():
            data[col] = {k: metrics.get(k) for k in all_keys}
        
        if self.overall:
            data['overall'] = {k: self.overall.get(k) for k in all_keys}
        
        return pd.DataFrame(data)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self, path: str = None, indent: int = 2) -> str:
        data = self.to_dict()
        json_str = json.dumps(data, indent=indent, default=str)
        
        if path:
            Path(path).write_text(json_str)
        
        return json_str
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = ["# Samey Report\n"]
        
        # Summary
        lines.append("## Summary\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        for k, v in sorted(self.summary.items()):
            if isinstance(v, float):
                lines.append(f"| {k} | {v:.4f} |")
            else:
                lines.append(f"| {k} | {v} |")
        lines.append("")
        
        # Per-column
        for col, metrics in self.columns.items():
            lines.append(f"## {col}\n")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            
            for key in ['compression_ratio', 'near_duplicate_rate', 'top_skeleton_share',
                       'skeleton_diversity', 'repeated_ngram_rate', 
                       'distinct_1', 'distinct_2', 'distinct_3']:
                if key in metrics:
                    v = metrics[key]
                    if isinstance(v, float):
                        lines.append(f"| {key} | {v:.4f} |")
                    else:
                        lines.append(f"| {key} | {v} |")
            lines.append("")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"Report(columns={list(self.columns.keys())}, n_metrics={len(self.summary)})"
