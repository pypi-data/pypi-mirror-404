# oncosplice/engines.py
from __future__ import annotations

from typing import Dict, List, Tuple, Optional, Union
import numpy as np

# Lazy-loaded model containers (loaded automatically on first use)
_pang_models = None
_pang_device = None


def _get_torch_device():
    """Get the best available device for PyTorch."""
    import sys
    import torch

    if sys.platform == 'darwin' and torch.backends.mps.is_available():
        try:
            torch.tensor([1.0], device="mps")
            return torch.device("mps")
        except RuntimeError:
            return torch.device("cpu")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _load_pangolin_models():
    """Lazy load Pangolin models."""
    global _pang_models, _pang_device

    if _pang_models is not None:
        return _pang_models

    import torch
    from pkg_resources import resource_filename
    from pangolin.model import Pangolin, L, W, AR

    _pang_device = _get_torch_device()
    print(f"Pangolin loading to {_pang_device}...")

    _pang_models = []
    pang_model_nums = [0, 1, 2, 3, 4, 5, 6, 7]

    for i in pang_model_nums:
        for j in range(1, 6):
            try:
                model = Pangolin(L, W, AR).to(_pang_device)
                model_path = resource_filename("pangolin", f"models/final.{j}.{i}.3")
                weights = torch.load(model_path, weights_only=True, map_location=_pang_device)
                model.load_state_dict(weights)
                model.eval()
                _pang_models.append(model)
            except Exception as e:
                print(f"Warning: Failed to load Pangolin model {j}.{i}: {e}")

    print(f"Pangolin loaded ({len(_pang_models)} models).")
    return _pang_models


_OPENSPLICEAI_MODEL_DIR = None

def _get_openspliceai_model_dir() -> str:
    """Return the path to the OpenSpliceAI MANE 10000nt model directory."""
    global _OPENSPLICEAI_MODEL_DIR
    if _OPENSPLICEAI_MODEL_DIR is not None:
        return _OPENSPLICEAI_MODEL_DIR

    import os

    # Models ship inside the package at geney/models/openspliceai-mane/10000nt
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(pkg_dir, 'models', 'openspliceai-mane', '10000nt')
    default = os.path.normpath(default)

    _OPENSPLICEAI_MODEL_DIR = os.environ.get('OPENSPLICEAI_MODEL_DIR', default)
    return _OPENSPLICEAI_MODEL_DIR


def pang_one_hot_encode(seq: str) -> np.ndarray:
    """One-hot encode DNA sequence for Pangolin model."""
    if not isinstance(seq, str):
        raise TypeError(f"Expected string, got {type(seq).__name__}")

    IN_MAP = np.asarray([[0, 0, 0, 0],  # N
                         [1, 0, 0, 0],  # A
                         [0, 1, 0, 0],  # C
                         [0, 0, 1, 0],  # G
                         [0, 0, 0, 1]]) # T

    valid_chars = set('ACGTN')
    if not all(c.upper() in valid_chars for c in seq):
        raise ValueError("Sequence contains invalid characters")

    seq = seq.upper().replace('A', '1').replace('C', '2')
    seq = seq.replace('G', '3').replace('T', '4').replace('N', '0')

    seq_array = np.asarray(list(map(int, list(seq))))
    return IN_MAP[seq_array.astype('int8')]




def pangolin_predict_probs(seq: str, models: list = None) -> Tuple[List[float], List[float]]:
    """Predict splice site probabilities using Pangolin.

    Pangolin outputs shape (1, 12, seq_len) where:
    - 12 channels = 4 tissues × 3 prediction types
    - For each tissue: [site_usage, acceptor_gain, donor_gain] or similar

    We aggregate by taking max across tissues.
    """
    import torch

    if models is None:
        models = _load_pangolin_models()

    if not models:
        raise ValueError("No Pangolin models loaded")

    x = pang_one_hot_encode(seq)
    x = torch.tensor(x.T[None, :, :], dtype=torch.float32, device=_pang_device)

    preds = []
    with torch.no_grad():
        for model in models:
            pred = model(x)
            preds.append(pred.cpu().numpy())

    y = np.mean(preds, axis=0)  # Shape: (1, 12, seq_len)

    # Pangolin has 12 channels organized as:
    # Indices 0,3,6,9: site usage scores for 4 tissues
    # Indices 1,4,7,10: acceptor gain scores for 4 tissues
    # Indices 2,5,8,11: donor gain scores for 4 tissues
    # Take max across the 4 tissues for each type

    # Acceptor: max of channels 1, 4, 7, 10
    acceptor_channels = y[0, [1, 4, 7, 10], :]  # (4, seq_len)
    acceptor_probs = np.max(acceptor_channels, axis=0).tolist()

    # Donor: max of channels 2, 5, 8, 11
    donor_channels = y[0, [2, 5, 8, 11], :]  # (4, seq_len)
    donor_probs = np.max(donor_channels, axis=0).tolist()

    return donor_probs, acceptor_probs


