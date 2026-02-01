# Geney - Splicing and Oncosplice Analysis Library

A Python library for analyzing splicing events and their impact on protein conservation in cancer genomics.

## Overview

Geney provides tools for:
1. **Variant representation** - Parse and validate genomic mutations
2. **Splicing prediction** - Predict splice site changes using SpliceAI or Pangolin
3. **Splice simulation** - Generate all viable transcript isoforms from predicted splicing
4. **Oncosplice scoring** - Assess impact of splicing changes on conserved protein domains

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Note: spliceai must be installed via conda
conda install -c bioconda spliceai

# Install geney in development mode
pip install -e .
```

## Core Classes

### 1. `MutationalEvent` (from `variants.py`)

Represents one or more genomic mutations.

**Input:**
```python
from geney.variants import MutationalEvent

# Single mutation
m = MutationalEvent("KRAS:12:25227343:G:T")

# Multiple mutations (epistasis)
m = MutationalEvent("KRAS:12:25227343:G:T|KRAS:12:25227344:A:T")
```

**Key Properties:**
- `.gene` - Gene name (str)
- `.central_position` - Central position (density center) of all mutations (int)
- `.position` - Alias for `.central_position` (backward compatibility)
- `.positions` - List of all mutation positions (List[int])
- `.compatible()` - Returns True if mutations don't overlap (bool)
- Iterable: yields `(pos, ref, alt)` tuples

**Note on Central Position:**
- For single mutations: equals the mutation position
- For multiple mutations: equals the mean (centroid) of all positions
- Used as the analysis point for splicing predictions

**Output:** Structured mutation object for downstream analysis

---

### 2. `TranscriptLibrary` (from `TranscriptLibrary.py`)

Creates reference and mutated transcript variants, then predicts splicing changes.

**Input:**
```python
from geney import TranscriptLibrary

tl = TranscriptLibrary(
    reference_transcript,  # seqmat Transcript object
    mutations              # MutationalEvent object (iterable)
)
```

**Key Methods:**
```python
# Predict splicing for all transcripts
tl.predict_splicing(
    pos=25227343,           # Position to analyze
    engine='spliceai',      # 'spliceai' or 'pangolin'
    inplace=True            # Returns self if True
)

# Get splicing results for specific event
splicing_df = tl.get_event_columns('event')
```

**Output:**
- `splicing_df` is a MultiIndex DataFrame with:
  - **Rows:** Genomic positions
  - **Columns:** MultiIndex with:
    - Level 0: `'donors'` or `'acceptors'`
    - Level 1: `'event_prob'`, `'ref_prob'`, `'annotated'`
  - **Values:** Splice site probabilities (0-1)

**Key Attributes:**
- `.ref` - Reference transcript
- `.event` - Mutated transcript with all mutations applied
- `.splicing_results` - Full splicing prediction DataFrame

**⚠️ Important:** This class depends on seqmat's Transcript objects having:
- `.clone()` method
- `.pre_mrna.apply_mutations((pos, ref, alt))` method
- `.pre_mrna.predict_splicing(pos, engine, inplace)` method
- `.pre_mrna.predicted_splicing` attribute

---

### 3. `SpliceSimulator` (from `SpliceSimulator.py`)

Generates all viable transcript isoforms based on splice site predictions.

**Input:**
```python
from geney import SpliceSimulator

ss = SpliceSimulator(
    splicing_df=splicing_results,  # From TranscriptLibrary
    transcript=tl.event,            # Mutated transcript
    max_distance=100_000_000,       # Max intron size
    feature='event'                 # Column prefix to use
)
```

**Key Methods:**

```python
# Get summary statistics
metadata = ss.report(position)
# Returns pd.Series with:
# - 'region': 'exon', 'intron', or None
# - 'index': Region index
# - "5'_dist": Distance to 5' end
# - "3'_dist": Distance to 3' end
# - 'donor_events': JSON of altered donor sites
# - 'acceptor_events': JSON of altered acceptor sites
# - 'missplicing': Max splicing delta

