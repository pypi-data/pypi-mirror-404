# oncosplice/pipelines.py
from __future__ import annotations

from datetime import datetime
import pandas as pd

from seqmat import Gene

from .splice_graph import SpliceSimulator
from .transcripts import TranscriptLibrary
from .variants import MutationalEvent
from .Oncosplice import Oncosplice


def oncosplice_pipeline(
    mut_id: str,
    transcript_id: str | None = None,
    splicing_engine: str = "spliceai",
    organism: str = "hg38",
) -> pd.DataFrame:
    """
    Run the full oncosplice pipeline for a mutation.

    Returns DataFrame with all viable isoforms and their oncosplice scores.
    """
    m = MutationalEvent(mut_id)
    assert m.compatible(), "Mutations in event are incompatible"

    reference_transcript = (
        Gene.from_file(m.gene, organism=organism)
        .transcript(transcript_id)
        .generate_pre_mrna()
        .generate_mature_mrna()
        .generate_protein()
    )

    tl = TranscriptLibrary(reference_transcript, m)
    central_pos = m.central_position

    tl.predict_splicing(central_pos, engine=splicing_engine, inplace=True)
    splicing_results = tl.get_event_columns("event")

    ss = SpliceSimulator(
        splicing_results, tl.event, feature="event", max_distance=100_000_000
    )

    base_report = pd.Series({
        "mut_id": mut_id,
        "gene": m.gene,
        "transcript_id": reference_transcript.transcript_id,
        "primary_transcript": reference_transcript.primary_transcript,
        "splicing_engine": splicing_engine,
        "central_position": central_pos,
        "mutation_count": len(m.positions),
        "time_of_execution": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    ss_metadata = ss.report(central_pos)
    rows = []
    for variant_transcript, isoform_metadata in ss.get_viable_transcripts(metadata=True):
        onco = Oncosplice(
            reference_transcript.protein,
            variant_transcript.protein,
            reference_transcript.cons_vector,
        )
        rows.append(
            pd.concat([
                base_report,
                ss_metadata,
                isoform_metadata,
                pd.Series({
                    "reference_mrna": reference_transcript.mature_mrna.seq,
                    "variant_mrna": variant_transcript.mature_mrna.seq,
                }),
                onco.get_analysis_series(),
            ])
        )

    return pd.DataFrame(rows)


def oncosplice_top_isoform(
    mut_id: str,
    transcript_id: str | None = None,
    splicing_engine: str = "spliceai",
    organism: str = "hg38",
) -> pd.Series | None:
    """
    Get the most likely non-reference isoform for a mutation.

    Returns Series with full oncosplice analysis, or None if no missplicing detected.
    """
    df = oncosplice_pipeline(mut_id, transcript_id, splicing_engine, organism)

    if df.empty:
        return None

    variants = df[df["summary"] != "-"]

    if variants.empty:
        return None

    return variants.iloc[0]


def max_splicing_delta(
    mut_id: str,
    transcript_id: str | None = None,
    splicing_engine: str = "spliceai",
    organism: str = "hg38",
) -> float:
    """
    Get the maximum splice site probability change for a mutation.
    """
    m = MutationalEvent(mut_id)
    assert m.compatible(), "Mutations in event are incompatible"

    reference_transcript = (
        Gene.from_file(m.gene, organism=organism)
        .transcript(transcript_id)
        .generate_pre_mrna()
        .generate_mature_mrna()
        .generate_protein()
    )

    tl = TranscriptLibrary(reference_transcript, m)
    splicing_results = tl.predict_splicing(
        m.central_position, engine=splicing_engine, inplace=True
    ).get_event_columns("event")

    ss = SpliceSimulator(
        splicing_results, tl.event, feature="event", max_distance=100_000_000
    )

    return ss.max_splicing_delta("event_prob")


# Keep old name for backwards compatibility
oncosplice_pipeline_single_transcript = oncosplice_pipeline