def sai_predict_probs(seq: str) -> Tuple[np.ndarray, np.ndarray]:
    """Predict acceptor and donor probabilities using OpenSpliceAI.

    Uses the OpenSpliceAI predict() function which handles encoding,
    windowing, ensemble averaging, and softmax internally.

    Returns (acceptor_probs, donor_probs) as numpy arrays matching the
    full input sequence length.
    """
    from openspliceai.predict.predict import predict
    import io, sys

    model_dir = _get_openspliceai_model_dir()

    # Suppress OpenSpliceAI's verbose print output
    _stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        y = predict(seq, model_dir, flanking_size=10000)  # (seq_len, 3)
    finally:
        sys.stdout = _stdout

    y = y.numpy()
    return y[:, 1], y[:, 2]  # acceptor, donor


def run_spliceai_seq(
    seq: str,
    indices: Union[List[int], np.ndarray],
    threshold: float = 0.0,
) -> Tuple[Dict[int, float], Dict[int, float]]:
    """Run SpliceAI on seq and return donor/acceptor sites above threshold."""
    if len(indices) != len(seq):
        raise ValueError(f"indices length ({len(indices)}) must match sequence length ({len(seq)})")

    acc_probs, don_probs = sai_predict_probs(seq)
    acceptor = {pos: p for pos, p in zip(indices, acc_probs) if p >= threshold}
    donor = {pos: p for pos, p in zip(indices, don_probs) if p >= threshold}
    return donor, acceptor


def _generate_random_sequence(length: int) -> str:
    """Generate a random DNA sequence of given length."""
    import random
    return ''.join(random.choices('ACGT', k=length))


def run_splicing_engine(
    seq: Optional[str] = None,
    engine: str = "spliceai",
) -> Tuple[List[float], List[float]]:
    """Run specified splicing engine to predict splice site probabilities."""
    if seq is None:
        seq = _generate_random_sequence(15_001)

    if not isinstance(seq, str) or not seq:
        raise ValueError("Sequence must be a non-empty string")

    valid_chars = set("ACGTN")
    if not all(c.upper() in valid_chars for c in seq):
        raise ValueError("Sequence contains invalid nucleotides")

    match engine:
        case "spliceai":
            acc, don = sai_predict_probs(seq)
            return don.tolist(), acc.tolist()
        case "pangolin":
            return pangolin_predict_probs(seq)
        case _:
            raise ValueError(f"Engine '{engine}' not implemented. Available: 'spliceai', 'pangolin'")


# ------------------------------------------------------------------------------
# Higher-level prediction utilities (formerly in splicing_table.py)
# ------------------------------------------------------------------------------

def predict_splicing(s, position: int, engine: str = 'spliceai', context: int = 7500):
    """
    Predict splicing probabilities at a given position using the specified engine.

    Args:
        s: Sequence object with .seq, .index, .clone(), .rev attributes
        position: The genomic position to predict splicing probabilities for.
        engine: The prediction engine to use. Supported: 'spliceai', 'pangolin'.
        context: The length of the target central region (default: 7500).

    Returns:
        pd.DataFrame with position index and columns: donor_prob, acceptor_prob, nucleotides
    """
    import pandas as pd

    if position < s.index.min() or position > s.index.max():
        raise ValueError(f"Position {position} is outside sequence bounds [{s.index.min()}, {s.index.max()}]")

    target = s.clone(position - context, position + context)

    if len(target.seq) == 0:
        raise ValueError(f"No sequence data found around position {position} with context {context}")

    seq, indices = target.seq, target.index

    if len(indices) == 0:
        raise ValueError(f"No indices found in sequence around position {position}")

    rel_pos = np.abs(indices - position).argmin()
    left_missing, right_missing = max(0, context - rel_pos), max(0, context - (len(seq) - rel_pos))

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

    donor_probs, acceptor_probs = run_splicing_engine(seq=seq, engine=engine)

    seq = seq[5000:-5000]
    indices = indices[5000:-5000]
    expected_len = len(seq)

    if len(donor_probs) != expected_len:
        if len(donor_probs) > expected_len:
            offset = (len(donor_probs) - expected_len) // 2
            donor_probs = donor_probs[offset:offset + expected_len]
            acceptor_probs = acceptor_probs[offset:offset + expected_len]
        else:
            pad_len = expected_len - len(donor_probs)
            donor_probs = donor_probs + [0.0] * pad_len
            acceptor_probs = acceptor_probs + [0.0] * pad_len

    df = pd.DataFrame({
        'position': indices,
        'donor_prob': donor_probs,
        'acceptor_prob': acceptor_probs,
        'nucleotides': list(seq)
    }).set_index('position').round(3)

    df.attrs['name'] = s.name
    return df


def adjoin_splicing_outcomes(
    splicing_predictions: Dict[str, 'pd.DataFrame'],
    transcript: Optional[object] = None,
) -> 'pd.DataFrame':
    """
    Combine splicing predictions for multiple mutations into a multi-index DataFrame.

    Args:
        splicing_predictions: {label -> DF with 'donor_prob','acceptor_prob','nucleotides'}
        transcript: optional transcript (must have .acceptors, .donors, .rev)
    """
    import pandas as pd

    if not splicing_predictions:
        raise ValueError("splicing_predictions cannot be empty")

    dfs = []
    for label, df in splicing_predictions.items():
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected DataFrame for '{label}', got {type(df).__name__}")

        required_cols = ["donor_prob", "acceptor_prob", "nucleotides"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"DataFrame for '{label}' missing required columns: {missing}")

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
