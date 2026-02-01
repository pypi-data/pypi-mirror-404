# oncosplice/splicing_table.py
from __future__ import annotations

from typing import Dict, Optional, Union
import numpy as np
import pandas as pd

from .engines import run_splicing_engine



def predict_splicing(s, position: int, engine: str = 'spliceai', context: int = 7500, 
                    ) -> Union['SeqMat', pd.DataFrame]:
    """
    Predict splicing probabilities at a given position using the specified engine.

    Args:
        position (int): The genomic position to predict splicing probabilities for.
        engine (str): The prediction engine to use. Supported: 'spliceai', 'pangolin'.
        context (int): The length of the target central region (default: 7500).
        format (str): Output format for the splicing engine results.

    Returns:
        pd.DataFrame: A DataFrame containing:
            - position: The genomic position
            - donor_prob: Probability of being a donor splice site
            - acceptor_prob: Probability of being an acceptor splice site
            - nucleotides: The nucleotide sequence at that position

    Raises:
        ValueError: If an unsupported engine is provided.
        IndexError: If the position is not found in the sequence.
    """
    # Validate position is within sequence bounds
    if position < s.index.min() or position > s.index.max():
        raise ValueError(f"Position {position} is outside sequence bounds [{s.index.min()}, {s.index.max()}]")
    
    # Retrieve extended context (includes flanks) around the position.
    target = s.clone(position - context, position + context)
    
    # Check if target clone resulted in empty sequence
    if len(target.seq) == 0:
        raise ValueError(f"No sequence data found around position {position} with context {context}")
    
    seq, indices = target.seq, target.index
    
    # Validate indices array is not empty
    if len(indices) == 0:
        raise ValueError(f"No indices found in sequence around position {position}")
    
    # Find relative position within the context window
    rel_pos = np.abs(indices - position).argmin()
    left_missing, right_missing = max(0, context - rel_pos), max(0, context - (len(seq) - rel_pos))
    # print(left_missing, right_missing)
    if left_missing > 0 or right_missing > 0:
        step = -1 if s.rev else 1

        if left_missing > 0:
            left_pad = np.arange(indices[0] - step * left_missing, indices[0], step)
        else:
            left_pad = np.array([], dtype=indices.dtype)

        if right_missing > 0:
            right_pad = np.arange(indices[-1] + step, indices[-1] + step * (right_missing + 1), step)
        else:
            right_pad = np.array([], dtype=indices.dtype)

        seq = 'N' * left_missing + seq + 'N' * right_missing
        indices = np.concatenate([left_pad, indices, right_pad])

    # Run the splicing prediction engine (function assumed to be defined externally)
    donor_probs, acceptor_probs = run_splicing_engine(seq=seq, engine=engine)
    # Trim off the fixed flanks before returning results.
    seq = seq[5000:-5000]
    indices = indices[5000:-5000]
    df = pd.DataFrame({
        'position': indices,
        'donor_prob': donor_probs,
        'acceptor_prob': acceptor_probs,
        'nucleotides': list(seq)
    }).set_index('position').round(3)

    df.attrs['name'] = s.name
    return df
    


def adjoin_splicing_outcomes(
    splicing_predictions: Dict[str, pd.DataFrame],
    transcript: Optional[object] = None,
) -> pd.DataFrame:
    """
    Combine splicing predictions for multiple mutations into a multi-index DataFrame.

    splicing_predictions: {label -> DF with 'donor_prob','acceptor_prob','nucleotides'}
    transcript: optional transcript (must have .acceptors, .donors, .rev)
    """
    if not splicing_predictions:
        raise ValueError("splicing_predictions cannot be empty")

    dfs = []
    for label, df in splicing_predictions.items():
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected DataFrame for '{label}', got {type(df).__name__}")

        required_cols = ["donor_prob", "acceptor_prob", "nucleotides"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(
                f"DataFrame for '{label}' missing required columns: {missing}"
            )

        var_df = df.rename(
            columns={
                "donor_prob": ("donors", f"{label}_prob"),
                "acceptor_prob": ("acceptors", f"{label}_prob"),
                "nucleotides": ("nts", f"{label}"),
            }
        )
        dfs.append(var_df)

    try:
        full_df = pd.concat(dfs, axis=1)
    except Exception as e:
        raise ValueError(f"Failed to concatenate DataFrames: {e}") from e

    if not isinstance(full_df.columns, pd.MultiIndex):
        full_df.columns = pd.MultiIndex.from_tuples(full_df.columns)

    if transcript is not None:
        full_df[("acceptors", "annotated")] = full_df.apply(
            lambda row: row.name in transcript.acceptors, axis=1
        )
        full_df[("donors", "annotated")] = full_df.apply(
            lambda row: row.name in transcript.donors, axis=1
        )
        full_df.sort_index(axis=1, level=0, inplace=True)
        full_df.sort_index(ascending=not transcript.rev, inplace=True)
    else:
        full_df.sort_index(axis=1, level=0, inplace=True)

    return full_df