# Iterate through viable isoforms
for variant_transcript, isoform_metadata in ss.get_viable_transcripts(metadata=True):
    # variant_transcript is a cloned transcript with:
    #   - .donors, .acceptors updated
    #   - .mature_mrna generated
    #   - .protein generated
    #   - .path_weight (probability)
    #   - .path_hash (unique identifier)

    # isoform_metadata is pd.Series with:
    #   - 'isoform_prevalence': Path probability
    #   - 'isoform_id': Unique hash
    #   - Plus comparison metrics to reference
    pass
```

**Output:**
- **Yields:** `(transcript, metadata)` tuples for each viable isoform
- Each transcript has `.protein` and `.mature_mrna.seq` attributes
- Ordered by path probability (highest first)

**⚠️ Important:** Requires seqmat Transcript to have:
- `.clone()` method (deep copy)
- `.generate_mature_mrna()` method
- `.generate_protein()` method
- `.donors`, `.acceptors`, `.rev`, `.transcript_start`, `.transcript_end` attributes
- `.exons`, `.introns` attributes (optional, for region detection)

---

### 4. `Oncosplice` (from `Oncosplice.py`)

Scores protein-level impact of splicing changes based on conservation.

**Input:**
```python
from geney import Oncosplice

onco = Oncosplice(
    reference_protein="MTEYK...",       # Reference protein sequence (str)
    variant_protein="MTEYKV...",        # Variant protein sequence (str)
    conservation_vector=np.array([...]) # Conservation scores (numpy array)
)
```

**Automatic Analysis:**
- Aligns reference and variant proteins
- Identifies insertions and deletions
- Calculates conservation-weighted impact score

**Key Methods:**
```python
# Get summary as pandas Series
analysis = onco.get_analysis_series()
# Returns pd.Series with:
# - 'reference_protein': Reference sequence
# - 'variant_protein': Variant sequence
# - 'reference_length': Length of reference
# - 'variant_length': Length of variant
# - 'oncosplice_score': Conservation-weighted impact score
# - 'oncosplice_percentile': Percentile of score
# - 'deletion_count': Number of deleted positions
# - 'insertion_count': Number of inserted positions
# - 'modified_positions_count': Total modified positions

# Visualize conservation and changes
onco.plot()
```

**Output:**
- **Score:** Higher scores = more impact on conserved regions
- **Percentile:** Percentile rank of the score
- **Series:** Structured analysis results

---

## Pipeline: `oncosplice_pipeline_single_transcript`

Complete workflow from mutation to oncosplice score.

### Current Implementation:

```python
from geney.pipelines import oncosplice_pipeline_single_transcript

report = oncosplice_pipeline_single_transcript(
    mut_id="KRAS:12:25227343:G:T",
    transcript_id="ENST00000311936",
    splicing_engine='spliceai',
    organism='hg38'
)
```

### Pipeline Flow:

```
1. MutationalEvent(mut_id)
   ↓ (validates and parses mutations)

2. Gene.from_file(gene, organism).transcript(id)
   ↓ (loads gene annotation)

3. TranscriptLibrary(ref_transcript, mutations)
   ↓ (applies mutations, predicts splicing)

4. SpliceSimulator(splicing_results, mutated_transcript)
   ↓ (generates viable isoforms)

5. For each isoform:
   Oncosplice(ref_protein, variant_protein, cons_vector)
   ↓ (scores conservation impact)

