"""k2py - Python bindings for k2 OnlineDenseIntersecter

This package provides Python bindings for the k2 forced alignment library,
specifically the OnlineDenseIntersecter for efficient streaming decoding.
"""

__version__ = "0.1.0"

from dataclasses import dataclass, field
from typing import Union, List, Dict, Any, Tuple

from ._k2 import (
    CreateFsaVecFromStr,
    FsaVec,
    Array2,
    OnlineDenseIntersecter as _OnlineDenseIntersecter,
)

@dataclass
class AlignedToken:
    token_id: Union[str, int]
    timestamp: int
    duration: int  # in frames
    score: float
    attr: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "token_id": self.token_id,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "score": self.score,
            "attr": self.attr,
        }

class OnlineDenseIntersecter(_OnlineDenseIntersecter):
    """Wrapper around C++ OnlineDenseIntersecter to produce Python-friendly results."""
    
    def finish(self) -> Tuple[List[List["AlignedToken"]], List[List[int]]]:
        """Finish decoding and return results including AlignedToken objects.
        
        Returns:
            A tuple containing:
            - results: List of List of AlignedToken objects (wrapped in list for batch consistency)
            - labels: List of List of timestamps (wrapped in list for batch consistency)
        """
        final_result = super().finish()
        
        # Convert to AlignedToken objects
        aligned_tokens = []
        token_ids = final_result["token_ids"]
        timestamps = final_result["timestamps"]
        durations = final_result["durations"]
        scores = final_result["scores"]

        for tid, ts, dur, score in zip(token_ids, timestamps, durations, scores):
            aligned_tokens.append(AlignedToken(tid, ts, dur, score))
            
        # Wrap in lists to match the expected format (list of lists for batch)
        # currently we only support single stream in this wrapper for simplicty of k2py
        # but the interface expects batch results
        return [aligned_tokens], [final_result["labels"]]

def AlignSegments(
    graph_result: Dict[str, Any],
    scores: Any, # numpy array
    search_beam: float,
    output_beam: float,
    min_active_states: int,
    max_active_states: int,
    use_double_scores: bool = True,
    allow_partial: bool = True,
) -> Tuple[List[List["AlignedToken"]], List[List[int]]]:
    """Align segments using offline dense intersection.

    Args:
        graph_result: Dictionary returned by CreateFsaVecFromStr
        scores: Numpy array of scores (rows, cols)
        search_beam: Beam size for search
        output_beam: Beam size for output
        min_active_states: Minimum active states
        max_active_states: Maximum active states
        use_double_scores: Whether to use double precision for scores
        allow_partial: If True, treat all states on last frame as final
                      when no final state is active. Default True.

    Returns:
        A tuple containing:
        - results: List of List of AlignedToken objects (wrapped in list for batch consistency)
        - labels: List of List of timestamps (wrapped in list for batch consistency)
    """
    from ._k2 import AlignSegments as _AlignSegments

    final_result = _AlignSegments(
        graph_result,
        scores,
        search_beam,
        output_beam,
        min_active_states,
        max_active_states,
        use_double_scores,
        allow_partial,
    )

    # Convert to AlignedToken objects
    aligned_tokens = []
    token_ids = final_result["token_ids"]
    timestamps = final_result["timestamps"]
    durations = final_result["durations"]
    scores = final_result["scores"]

    for tid, ts, dur, score in zip(token_ids, timestamps, durations, scores):
        aligned_tokens.append(AlignedToken(tid, ts, dur, score))
        
    # Wrap in lists to match the expected format (list of lists for batch)
    return [aligned_tokens], [final_result["labels"]]


__all__ = [
    "CreateFsaVecFromStr",
    "FsaVec",
    "Array2",
    "OnlineDenseIntersecter",
    "AlignedToken",
    "AlignSegments",
]
