# oncosplice/splice_graph.py
from __future__ import annotations

from collections import defaultdict
import hashlib
from typing import Dict, Generator, List, Tuple

import numpy as np
import pandas as pd
from pandas import Series


def _short_hash(items: Tuple) -> str:
    """Generate a short hash string from a tuple."""
    encoded = repr(items).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()[:8]


class SpliceSimulator:
    """
    Builds a splice-site graph from a splicing DataFrame and enumerates isoform paths.
    """

    def __init__(self, splicing_df: pd.DataFrame, transcript, max_distance: int, feature: str = "event"):
        self.full_df = splicing_df
        self.feature = feature
        self.rev = transcript.rev
        self.transcript_start = transcript.transcript_start
        self.transcript_end = transcript.transcript_end
        self.donors = transcript.donors
        self.acceptors = transcript.acceptors
        self.transcript = transcript
        self.max_distance = max_distance

        self.set_donor_nodes()
        self.set_acceptor_nodes()

    def _compute_splice_df(self, site_type: str) -> pd.DataFrame:
        feature_col = f"{self.feature}_prob"
        df = getattr(self.full_df, site_type + "s").copy()
        site_set = getattr(self, site_type + "s")

        missing = set(site_set) - set(df.index)
        if missing:
            df = pd.concat([df, pd.DataFrame(index=list(missing))], axis=0)
            df.loc[list(missing), ["annotated", "ref_prob", feature_col]] = [True, 1, 1]

        if "annotated" not in df.columns:
            df["annotated"] = False
        else:
            df["annotated"] = df["annotated"].where(df["annotated"].notna(), False).astype(bool)

        df.sort_index(ascending=not self.rev, inplace=True)

        MIN_INCREASE_RATIO = 0.2

        df["discovered_delta"] = np.where(
            ~df["annotated"],
            (df[feature_col] - df["ref_prob"]),
            np.nan,
        )
        df["discovered_delta"] = df["discovered_delta"].where(
            df["discovered_delta"] >= MIN_INCREASE_RATIO, 0
        )

        with np.errstate(divide="ignore", invalid="ignore"):
            df["deleted_delta"] = np.where(
                (df["ref_prob"] > 0) & df["annotated"],
                (df[feature_col] - df["ref_prob"]) / df["ref_prob"],
                0,
            )
        df["deleted_delta"] = df["deleted_delta"].clip(upper=0)

        df["P"] = df["annotated"].astype(float) + df["discovered_delta"] + df["deleted_delta"]
        return df

    @property
    def donor_df(self) -> pd.DataFrame:
        return self._compute_splice_df("donor")

    @property
    def acceptor_df(self) -> pd.DataFrame:
        return self._compute_splice_df("acceptor")

    def report(self, pos):
        metadata = self.find_splice_site_proximity(pos)
        metadata["donor_events"] = self.donor_df[
            (self.donor_df.deleted_delta.abs() > 0.2)
            | (self.donor_df.discovered_delta.abs() > 0.2)
        ].reset_index().to_json()
        metadata["acceptor_events"] = self.acceptor_df[
            (self.acceptor_df.deleted_delta.abs() > 0.2)
            | (self.acceptor_df.discovered_delta.abs() > 0.2)
        ].reset_index().to_json()
        metadata["missplicing"] = self.max_splicing_delta("event_prob")
        return metadata

    def summarize_events(self, threshold: float = 0.2) -> str:
        """
        Generate human-readable summary of splice site changes.

        Returns text describing discovered and deleted donors/acceptors.
        Format: "D(position) ref_prob -> event_prob" or "A(position) ref_prob -> event_prob"
        """
        feature_col = f"{self.feature}_prob"
        lines = []

        # Process donors
        donor_df = self.donor_df
        discovered_donors = donor_df[donor_df["discovered_delta"].abs() >= threshold]
        deleted_donors = donor_df[donor_df["deleted_delta"].abs() >= threshold]

        if len(discovered_donors) > 0 or len(deleted_donors) > 0:
            lines.append("=== DONORS ===")

            if len(discovered_donors) > 0:
                lines.append("Discovered:")
                for pos, row in discovered_donors.iterrows():
                    ref = row.get("ref_prob", 0)
                    evt = row.get(feature_col, row.get("event_prob", 0))
                    lines.append(f"  D({pos}) {ref:.2f} -> {evt:.2f} [+{evt-ref:.2f}]")

            if len(deleted_donors) > 0:
                lines.append("Deleted:")
                for pos, row in deleted_donors.iterrows():
                    ref = row.get("ref_prob", 0)
                    evt = row.get(feature_col, row.get("event_prob", 0))
                    lines.append(f"  D({pos}) {ref:.2f} -> {evt:.2f} [{evt-ref:.2f}]")

        # Process acceptors
        acceptor_df = self.acceptor_df
        discovered_acceptors = acceptor_df[acceptor_df["discovered_delta"].abs() >= threshold]
        deleted_acceptors = acceptor_df[acceptor_df["deleted_delta"].abs() >= threshold]

        if len(discovered_acceptors) > 0 or len(deleted_acceptors) > 0:
            lines.append("=== ACCEPTORS ===")

            if len(discovered_acceptors) > 0:
                lines.append("Discovered:")
                for pos, row in discovered_acceptors.iterrows():
                    ref = row.get("ref_prob", 0)
                    evt = row.get(feature_col, row.get("event_prob", 0))
                    lines.append(f"  A({pos}) {ref:.2f} -> {evt:.2f} [+{evt-ref:.2f}]")

            if len(deleted_acceptors) > 0:
                lines.append("Deleted:")
                for pos, row in deleted_acceptors.iterrows():
                    ref = row.get("ref_prob", 0)
                    evt = row.get(feature_col, row.get("event_prob", 0))
                    lines.append(f"  A({pos}) {ref:.2f} -> {evt:.2f} [{evt-ref:.2f}]")

        if not lines:
            return "No significant splice site changes detected."

        return "\n".join(lines)

    def max_splicing_delta(self, event: str) -> float:
        all_diffs = []
        for site_type in ["donors", "acceptors"]:
            df = self.full_df[site_type]
            diffs = (df[event] - df["ref_prob"]).tolist()
            all_diffs.extend(diffs)
        return max(all_diffs, key=abs)

    def set_donor_nodes(self) -> None:
        donors = self.donor_df.P
        donor_list = list(donors[donors > 0].round(2).items())
        donor_list.append((self.transcript_end, 1))
        self.donor_nodes = sorted(
            donor_list, key=lambda x: int(x[0]), reverse=bool(self.rev)
        )

    def set_acceptor_nodes(self) -> None:
        acceptors = self.acceptor_df.P
        acceptor_list = list(acceptors[acceptors > 0].round(2).items())
        acceptor_list.insert(0, (self.transcript_start, 1.0))
        self.acceptor_nodes = sorted(
            acceptor_list, key=lambda x: int(x[0]), reverse=bool(self.rev)
        )

    def generate_graph(self) -> Dict[Tuple[int, str], List[Tuple[int, str, float]]]:
        adjacency_list: Dict[Tuple[int, str], List[Tuple[int, str, float]]] = defaultdict(list)

        # donor -> acceptor
        for d_pos, d_prob in self.donor_nodes:
            running_prob = 1.0
            for a_pos, a_prob in self.acceptor_nodes:
                correct_orientation = ((a_pos > d_pos and not self.rev) or (a_pos < d_pos and self.rev))
                distance_valid = abs(a_pos - d_pos) <= self.max_distance
                if not (correct_orientation and distance_valid):
                    continue

                if not self.rev:
                    in_between_acceptors = sum(1 for a, _ in self.acceptor_nodes if d_pos < a < a_pos)
                    in_between_donors = sum(1 for d, _ in self.donor_nodes if d_pos < d < a_pos)
                else:
                    in_between_acceptors = sum(1 for a, _ in self.acceptor_nodes if a_pos < a < d_pos)
                    in_between_donors = sum(1 for d, _ in self.donor_nodes if a_pos < d < d_pos)

                if in_between_donors == 0 or in_between_acceptors == 0:
                    adjacency_list[(d_pos, "donor")].append((a_pos, "acceptor", a_prob))
                    running_prob -= a_prob
                else:
                    if running_prob > 0:
                        adjacency_list[(d_pos, "donor")].append(
                            (a_pos, "acceptor", a_prob * running_prob)
                        )
                        running_prob -= a_prob
                    else:
                        break

        # acceptor -> donor
        for a_pos, a_prob in self.acceptor_nodes:
            running_prob = 1.0
            for d_pos, d_prob in self.donor_nodes:
                correct_orientation = ((d_pos > a_pos and not self.rev) or (d_pos < a_pos and self.rev))
                distance_valid = abs(d_pos - a_pos) <= self.max_distance
                if not (correct_orientation and distance_valid):
                    continue

                if not self.rev:
                    in_between_acceptors = sum(1 for a, _ in self.acceptor_nodes if a_pos < a < d_pos)
                    in_between_donors = sum(1 for d, _ in self.donor_nodes if a_pos < d < d_pos)
                else:
                    in_between_acceptors = sum(1 for a, _ in self.acceptor_nodes if d_pos < a < a_pos)
                    in_between_donors = sum(1 for d, _ in self.donor_nodes if d_pos < d < a_pos)

                tag = "donor" if d_pos != self.transcript_end else "transcript_end"
                if in_between_acceptors == 0:
                    adjacency_list[(a_pos, "acceptor")].append((d_pos, tag, d_prob))
                    running_prob -= d_prob
                else:
                    if running_prob > 0:
                        adjacency_list[(a_pos, "acceptor")].append(
                            (d_pos, tag, d_prob * running_prob)
                        )
                        running_prob -= d_prob
                    else:
                        break

        # transcript_start -> donors
        running_prob = 1.0
        for d_pos, d_prob in self.donor_nodes:
            correct_orientation = (
                (d_pos > self.transcript_start and not self.rev)
                or (d_pos < self.transcript_start and self.rev)
            )
            distance_valid = abs(d_pos - self.transcript_start) <= self.max_distance
            if correct_orientation and distance_valid:
                adjacency_list[(self.transcript_start, "transcript_start")].append(
                    (d_pos, "donor", d_prob)
                )
                running_prob -= d_prob
                if running_prob <= 0:
                    break

        # normalize outgoing edges
        for key, next_nodes in adjacency_list.items():
            total_prob = sum(prob for (_, _, prob) in next_nodes)
            if total_prob > 0:
                adjacency_list[key] = [
                    (pos, typ, round(prob / total_prob, 3))
                    for pos, typ, prob in next_nodes
                ]
        return adjacency_list

    def find_all_paths(
        self,
        graph: Dict[Tuple[int, str], List[Tuple[int, str, float]]],
        start: Tuple[int, str],
        end: Tuple[int, str],
        path: List[Tuple[int, str]] | None = None,
        probability: float = 1.0,
    ) -> Generator[Tuple[List[Tuple[int, str]], float], None, None]:
        if path is None:
            path = [start]
        else:
            path = path + [start]

        if start == end:
            yield path, probability
            return
        if start not in graph:
            return

        for next_pos, tag, prob in graph[start]:
            yield from self.find_all_paths(
                graph,
                (next_pos, tag),
                end,
                path,
                probability * prob,
            )

    # ------------------------------------------------------------------
    # Strategy 1: Competitive Zone Redistribution
    # ------------------------------------------------------------------

    def _compute_zone_probabilities(
        self, site_type: str, zone_radius: int = 50
    ) -> Dict[int, float]:
        """
        Redistribute lost probability from weakened reference sites to nearby
        cryptic sites within a competition zone.

        For each reference site, the "lost" probability (1.0 - event_prob) is
        distributed proportionally among novel sites within zone_radius bp.
        """
        feature_col = f"{self.feature}_prob"
        df = self._compute_splice_df(site_type)
        ref_positions = df[df["annotated"]].index.tolist()
        novel_positions = df[~df["annotated"] & (df["P"] > 0)].index.tolist()

        adjusted: Dict[int, float] = {}
        claimed: set = set()

        for ref_pos in ref_positions:
            ref_event_p = float(df.loc[ref_pos, feature_col])
            adjusted[ref_pos] = max(ref_event_p, 0.0)

            lost = max(0.0, 1.0 - ref_event_p)
            if lost <= 0:
                continue

            zone_novels = [
                n for n in novel_positions
                if abs(n - ref_pos) <= zone_radius and n not in claimed
            ]
            if not zone_novels:
                continue

            deltas = {n: float(df.loc[n, "P"]) for n in zone_novels}
            total_delta = sum(deltas.values())
            if total_delta <= 0:
                continue

            for n in zone_novels:
                adjusted[n] = lost * (deltas[n] / total_delta)
                claimed.add(n)

        # Unclaimed novels keep their raw P
        for n in novel_positions:
            if n not in claimed:
                adjusted[n] = float(df.loc[n, "P"])

        return adjusted

    def generate_graph_competitive(
        self, zone_radius: int = 50
    ) -> Dict[Tuple[int, str], List[Tuple[int, str, float]]]:
        """Same structure as generate_graph() but uses zone-adjusted probabilities."""
        donor_zone = self._compute_zone_probabilities("donor", zone_radius)
        acceptor_zone = self._compute_zone_probabilities("acceptor", zone_radius)

        # Rebuild node lists with zone probabilities
        donor_nodes = [
            (pos, donor_zone.get(pos, prob))
            for pos, prob in self.donor_nodes
        ]
        acceptor_nodes = [
            (pos, acceptor_zone.get(pos, prob))
            for pos, prob in self.acceptor_nodes
        ]

        return self._build_graph(donor_nodes, acceptor_nodes)

    def _build_graph(
        self,
        donor_nodes: List[Tuple[int, float]],
        acceptor_nodes: List[Tuple[int, float]],
    ) -> Dict[Tuple[int, str], List[Tuple[int, str, float]]]:
        """
        Core graph construction shared by all strategies.
        Extracted from generate_graph() so competitive/other strategies can
        supply different node probability lists.
        """
        adjacency_list: Dict[Tuple[int, str], List[Tuple[int, str, float]]] = defaultdict(list)

        # donor -> acceptor
        for d_pos, d_prob in donor_nodes:
            running_prob = 1.0
            for a_pos, a_prob in acceptor_nodes:
                correct_orientation = (a_pos > d_pos and not self.rev) or (a_pos < d_pos and self.rev)
                distance_valid = abs(a_pos - d_pos) <= self.max_distance
                if not (correct_orientation and distance_valid):
                    continue

                if not self.rev:
                    in_between_acceptors = sum(1 for a, _ in acceptor_nodes if d_pos < a < a_pos)
                    in_between_donors = sum(1 for d, _ in donor_nodes if d_pos < d < a_pos)
                else:
                    in_between_acceptors = sum(1 for a, _ in acceptor_nodes if a_pos < a < d_pos)
                    in_between_donors = sum(1 for d, _ in donor_nodes if a_pos < d < d_pos)

                if in_between_donors == 0 or in_between_acceptors == 0:
                    adjacency_list[(d_pos, "donor")].append((a_pos, "acceptor", a_prob))
                    running_prob -= a_prob
                else:
                    if running_prob > 0:
                        adjacency_list[(d_pos, "donor")].append(
                            (a_pos, "acceptor", a_prob * running_prob)
                        )
                        running_prob -= a_prob
                    else:
                        break

        # acceptor -> donor
        for a_pos, a_prob in acceptor_nodes:
            running_prob = 1.0
            for d_pos, d_prob in donor_nodes:
                correct_orientation = (d_pos > a_pos and not self.rev) or (d_pos < a_pos and self.rev)
                distance_valid = abs(d_pos - a_pos) <= self.max_distance
                if not (correct_orientation and distance_valid):
                    continue

                if not self.rev:
                    in_between_acceptors = sum(1 for a, _ in acceptor_nodes if a_pos < a < d_pos)
                    in_between_donors = sum(1 for d, _ in donor_nodes if a_pos < d < d_pos)
                else:
                    in_between_acceptors = sum(1 for a, _ in acceptor_nodes if d_pos < a < a_pos)
                    in_between_donors = sum(1 for d, _ in donor_nodes if d_pos < d < a_pos)

                tag = "donor" if d_pos != self.transcript_end else "transcript_end"
                if in_between_acceptors == 0:
                    adjacency_list[(a_pos, "acceptor")].append((d_pos, tag, d_prob))
                    running_prob -= d_prob
                else:
                    if running_prob > 0:
                        adjacency_list[(a_pos, "acceptor")].append(
                            (d_pos, tag, d_prob * running_prob)
                        )
                        running_prob -= d_prob
                    else:
                        break

        # transcript_start -> donors
        running_prob = 1.0
        for d_pos, d_prob in donor_nodes:
            correct_orientation = (
                (d_pos > self.transcript_start and not self.rev)
                or (d_pos < self.transcript_start and self.rev)
            )
            distance_valid = abs(d_pos - self.transcript_start) <= self.max_distance
            if correct_orientation and distance_valid:
                adjacency_list[(self.transcript_start, "transcript_start")].append(
                    (d_pos, "donor", d_prob)
                )
                running_prob -= d_prob
                if running_prob <= 0:
                    break

        # normalize outgoing edges
        for key, next_nodes in adjacency_list.items():
            total_prob = sum(prob for (_, _, prob) in next_nodes)
            if total_prob > 0:
                adjacency_list[key] = [
                    (pos, typ, round(prob / total_prob, 3))
                    for pos, typ, prob in next_nodes
                ]
        return adjacency_list

    # ------------------------------------------------------------------
    # Strategy 2: Log-Odds Relative Scoring
    # ------------------------------------------------------------------

    def _score_path_log_odds(
        self,
        path: List[Tuple[int, str]],
        donor_df: pd.DataFrame,
        acceptor_df: pd.DataFrame,
    ) -> float:
        """
        Score a path relative to canonical using log-odds at each splice site.

        For each node in the path:
          - If it IS a reference site: contribution = log(P)
          - If it is novel: contribution = log(P) - log(P_nearest_ref)

        Returns exp(sum_of_contributions).
        """
        log_sum = 0.0

        for pos, typ in path:
            if typ in ("transcript_start", "transcript_end"):
                continue

            if typ == "donor":
                df = donor_df
                ref_sites = self.donors
            else:
                df = acceptor_df
                ref_sites = self.acceptors

            site_p = float(df.loc[pos, "P"]) if pos in df.index else 0.01

            if pos in ref_sites:
                # Reference site: deviation from perfect (P=1.0)
                log_sum += np.log(max(site_p, 1e-6))
            else:
                # Novel site: compare to nearest reference
                if len(ref_sites) > 0:
                    nearest_ref = min(ref_sites, key=lambda r: abs(r - pos))
                    ref_p = float(df.loc[nearest_ref, "P"]) if nearest_ref in df.index else 1.0
                else:
                    ref_p = 1.0
                log_sum += np.log(max(site_p, 1e-6)) - np.log(max(ref_p, 1e-6))

        return np.exp(log_sum)

    # ------------------------------------------------------------------
    # Strategy 3: Sequential Per-Intron Decision Model
    # ------------------------------------------------------------------

    def get_viable_paths_sequential(
        self,
        min_intron_prob: float = 0.01,
        beam_width: int = 50,
        zone_radius: int = 500,
    ) -> List[Tuple[List[Tuple[int, str]], float]]:
        """
        Model splicing as sequential per-intron decisions (co-transcriptional).

        At each reference intron, the spliceosome chooses:
          1. Canonical splice (use reference donor + acceptor)
          2. Cryptic splice (use a nearby novel site for donor or acceptor)
          3. Intron retention (neither boundary is spliced)

        Uses beam search to avoid exponential blowup across many introns.
        """
        ref_introns = getattr(self.transcript, "introns", [])
        if not ref_introns:
            # Single-exon gene: return canonical path
            return [([
                (self.transcript_start, "transcript_start"),
                (self.transcript_end, "transcript_end"),
            ], 1.0)]

        donor_df = self.donor_df
        acceptor_df = self.acceptor_df

        # Build per-intron decision options
        intron_options = []  # list of list of (label, donor_pos, acceptor_pos, raw_prob)

        for t1, t2 in ref_introns:
            if not self.rev:
                d_pos, a_pos = t1, t2
            else:
                d_pos, a_pos = t2, t1

            d_p = float(donor_df.loc[d_pos, "P"]) if d_pos in donor_df.index else 1.0
            a_p = float(acceptor_df.loc[a_pos, "P"]) if a_pos in acceptor_df.index else 1.0

            options = []

            # Option 1: canonical splice
            canonical_p = d_p * a_p
            if canonical_p > min_intron_prob:
                options.append(("canonical", d_pos, a_pos, canonical_p))

            # Option 2: cryptic donor variants
            novel_donors = donor_df[
                (~donor_df["annotated"])
                & (donor_df.index >= d_pos - zone_radius)
                & (donor_df.index <= d_pos + zone_radius)
                & (donor_df["P"] > 0)
            ]
            for nd_pos in novel_donors.index:
                nd_p = float(novel_donors.loc[nd_pos, "P"])
                cp = nd_p * a_p
                if cp > min_intron_prob:
                    options.append(("cryptic_donor", int(nd_pos), a_pos, cp))

            # Option 3: cryptic acceptor variants
            novel_acceptors = acceptor_df[
                (~acceptor_df["annotated"])
                & (acceptor_df.index >= a_pos - zone_radius)
                & (acceptor_df.index <= a_pos + zone_radius)
                & (acceptor_df["P"] > 0)
            ]
            for na_pos in novel_acceptors.index:
                na_p = float(novel_acceptors.loc[na_pos, "P"])
                cp = d_p * na_p
                if cp > min_intron_prob:
                    options.append(("cryptic_acceptor", d_pos, int(na_pos), cp))

            # Option 4: intron retention
            retain_p = max(1.0 - sum(o[3] for o in options), 0.01)
            options.append(("retain", None, None, retain_p))

            # Normalize per intron
            total = sum(o[3] for o in options)
            if total > 0:
                options = [(lbl, d, a, p / total) for lbl, d, a, p in options]

            intron_options.append(options)

        # Beam search across introns
        # Each beam entry: (donors_list, acceptors_list, cumulative_prob)
        beam = [([], [], 1.0)]

        for intron_idx, options in enumerate(intron_options):
            new_beam = []
            for donors, acceptors, cum_prob in beam:
                for label, d, a, p in options:
                    new_prob = cum_prob * p
                    if label == "retain":
                        # No splice sites added for this intron
                        new_beam.append((donors[:], acceptors[:], new_prob))
                    else:
                        new_d = donors + ([d] if d is not None else [])
                        new_a = acceptors + ([a] if a is not None else [])
                        new_beam.append((new_d, new_a, new_prob))

            # Prune beam
            new_beam.sort(key=lambda x: x[2], reverse=True)
            beam = new_beam[:beam_width]

        # Convert beam entries to path format
        paths = []
        for donors, acceptors, prob in beam:
            path = [(self.transcript_start, "transcript_start")]
            # Interleave donors and acceptors in positional order
            sites = [(d, "donor") for d in donors] + [(a, "acceptor") for a in acceptors]
            sites.sort(key=lambda x: x[0], reverse=bool(self.rev))
            path.extend(sites)
            path.append((self.transcript_end, "transcript_end"))
            paths.append((path, prob))

        paths.sort(key=lambda x: x[1], reverse=True)
        return paths

    # ------------------------------------------------------------------
    # Unified get_viable_paths with strategy selection
    # ------------------------------------------------------------------

    def get_viable_paths(
        self, scoring_strategy: str = "multiplicative"
    ) -> List[Tuple[List[Tuple[int, str]], float]]:
        """
        Enumerate all viable splice paths from transcript start to end.

        Args:
            scoring_strategy: One of:
                - "multiplicative" (default): product of edge weights
                - "competitive": zone-based probability redistribution
                - "log_odds": paths scored relative to canonical via log-odds
                - "sequential": per-intron co-transcriptional decision model
        """
        if scoring_strategy == "sequential":
            return self.get_viable_paths_sequential()

        # Build graph (strategy determines edge weights)
        if scoring_strategy == "competitive":
            graph = self.generate_graph_competitive()
        else:
            graph = self.generate_graph()

        start_node = (self.transcript_start, "transcript_start")
        end_node = (self.transcript_end, "transcript_end")
        paths = list(self.find_all_paths(graph, start_node, end_node))

        if scoring_strategy == "log_odds":
            # Re-score each path using log-odds relative to canonical
            donor_df = self.donor_df
            acceptor_df = self.acceptor_df
            paths = [
                (path, self._score_path_log_odds(path, donor_df, acceptor_df))
                for path, _ in paths
            ]
            # Normalize scores to sum to 1.0
            total = sum(p for _, p in paths)
            if total > 0:
                paths = [(path, prob / total) for path, prob in paths]

        paths.sort(key=lambda x: x[1], reverse=True)
        return paths

    def isoforms_df(self, scoring_strategy: str = "multiplicative") -> pd.DataFrame:
        """
        Return a DataFrame of all viable isoforms with probabilities and missplicing descriptions.

        Columns:
            - isoform_id: unique hash of the splice path
            - probability: probability/prevalence of this isoform
            - splicing_changes: short missplicing event codes (ES, IR, PES, PIR, NE, or "-" for canonical)
            - exon_skipping: full exon skipping details
            - partial_exon_skipping: partial exon skipping (truncation) details
            - intron_retention: full intron retention details
            - partial_intron_retention: partial intron retention details
            - novel_exon: novel/cryptic exon details
        """
        rows = []
        for t, md in self.get_viable_transcripts(metadata=True, scoring_strategy=scoring_strategy):
            rows.append({
                "isoform_id": md.get("isoform_id", ""),
                "probability": md.get("isoform_prevalence", 0.0),
                "splicing_changes": md.get("summary", "-"),
                "exon_skipping": md.get("es", ""),
                "partial_exon_skipping": md.get("pes", ""),
                "intron_retention": md.get("ir", ""),
                "partial_intron_retention": md.get("pir", ""),
                "novel_exon": md.get("ne", ""),
            })

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows)

    def _is_implausible_ir_path(self, var_transcript) -> bool:
        """
        Check if this transcript has intron retention that is implausible
        because nearby cryptic splice sites compensate for the lost original sites.

        Returns True if the path should be filtered out.

        Key insight: If the variant uses ANY splice site near a reference intron
        boundary, the intron is being spliced (possibly at a shifted position).
        True IR only occurs when NO splice sites are used near BOTH boundaries.
        """
        ref_introns = getattr(self.transcript, "introns", [])

        if not ref_introns:
            return False

        TOLERANCE = 500  # bp - consider splice sites within this distance as "covering" the boundary
        MIN_TOTAL_PROB = 0.5  # if total prob >= this, cryptic sites could compensate

        var_donors = set(var_transcript.donors)
        var_acceptors = set(var_transcript.acceptors)

        donor_df = self.donor_df
        acceptor_df = self.acceptor_df

        for t1, t2 in ref_introns:
            # Determine which end is donor and which is acceptor based on strand
            if not self.rev:
                donor_pos, acceptor_pos = t1, t2  # + strand
            else:
                donor_pos, acceptor_pos = t2, t1  # - strand

            # Check if variant uses ANY donor near the reference donor position
            donor_used = any(
                abs(d - donor_pos) <= TOLERANCE
                for d in var_donors
            )

            # Check if variant uses ANY acceptor near the reference acceptor position
            acceptor_used = any(
                abs(a - acceptor_pos) <= TOLERANCE
                for a in var_acceptors
            )

            # If both boundaries are used (possibly at shifted positions),
            # the intron is being spliced out - NOT retained
            if donor_used and acceptor_used:
                continue

            # At least one boundary is NOT used - this path has potential IR
            # Check if cryptic sites with high probability exist but aren't being used
            # (which would make this IR path implausible)

            nearby_donors = donor_df.loc[
                (donor_df.index >= donor_pos - TOLERANCE) &
                (donor_df.index <= donor_pos + TOLERANCE)
            ]
            total_donor_prob = nearby_donors["P"].sum() if len(nearby_donors) > 0 else 0

            nearby_acceptors = acceptor_df.loc[
                (acceptor_df.index >= acceptor_pos - TOLERANCE) &
                (acceptor_df.index <= acceptor_pos + TOLERANCE)
            ]
            total_acceptor_prob = nearby_acceptors["P"].sum() if len(nearby_acceptors) > 0 else 0

            # If both boundaries have high probability cryptic sites available,
            # but this path doesn't use them, the IR is implausible
            if total_donor_prob >= MIN_TOTAL_PROB and total_acceptor_prob >= MIN_TOTAL_PROB:
                return True

        return False

    def get_viable_transcripts(self, metadata: bool = False, scoring_strategy: str = "multiplicative"):
        paths = self.get_viable_paths(scoring_strategy=scoring_strategy)

        for path, prob in paths:
            donors = [pos for pos, typ in path if typ == "donor"]
            acceptors = [pos for pos, typ in path if typ == "acceptor"]

            t = self.transcript.clone()
            t.donors = [d for d in donors if d != t.transcript_end]
            t.acceptors = [a for a in acceptors if a != t.transcript_start]
            t.path_weight = prob
            t.path_hash = _short_hash(tuple(donors + acceptors))
            t.generate_mature_mrna().generate_protein()

            # Filter out implausible IR paths (where cryptic sites compensate)
            if self._is_implausible_ir_path(t):
                continue

            if metadata:
                md = pd.concat(
                    [
                        self.compare_splicing_to_reference(t),
                        pd.Series(
                            {
                                "isoform_prevalence": t.path_weight,
                                "isoform_id": t.path_hash,
                            }
                        ),
                    ]
                )
                yield t, md
            else:
                yield t

    def find_splice_site_proximity(self, pos: int) -> Series:
        def result(region, index, start, end):
            return pd.Series(
                {
                    "region": region,
                    "index": index + 1,
                    "5'_dist": abs(pos - min(start, end)),
                    "3'_dist": abs(pos - max(start, end)),
                }
            )

        if not hasattr(self.transcript, "exons") or not hasattr(self.transcript, "introns"):
            return pd.Series(
                {"region": None, "index": None, "5'_dist": np.inf, "3'_dist": np.inf}
            )

        for i, (start, end) in enumerate(self.transcript.exons):
            if min(start, end) <= pos <= max(start, end):
                return result("exon", i, start, end)

        for i, (start, end) in enumerate(self.transcript.introns):
            if min(start, end) <= pos <= max(start, end):
                return result("intron", i, start, end)

        return pd.Series(
            {"region": None, "index": None, "5'_dist": np.inf, "3'_dist": np.inf}
        )

    def define_missplicing_events(self, var) -> Tuple[str, str, str, str, str]:
        ref = self.transcript
        ref_introns, ref_exons = getattr(ref, "introns", []), getattr(ref, "exons", [])
        var_introns, var_exons = getattr(var, "introns", []), getattr(var, "exons", [])

        num_ref_exons = len(ref_exons)
        num_ref_introns = len(ref_introns)

        pes, pir, es, ne, ir = [], [], [], [], []
        pir_intron_indices = set()  # Track which introns have PIR

        # Partial exon skipping (exon truncation)
        for exon_count, (t1, t2) in enumerate(ref_exons):
            for (s1, s2) in var_exons:
                if (not ref.rev and ((s1 == t1 and s2 < t2) or (s1 > t1 and s2 == t2))) or (
                    ref.rev and ((s1 == t1 and s2 > t2) or (s1 < t1 and s2 == t2))
                ):
                    pes.append(
                        f"Exon {exon_count+1}/{num_ref_exons} truncated: {(t1, t2)} --> {(s1, s2)}"
                    )

        # Partial intron retention (one boundary preserved, other shifted)
        for intron_count, (t1, t2) in enumerate(ref_introns):
            for (s1, s2) in var_introns:
                # Check if one boundary matches and the intron is shorter (partial retention)
                if (not ref.rev and ((s1 == t1 and s2 < t2) or (s1 > t1 and s2 == t2))) or (
                    ref.rev and ((s1 == t1 and s2 > t2) or (s1 < t1 and s2 == t2))
                ):
                    pir.append(
                        f"Intron {intron_count+1}/{num_ref_introns} partially retained: {(t1, t2)} --> {(s1, s2)}"
                    )
                    pir_intron_indices.add(intron_count)

        # Exon skipping (both boundaries missing)
        for exon_count, (t1, t2) in enumerate(ref_exons):
            if t1 not in var.acceptors and t2 not in var.donors:
                es.append(
                    f"Exon {exon_count+1}/{num_ref_exons} skipped: {(t1, t2)}"
                )

        # Novel exon (boundaries not in reference)
        for (s1, s2) in var_exons:
            if s1 not in ref.acceptors and s2 not in ref.donors:
                ne.append(f"Novel Exon: {(s1, s2)}")

        # Full intron retention - only if NOT already partial retention
        # AND no splice sites are being used near the intron boundaries
        TOLERANCE = 500  # bp - consider splice sites within this distance as "covering" the boundary

        for intron_count, (t1, t2) in enumerate(ref_introns):
            if intron_count in pir_intron_indices:
                continue  # Already classified as PIR

            # Check if the intron is preserved exactly in variant
            intron_preserved = any(s1 == t1 and s2 == t2 for s1, s2 in var_introns)
            if intron_preserved:
                continue  # Intron is properly spliced

            # Determine donor/acceptor positions based on strand
            if not ref.rev:
                donor_pos, acceptor_pos = t1, t2  # + strand
            else:
                donor_pos, acceptor_pos = t2, t1  # - strand

            # Check if variant uses ANY splice site near each boundary
            # If so, the intron is being spliced (at shifted positions), not retained
            donor_used = any(abs(d - donor_pos) <= TOLERANCE for d in var.donors)
            acceptor_used = any(abs(a - acceptor_pos) <= TOLERANCE for a in var.acceptors)

            if donor_used and acceptor_used:
                continue  # Intron is being spliced at shifted positions, not retained

            # If we get here, the intron is truly retained
            ir.append(
                f"Intron {intron_count+1}/{num_ref_introns} retained: {(t1, t2)}"
            )

        return ",".join(pes), ",".join(pir), ",".join(es), ",".join(ne), ",".join(ir)

    def summarize_missplicing_event(self, pes, pir, es, ne, ir) -> str:
        event = []
        if pes:
            event.append("PES")
        if es:
            event.append("ES")
        if pir:
            event.append("PIR")
        if ir:
            event.append("IR")
        if ne:
            event.append("NE")
        return ",".join(event) if event else "-"

    def compare_splicing_to_reference(self, transcript_variant) -> Series:
        pes, pir, es, ne, ir = self.define_missplicing_events(transcript_variant)
        return pd.Series(
            {
                "pes": pes,
                "pir": pir,
                "es": es,
                "ne": ne,
                "ir": ir,
                "summary": self.summarize_missplicing_event(pes, pir, es, ne, ir),
            }
        )