6. Returns DataFrame with all isoforms and scores
```

### ✅ **Design Decisions:**

1. **Central Position for Analysis:**
   - The pipeline uses `m.central_position` (mean of all mutation positions) as the focal point
   - For single mutations: this equals the mutation position
   - For compound events: this represents the density center
   - Both splicing prediction and metadata reporting use this central position
   - **Rationale:** Provides a single consistent reference point for analysis of mutation clusters

2. **Multi-mutation Handling:**
   - All mutations are applied to the transcript via `TranscriptLibrary`
   - Splicing is predicted at the central position to capture regional effects
   - Individual mutation positions are preserved in `.positions` for detailed analysis if needed

3. **Dependencies on seqmat:**
   - Requires `reference_transcript.cons_vector` - where does this come from?
   - Requires `transcript.mature_mrna.seq` - ensure seqmat provides this
   - Requires `transcript.protein` - ensure seqmat provides this

### Output Schema:

Returns `pd.DataFrame` where each row is a viable isoform with:

**Base Information:**
- `mut_id`: Original mutation ID
- `gene`: Gene name
- `transcript_id`: Transcript identifier
- `primary_transcript`: Boolean flag
- `splicing_engine`: Engine used ('spliceai' or 'pangolin')
- `central_position`: Central position of mutation event
- `mutation_count`: Number of mutations in the event
- `time_of_execution`: Timestamp

**Splice Metadata:** (from `ss.report()`)
- `region`: 'exon', 'intron', or None
- `index`: Region index
- `5'_dist`, `3'_dist`: Distances to region boundaries
- `donor_events`: JSON of altered donors
- `acceptor_events`: JSON of altered acceptors
- `missplicing`: Max splicing delta

**Isoform Metadata:** (from `ss.get_viable_transcripts()`)
- `isoform_prevalence`: Probability of this isoform
- `isoform_id`: Unique hash identifier
- Plus comparison metrics to reference

**Sequence Data:**
- `reference_mrna`: Reference mRNA sequence
- `variant_mrna`: Variant mRNA sequence

**Oncosplice Analysis:** (from `onco.get_analysis_series()`)
- `reference_protein`: Reference protein sequence
- `variant_protein`: Variant protein sequence
- `reference_length`, `variant_length`: Sequence lengths
- `oncosplice_score`: Conservation impact score
- `oncosplice_percentile`: Score percentile
- `deletion_count`, `insertion_count`: Change counts
- `modified_positions_count`: Total modifications

---

## Requirements

### Core Dependencies:
- `numpy` - Numerical operations
- `pandas` - Data manipulation
- `biopython` - Sequence alignment
- `matplotlib`, `seaborn` - Visualization
- `tensorflow`, `keras` - SpliceAI models
- `torch` - Pangolin models
- `joblib` - Model persistence
- **`seqmat`** - Gene/Transcript handling (external)
- **`pangolin`** - Splicing prediction (optional)

### Conda-only:
```bash
conda install -c bioconda spliceai
```

---

## Example Usage

```python
from geney.variants import MutationalEvent
from geney.pipelines import oncosplice_pipeline_single_transcript

# Analyze a single mutation
report_df = oncosplice_pipeline_single_transcript(
    mut_id="KRAS:12:25227343:G:T",
    transcript_id="ENST00000311936",
    splicing_engine='spliceai',
    organism='hg38'
)

# View top isoforms by prevalence
print(report_df.sort_values('isoform_prevalence', ascending=False).head())

# Find isoforms with high oncosplice scores
high_impact = report_df[report_df['oncosplice_score'] > 0.8]
```

---

## Notes & Caveats

1. **Multi-mutation events:** The pipeline may not correctly handle compound mutations. Review lines 20 and 30 in `pipelines.py`.

2. **seqmat dependency:** This library heavily depends on seqmat's Gene and Transcript classes. Ensure seqmat provides all required methods and attributes.

3. **Conservation vectors:** The source of conservation scores (`cons_vector`) must be documented in seqmat.

4. **Memory usage:** Generating all viable isoforms can be memory-intensive for genes with many splice sites.

5. **Splicing engines:**
   - `'spliceai'` - Requires conda installation
   - `'pangolin'` - Alternative engine
   - `'spliceai-pytorch'` - Deprecated (raises error)

---

## Contributing

When modifying the pipeline:
1. Ensure compatibility with `MutationalEvent` iteration format
2. Test with both single and multi-mutation events
3. Verify seqmat integration points
4. Update this README with any changes to output schemas
