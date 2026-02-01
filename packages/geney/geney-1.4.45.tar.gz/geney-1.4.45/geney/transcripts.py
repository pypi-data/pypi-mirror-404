# oncosplice/transcripts.py
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple, Optional

from .engines import adjoin_splicing_outcomes, predict_splicing


class TranscriptLibrary:
    """
    Holds a reference transcript and mutated variants derived from a MutationalEvent.

    _transcripts: {'ref': ref_transcript, 'event': all_mutations, 'mut1': first mutation, ...}
    """

    def __init__(self, reference_transcript, mutations: Iterable[Tuple[int, str, str]]):
        self.ref = reference_transcript.clone()
        self.event = reference_transcript.clone()
        self._transcripts: Dict[str, object] = {"ref": self.ref, "event": self.event}

        for i, (pos, ref, alt) in enumerate(mutations):
            self.event.pre_mrna.apply_mutations((pos, ref, alt))
            if len(list(mutations)) > 1:
                t = reference_transcript.clone()
                t.pre_mrna.apply_mutations((pos, ref, alt))
                name = f"mut{i+1}"
                self._transcripts[name] = t
                setattr(self, name, t)

        setattr(self, "ref", self.ref)
        setattr(self, "event", self.event)

    def predict_splicing(self, pos, engine: str = "spliceai", inplace: bool = False):
        """
        Run splicing predictions for all transcripts at a genomic position.
        Assumes each transcript has pre_mrna.predict_splicing(pos, engine, inplace=True)
        and stores results in pre_mrna.predicted_splicing.
        """
        splicing_predictions = {
            k: predict_splicing(t.pre_mrna, pos, engine=engine)
            for k, t in self._transcripts.items()
        }
        self.splicing_results = adjoin_splicing_outcomes(
            {k: df for k, df in splicing_predictions.items()},
            self.ref,
        )
        if inplace:
            return self
        
        return self.splicing_results

    def get_event_columns(self, event_name: str, sites=("donors", "acceptors")):
        """
        Extract selected columns for a given event label ('event', 'mut1', etc.).
        Returns a DataFrame subset of self.splicing_results.
        """
        if not hasattr(self, "splicing_results"):
            raise ValueError("You must run predict_splicing() first.")

        metrics = (f"{event_name}_prob", "ref_prob", "annotated")
        cols = [(site, metric) for site in sites for metric in metrics]
        return self.splicing_results.loc[:, cols]

    def __getitem__(self, key):
        return self._transcripts[key]

    def __iter__(self):
        return iter(self._transcripts.items())