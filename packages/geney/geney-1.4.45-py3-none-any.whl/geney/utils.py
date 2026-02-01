__all__ = ['is_monotonic', 'contains', 'unload_json', 'unload_pickle', 'dump_json', 'dump_pickle', 'generate_random_nucleotide_sequences', 'generate_random_sequence', 'short_hash_of_list']

import pickle
import json
from pathlib import Path
from bisect import bisect_left
import hashlib
import random
from typing import Any, List, Sequence, Union

# def is_monotonic(A):
#     x, y = [], []
#     x.extend(A)
#     y.extend(A)
#     x.sort()
#     y.sort(reverse=True)
#     if (x == A or y == A):
#         return True
#     return False


# def available_genes(organism='hg38'):
#     from geney import config
#     annotation_path = config[organism]['MRNA_PATH'] / 'protein_coding'
#     return sorted(list(set([m.stem.split('_')[-1] for m in annotation_path.glob('*')])))


def contains(a: Sequence[Any], x: Any) -> bool:
    """Check if sorted sequence contains value using binary search.
    
    Args:
        a: Sorted sequence to search in
        x: Value to search for
        
    Returns:
        True if value is found, False otherwise
        
    Raises:
        TypeError: If sequence is not sortable
    """
    if not hasattr(a, '__len__') or not hasattr(a, '__getitem__'):
        raise TypeError("First argument must be a sequence")
        
    try:
        i = bisect_left(a, x)
        return i != len(a) and a[i] == x
    except TypeError as e:
        raise TypeError(f"Cannot compare types in sequence: {e}") from e


def unload_json(file_path: Union[str, Path]) -> Any:
    """Load data from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded data structure
        
    Raises:
        FileNotFoundError: If file doesn't exist
        JSONDecodeError: If file contains invalid JSON
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file {file_path}: {e.msg}", e.doc, e.pos) from e


def dump_json(file_path: Union[str, Path], payload: Any, indent: int = 2) -> None:
    """Save data to JSON file.
    
    Args:
        file_path: Path to output JSON file
        payload: Data to save
        indent: JSON indentation level
        
    Raises:
        TypeError: If payload is not JSON serializable
        PermissionError: If cannot write to file
    """
    file_path = Path(file_path)
    
    # Create parent directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=indent, ensure_ascii=False)
    except TypeError as e:
        raise TypeError(f"Cannot serialize data to JSON: {e}") from e


def unload_pickle(file_path: Union[str, Path]) -> Any:
    """Load data from pickle file.
    
    Args:
        file_path: Path to pickle file
        
    Returns:
        Loaded data structure
        
    Raises:
        FileNotFoundError: If file doesn't exist
        pickle.UnpicklingError: If file contains invalid pickle data
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Pickle file not found: {file_path}")
        
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        return data
    except pickle.UnpicklingError as e:
        raise pickle.UnpicklingError(f"Invalid pickle data in file {file_path}: {e}") from e


def dump_pickle(file_path: Union[str, Path], payload: Any) -> None:
    """Save data to pickle file.
    
    Args:
        file_path: Path to output pickle file
        payload: Data to save
        
    Raises:
        PermissionError: If cannot write to file
    """
    file_path = Path(file_path)
    
    # Create parent directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(payload, f)
    except Exception as e:
        raise RuntimeError(f"Failed to save pickle file {file_path}: {e}") from e



def is_monotonic(A: Sequence[Any]) -> bool:
    """Check if sequence is monotonic (non-decreasing or non-increasing).
    
    Args:
        A: Sequence to check
        
    Returns:
        True if sequence is monotonic, False otherwise
        
    Raises:
        TypeError: If sequence elements are not comparable
    """
    if not hasattr(A, '__len__') or len(A) < 2:
        return True
        
    try:
        return (all(x <= y for x, y in zip(A, A[1:])) or 
                all(x >= y for x, y in zip(A, A[1:])))
    except TypeError as e:
        raise TypeError(f"Cannot compare sequence elements: {e}") from e


def generate_random_sequence(length: int) -> str:
    """Generate a random DNA sequence of given length.
    
    Args:
        length: Length of sequence to generate
        
    Returns:
        Random DNA sequence containing only A, C, G, T
        
    Raises:
        ValueError: If length is not positive
    """
    if not isinstance(length, int):
        raise TypeError(f"Length must be integer, got {type(length).__name__}")
        
    if length <= 0:
        raise ValueError(f"Length must be positive, got {length}")
        
    return ''.join(random.choices('ACGT', k=length))

def generate_random_nucleotide_sequences(num_sequences: int, min_len: int = 3, max_len: int = 10) -> List[str]:
    """
    Generate random DNA sequences of variable lengths.

    Args:
        num_sequences: Number of sequences to generate
        min_len: Minimum sequence length
        max_len: Maximum sequence length

    Returns:
        List of random nucleotide sequences
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not isinstance(num_sequences, int) or num_sequences <= 0:
        raise ValueError(f"num_sequences must be positive integer, got {num_sequences}")
        
    if not isinstance(min_len, int) or min_len <= 0:
        raise ValueError(f"min_len must be positive integer, got {min_len}")
        
    if not isinstance(max_len, int) or max_len <= 0:
        raise ValueError(f"max_len must be positive integer, got {max_len}")
        
    if min_len > max_len:
        raise ValueError(f"min_len ({min_len}) cannot be greater than max_len ({max_len})")
    
    nucleotides = ['A', 'C', 'G', 'T']
    lengths = list(range(min_len, max_len + 1))
    
    sequences = [
        ''.join(random.choices(nucleotides, k=random.choice(lengths)))
        for _ in range(num_sequences)
    ]
    return sequences



def short_hash_of_list(numbers: List[Any], length: int = 5) -> str:
    """Generate a short hash string from a list of numbers.
    
    Args:
        numbers: List of values to hash
        length: Length of output hash string
        
    Returns:
        Short hash string
        
    Raises:
        ValueError: If length is not positive
    """
    if not isinstance(length, int) or length <= 0:
        raise ValueError(f"Length must be positive integer, got {length}")
        
    if length > 64:  # SHA256 hex digest is 64 characters
        raise ValueError(f"Length cannot exceed 64, got {length}")
    
    try:
        encoded = repr(numbers).encode('utf-8')
        full_hash = hashlib.sha256(encoded).hexdigest()
        return full_hash[:length]
    except Exception as e:
        raise RuntimeError(f"Failed to generate hash: {e}") from e
