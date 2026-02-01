# oncosplice/variants.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

__all__ = ["Mutation", "MutationalEvent", "MutationLibrary"]

# GENE:CHR:POS:REF:ALT
_MUTATION_ID_RE = re.compile(
    r"^([^:]+):([^:]+):(\d+):([ACGTN\-]+):([ACGTN\-]+)$",
    re.IGNORECASE,
)


class Mutation:
    """Represents a single mutation with genomic coordinates and alleles."""

    def __init__(self, gene: str, chrom: str, pos: Union[int, str], ref: str, alt: str):
        if not gene:
            raise ValueError("Gene name cannot be empty")
        if not chrom:
            raise ValueError("Chromosome cannot be empty")
        if not ref or not alt:
            raise ValueError("Reference and alternate alleles cannot be empty")

        self.gene = gene
        self.chrom = chrom

        try:
            self.pos = int(pos)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Position must be numeric, got '{pos}'") from e

        if self.pos < 0:
            raise ValueError(f"Position must be non-negative, got {self.pos}")

        valid_chars = set("ACGTN-")
        ref_u = ref.upper()
        alt_u = alt.upper()
        if not all(c in valid_chars for c in ref_u):
            raise ValueError(f"Invalid characters in reference allele: {ref}")
        if not all(c in valid_chars for c in alt_u):
            raise ValueError(f"Invalid characters in alternate allele: {alt}")

        self.ref = ref_u
        self.alt = alt_u
        self.mut_type = self._infer_type()

    @classmethod
    def from_id(cls, mut_id: str) -> "Mutation":
        m = _MUTATION_ID_RE.match(mut_id.strip())
        if not m:
            raise ValueError(
                f"Invalid mutation ID '{mut_id}'. Expected GENE:CHROM:POS:REF:ALT"
            )
        return cls(*m.groups())

    def _infer_type(self) -> str:
        if self.ref == "-" or self.alt == "-":
            return "indel"
        if len(self.ref) == len(self.alt) == 1:
            return "snp"
        return "indel"

    @property
    def span(self) -> int:
        ref_len = 0 if self.ref == "-" else len(self.ref)
        alt_len = 0 if self.alt == "-" else len(self.alt)
        return max(ref_len, alt_len, 1)

    @property
    def end(self) -> int:
        return self.pos + self.span

    def overlaps_with(self, other: "Mutation") -> bool:
        if not isinstance(other, Mutation):
            raise TypeError(f"Expected Mutation, got {type(other).__name__}")
        if self.chrom != other.chrom:
            return False
        return not (self.end <= other.pos or other.end <= self.pos)

    def to_dict(self) -> Dict[str, Union[str, int]]:
        return {
            "gene": self.gene,
            "chrom": self.chrom,
            "pos": self.pos,
            "ref": self.ref,
            "alt": self.alt,
            "type": self.mut_type,
        }

    def __repr__(self) -> str:
        return f"{self.gene}:{self.chrom}:{self.pos}:{self.ref}:{self.alt}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Mutation):
            return False
        return (
            self.gene == other.gene
            and self.chrom == other.chrom
            and self.pos == other.pos
            and self.ref == other.ref
            and self.alt == other.alt
        )

    def __hash__(self) -> int:
        return hash((self.gene, self.chrom, self.pos, self.ref, self.alt))


class MutationalEvent:
    """Represents a compound mutational event (one or more mutations)."""

    def __init__(self, mut_id: str):
        if not mut_id:
            raise ValueError("Mutation ID cannot be empty")

        self.raw = mut_id.strip()
        try:
            self.mutations: List[Mutation] = self._parse_mutations(self.raw)
        except Exception as e:
            raise ValueError(f"Failed to parse mutation ID '{mut_id}': {e}") from e

        if not self.mutations:
            raise ValueError(f"No valid mutations found in '{mut_id}'")

        self.gene = self._verify_same_gene()

    def __len__(self) -> int:
        return len(self.mutations)

    @staticmethod
    def _parse_mutations(mut_id: str) -> List[Mutation]:
        parts = re.split(r"[|,]", mut_id)
        out: List[Mutation] = []
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            m = _MUTATION_ID_RE.match(part)
            if not m:
                raise ValueError(
                    f"Invalid format for mutation #{i+1}: '{part}'. "
                    "Expected GENE:CHROM:POS:REF:ALT"
                )
            out.append(Mutation(*m.groups()))
        return out

    def _verify_same_gene(self) -> str:
        genes = {m.gene for m in self.mutations}
        if len(genes) != 1:
            raise ValueError(
                f"All mutations must be in the same gene, found: {', '.join(sorted(genes))}"
            )
        return genes.pop()

    @property
    def chrom(self) -> str:
        chroms = {m.chrom for m in self.mutations}
        if len(chroms) != 1:
            raise ValueError(
                f"Mutations span multiple chromosomes: {', '.join(sorted(chroms))}"
            )
        return chroms.pop()

    @property
    def positions(self) -> List[int]:
        return [m.pos for m in self.mutations]

    @property
    def central_position(self) -> int:
        return int(np.mean(self.positions))

    @property
    def position(self) -> int:
        return self.central_position

    @property
    def types(self) -> List[str]:
        return [m.mut_type for m in self.mutations]

    def compatible(self) -> bool:
        for i, m1 in enumerate(self.mutations):
            for m2 in self.mutations[i + 1 :]:
                if m1.overlaps_with(m2):
                    return False
        return True

    def validate(self) -> None:
        if not self.mutations:
            raise ValueError("Event contains no mutations")

        if not self.compatible():
            overlapping = []
            for i, m1 in enumerate(self.mutations):
                for m2 in self.mutations[i + 1 :]:
                    if m1.overlaps_with(m2):
                        overlapping.append(f"{m1} overlaps with {m2}")
            raise ValueError(
                f"Mutations are not compatible: {'; '.join(overlapping)}"
            )

        chroms = {m.chrom for m in self.mutations}
        if len(chroms) > 1:
            raise ValueError(
                f"Mutations span multiple chromosomes: {', '.join(sorted(chroms))}"
            )

    def to_dataframe(self) -> pd.DataFrame:
        if not self.mutations:
            return pd.DataFrame(
                columns=["gene", "chrom", "pos", "ref", "alt", "type"]
            )
        return pd.DataFrame([m.to_dict() for m in self.mutations])

    def mutation_args(self) -> List[Tuple[int, str, str]]:
        return [(m.pos, m.ref, m.alt) for m in self.mutations]

    def __iter__(self):
        return iter(self.mutation_args())

    def __repr__(self) -> str:
        muts = ", ".join(f"{m.pos}:{m.ref}>{m.alt}" for m in self.mutations)
        return f"MutationalEvent({self.gene} -> [{muts}])"

    def __str__(self) -> str:
        return f"{self.gene}: {len(self.mutations)} mutation(s)"


