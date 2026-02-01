# oncosplice/__init__.py
from .variants import Mutation, MutationalEvent, MutationLibrary
from .engines import (
    sai_predict_probs,
    run_spliceai_seq,
    run_splicing_engine,
    predict_splicing,
    adjoin_splicing_outcomes,
)
from .transcripts import TranscriptLibrary
from .splice_graph import SpliceSimulator
from .pipelines import (
    oncosplice_pipeline,
    oncosplice_top_isoform,
    max_splicing_delta,
    oncosplice_pipeline_single_transcript,  # backwards compat
)

__all__ = [
    "Mutation",
    "MutationalEvent",
    "MutationLibrary",
    "sai_predict_probs",
    "run_spliceai_seq",
    "run_splicing_engine",
    "predict_splicing",
    "adjoin_splicing_outcomes",
    "TranscriptLibrary",
    "SpliceSimulator",
    "oncosplice_pipeline",
    "oncosplice_top_isoform",
    "max_splicing_delta",
    "oncosplice_pipeline_single_transcript",
]


mut_id = 'KRAS:12:25227343:G:T'
epistasis_id = 'KRAS:12:25227343:G:T|KRAS:12:25227344:A:T'