class MutationLibrary:
    """
    Collection of mutational events built from IDs, text files, or VCF files.

    events: mapping from raw mutation ID string -> MutationalEvent (validated)
    """

    def __init__(self, events: Optional[Dict[str, MutationalEvent]] = None):
        self.events: Dict[str, MutationalEvent] = events or {}
        self._errors: Dict[str, str] = {}

    @classmethod
    def from_mutation_ids(
        cls,
        mut_ids: Iterable[str],
        *,
        validate: bool = True,
        skip_invalid: bool = True,
    ) -> "MutationLibrary":
        events: Dict[str, MutationalEvent] = {}
        errors: Dict[str, str] = {}

        for mid in mut_ids:
            mid = mid.strip()
            if not mid:
                continue

            try:
                ev = MutationalEvent(mid)
                if validate:
                    ev.validate()
                events[mid] = ev
            except Exception as e:
                if skip_invalid:
                    errors[mid] = str(e)
                    continue
                raise

        lib = cls(events)
        lib._errors = errors
        return lib

    @classmethod
    def from_text_file(
        cls,
        path: Union[str, Path],
        comment_char: str = "#",
        *,
        validate: bool = True,
        skip_invalid: bool = True,
    ) -> "MutationLibrary":
        p = Path(path)
        mut_ids: List[str] = []
        with p.open() as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith(comment_char):
                    continue
                mut_ids.append(line)
        return cls.from_mutation_ids(
            mut_ids,
            validate=validate,
            skip_invalid=skip_invalid,
        )

    @classmethod
    def from_vcf(
        cls,
        path: Union[str, Path],
        gene_field: Optional[str] = "GENE",
        *,
        validate: bool = True,
        skip_invalid: bool = True,
    ) -> "MutationLibrary":
        p = Path(path)

        df = pd.read_csv(
            p,
            sep="\t",
            comment="#",
            dtype={"CHROM": str},
        )

        required = {"CHROM", "POS", "REF", "ALT"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"VCF is missing required columns: {', '.join(sorted(missing))}"
            )

        mut_ids: List[str] = []
        for _, row in df.iterrows():
            chrom = str(row["CHROM"])
            pos = int(row["POS"])
            ref = str(row["REF"])
            alts = str(row["ALT"]).split(",")

            if gene_field is not None and gene_field in row and pd.notna(row[gene_field]):
                gene = str(row[gene_field])
            else:
                gene = "."

            for alt in alts:
                mut_ids.append(f"{gene}:{chrom}:{pos}:{ref}:{alt}")

        return cls.from_mutation_ids(
            mut_ids,
            validate=validate,
            skip_invalid=skip_invalid,
        )

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self):
        return iter(self.events.items())

    def __contains__(self, mut_id: str) -> bool:
        return mut_id in self.events

    def get(self, mut_id: str) -> Optional[MutationalEvent]:
        return self.events.get(mut_id)

    def add(self, mut_id: str, *, validate: bool = True) -> Optional[MutationalEvent]:
        mut_id = mut_id.strip()
        if not mut_id:
            return None

        try:
            ev = MutationalEvent(mut_id)
            if validate:
                ev.validate()
            self.events[ev.raw] = ev
            return ev
        except Exception as e:
            self._errors[mut_id] = str(e)
            return None

    def to_dataframe(self) -> pd.DataFrame:
        records: List[Dict[str, Union[str, int]]] = []
        for eid, event in self.events.items():
            df = event.to_dataframe()
            if not df.empty:
                df = df.copy()
                df["event_id"] = eid
                records.append(df)
        if not records:
            return pd.DataFrame(
                columns=["event_id", "gene", "chrom", "pos", "ref", "alt", "type"]
            )
        return pd.concat(records, ignore_index=True)

    @property
    def errors(self) -> Dict[str, str]:
        return dict(self._errors)