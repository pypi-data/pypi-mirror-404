import re
import pandas as pd
import numpy as np
from Bio import pairwise2
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import seaborn as sns  # Optional: uncomment if you wish to set a seaborn theme

class Oncosplice:
    def __init__(self, reference_protein: str, variant_protein: str, conservation_vector: np.ndarray,
                 window_length: int = 13):
        """
        Initializes the Oncosplice analysis with protein sequences and conservation data.

        Args:
            reference_protein (str): Reference protein sequence.
            variant_protein (str): Variant protein sequence.
            conservation_vector (np.ndarray): 1D array of conservation scores for the reference protein.
            window_length (int, optional): Window length for smoothing calculations. Defaults to 13.
        """
        self.reference_protein = reference_protein
        self.variant_protein = variant_protein
        self.conservation_vector = self.transform_conservation_vector(
                        conservation_vector, window=window_length)
        self.window_length = window_length

        # These will be calculated in run_analysis()
        self.alignment = None
        self.deletions = None
        self.insertions = None
        self.modified_positions = None
        self.smoothed_conservation = None
        self.score = None
        self.percentile = None

        self.run_analysis()

    def run_analysis(self) -> None:
        """
        Runs the alignment and conservation analysis.
        """
        self.alignment = self.get_logical_alignment(self.reference_protein, self.variant_protein)
        self.deletions, self.insertions = self.find_indels_with_mismatches_as_deletions(self.alignment.seqA,
                                                                                        self.alignment.seqB)
        self.modified_positions = self.find_modified_positions(len(self.reference_protein), self.deletions,
                                                               self.insertions)
        self.smoothed_conservation = np.convolve(self.conservation_vector * self.modified_positions,
                                                 np.ones(self.window_length), mode='same') / self.window_length

        sorted_cons = sorted(self.conservation_vector)
        max_temp_cons = max(self.smoothed_conservation)
        self.percentile = sorted_cons.index(next(x for x in sorted_cons if x >= max_temp_cons)) / len(
            self.conservation_vector)
        self.score = max_temp_cons

    @staticmethod
    def find_continuous_gaps(sequence: str) -> list[tuple[int, int]]:
        """
        Finds continuous gap sequences in an alignment.
        """
        return [(m.start(), m.end()) for m in re.finditer(r'-+', sequence)]

    @staticmethod
    def build_position_mapper(sequence: str) -> dict[int, int]:
        """
        Creates a mapping from each alignment index to its corresponding position in the ungapped sequence.
        """
        mapper = {}
        counter = 0
        for i, char in enumerate(sequence):
            if char != '-':
                counter += 1
            mapper[i] = counter
        return mapper

    def get_logical_alignment(self, ref_prot: str, var_prot: str):
        """
        Aligns two protein sequences and returns the alignment with the minimal gap sum.
        If the variant is empty, uses the first character of the reference.

        Returns:
            Alignment object (with attributes seqA and seqB) from pairwise2.
        """
        if var_prot == '':
            print("Variant protein is empty; using first character of reference as heuristic...")
            var_prot = ref_prot[0]

        alignments = pairwise2.align.globalms(ref_prot, var_prot, 1, -1, -3, 0, penalize_end_gaps=(True, True))
        if not alignments:
            print("No alignment found for:", ref_prot, var_prot)

        if len(alignments) > 1:
            gap_lengths = [sum(
                end - start for start, end in (self.find_continuous_gaps(al.seqA) + self.find_continuous_gaps(al.seqB)))
                           for al in alignments]
            optimal_alignment = alignments[gap_lengths.index(min(gap_lengths))]
        else:
            optimal_alignment = alignments[0]

        return optimal_alignment

    def find_indels_with_mismatches_as_deletions(self, seqA: str, seqB: str) -> tuple[dict[int, str], dict[int, str]]:
        """
        Identifies insertions and deletions in aligned sequences, treating mismatches as deletions.

        Returns:
            tuple: (deletions, insertions) dictionaries.
        """
        if len(seqA) != len(seqB):
            raise ValueError("Sequences must be of the same length")

        mapperA = self.build_position_mapper(seqA)
        mapperB = self.build_position_mapper(seqB)
        seqA_array = np.array(list(seqA))
        seqB_array = np.array(list(seqB))

        # Mark mismatches (where neither is a gap) as gaps in seqB.
        mismatches = (seqA_array != seqB_array) & (seqA_array != '-') & (seqB_array != '-')
        seqB_array[mismatches] = '-'
        modified_seqB = ''.join(seqB_array)

        gaps_in_A = self.find_continuous_gaps(seqA)
        gaps_in_B = self.find_continuous_gaps(modified_seqB)

        insertions = {
            mapperB[start]: modified_seqB[start:end].replace('-', '')
            for start, end in gaps_in_A if seqB[start:end].strip('-')
        }
        deletions = {
            mapperA[start]: seqA[start:end].replace('-', '')
            for start, end in gaps_in_B if seqA[start:end].strip('-')
        }
        return deletions, insertions

    @staticmethod
    def parabolic_window(window_size: int) -> np.ndarray:
        """
        Creates a parabolic window function with a peak at the center.
        """
        x = np.linspace(-1, 1, window_size)
        return 0.9 * (1 - x ** 2) + 0.1

    @staticmethod
    def transform_conservation_vector(conservation_vector: np.ndarray, window: int = 13,
                                      factor: float = 4) -> np.ndarray:
        """
        Transforms a 1D conservation vector using a parabolic window and exponential scaling.
        """
        conv_window = Oncosplice.parabolic_window(window)
        transformed_vector = np.convolve(conservation_vector, conv_window, mode='same') / np.sum(conv_window)
        assert len(transformed_vector) == len(
            conservation_vector), "Length mismatch in transformed conservation vector."
        return np.exp(-transformed_vector * factor)

    @staticmethod
    def find_modified_positions(sequence_length: int, deletions: dict[int, str], insertions: dict[int, str],
                                reach_limit: int = 16) -> np.ndarray:
        """
        Marks sequence positions as modified if they lie within a deletion or near an insertion.
        """
        modified = np.zeros(sequence_length, dtype=float)
        for pos, deletion in deletions.items():
            deletion_length = len(deletion)
            modified[pos:pos + deletion_length] = 1

        for pos, insertion in insertions.items():
            reach = min(len(insertion) // 2, reach_limit)
            start = max(0, pos - reach)
            end = min(sequence_length, pos + reach)
            modified[start:end] = 1

        return modified

    @staticmethod
    def moving_average_conv(vector: np.ndarray, window_size: int, factor: float = 1) -> np.ndarray:
        """
        Computes the moving average convolution of a vector.
        """
        if not isinstance(vector, (list, tuple, np.ndarray)):
            raise TypeError("Input vector must be a list, tuple, or numpy array.")
        if not isinstance(window_size, int) or window_size <= 0:
            raise ValueError("window_size must be a positive integer.")
        if len(vector) < window_size:
            raise ValueError("window_size must not exceed the length of the vector.")
        if factor == 0:
            raise ValueError("factor must be non-zero.")
        return np.convolve(vector, np.ones(window_size), mode='same') / window_size

    @staticmethod
    def calculate_penalty(domains: dict[int, str], cons_scores: np.ndarray, window: int,
                          is_insertion: bool = False) -> np.ndarray:
        """
        Calculates a penalty for mutations based on conservation scores.
        """
        penalty = np.zeros(len(cons_scores))
        for pos, seq in domains.items():
            mutation_length = len(seq)
            weight = max(1.0, mutation_length / window)
            if is_insertion:
                reach = min(window // 2, mutation_length // 2)
                penalty[pos - reach:pos + reach] = weight * cons_scores[pos - reach:pos + reach]
            else:
                penalty[pos:pos + mutation_length] = weight * cons_scores[pos:pos + mutation_length]
        return penalty

    def oncosplice_score(self) -> tuple[float, float]:
        """
        Returns the computed Oncosplice score and its percentile.
        """
        return self.score, self.percentile

    # ----------------- Visualization Methods -----------------

    def plot_alignment(self) -> None:
        """
        Visualizes the alignment of reference and variant protein sequences.
        Differences (mismatches or gaps) are marked in red.
        """
        aligned_ref = self.alignment.seqA
        aligned_var = self.alignment.seqB
        n = len(aligned_ref)

        fig, ax = plt.subplots(figsize=(max(12, n * 0.5), 3))
        ax.axis("off")

        x_start, x_end = 0.01, 0.99
        char_step = (x_end - x_start) / n
        y_ref, y_var = 0.65, 0.35

        ax.text(0.0, y_ref, "Reference:", fontsize=12, fontfamily="monospace", ha="right", va="center")
        ax.text(0.0, y_var, "Variant:  ", fontsize=12, fontfamily="monospace", ha="right", va="center")

        for i in range(n):
            x = x_start + i * char_step
            char_ref = aligned_ref[i]
            char_var = aligned_var[i]
            color = "black" if char_ref == char_var else "red"
            ax.text(x, y_ref, char_ref, fontsize=12, fontfamily="monospace",
                    ha="center", va="center", color=color)
            ax.text(x, y_var, char_var, fontsize=12, fontfamily="monospace",
                    ha="center", va="center", color=color)

        plt.title("Protein Sequence Alignment (differences in red)")
        plt.show()

    def plot_indels(self) -> None:
        """
        Visualizes the positions of insertions and deletions along the reference protein.
        """
        positions = np.arange(len(self.reference_protein))
        indel_signal = np.zeros(len(self.reference_protein))
        for pos, deletion in self.deletions.items():
            indel_signal[pos:pos + len(deletion)] = 1
        for pos, insertion in self.insertions.items():
            reach = min(len(insertion) // 2, 16)
            start = max(0, pos - reach)
            end = min(len(self.reference_protein), pos + reach)
            indel_signal[start:end] = 2

        plt.figure(figsize=(10, 2))
        plt.step(positions, indel_signal, where="post", marker="o")
        plt.xlabel("Position")
        plt.ylabel("Indel Signal\n(1 = Deletion, 2 = Insertion)")
        plt.title("Insertions and Deletions Along Protein")
        plt.ylim(-0.5, 2.5)
        plt.show()

    def plot_combined_analysis(self, gene: str = '', domain_annotations: list[tuple[int, int, str]] = None) -> None:
        """
        Creates a comprehensive plot that shows:
          - Two conservation curves computed at different resolutions (using different window sizes).
          - Normalized Rate4Site–like scores (plotted on a twin y-axis).
          - Vertical markers for mutation events: deletions (red), insertions (blue), and missense mutations (magenta).
          - Protein domain annotations (if provided) in a separate axis above the main plot.

        Args:
            gene (str): Gene name for the x-axis label.
            domain_annotations (list of tuples): Each tuple is (start, end, label) for a protein domain.
        """
        # Optionally, you may set a seaborn style:
        # sns.set_theme(style="white")

        fig, ax = plt.subplots(figsize=(15, 5))
        ax.set_xlabel(f'AA Position - {gene}', weight='bold')
        ax.set_xlim(0, len(self.conservation_vector))
        ax.set_ylim(0, 1.2)
        ax.set_ylabel('Relative Importance', weight='bold')
        ax.tick_params(axis='y')
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Compute conservation vectors at two resolutions.
        cons_low = Oncosplice.transform_conservation_vector(self.conservation_vector, window=76)
        cons_high = Oncosplice.transform_conservation_vector(self.conservation_vector, window=6)
        # Normalize the vectors.
        cons_low = cons_low / np.max(cons_low)
        cons_high = cons_high / np.max(cons_high)
        positions = np.arange(len(self.conservation_vector))

        ax.plot(positions, cons_low, c='blue', label='Estimated Functional Residues (low-res)')
        ax.plot(positions, cons_high, c='black', label='Estimated Functional Domains (high-res)')

        # Plot Rate4Site–like scores on a twin y‑axis.
        ax2 = ax.twinx()
        c = np.array(self.conservation_vector)
        c = c + abs(min(c))
        c = c / np.max(c)
        ax2.scatter(positions, c, color='green', label='Rate4Site Scores', alpha=0.4)
        ax2.set_ylabel('Rate4Site Normalized', color='green', weight='bold')
        ax2.tick_params(axis='y', labelcolor='green')
        ax2.spines['right'].set_visible(True)
        ax2.spines['top'].set_visible(False)

        # Compute mutation event positions from the alignment.
        ref_seq = self.alignment.seqA
        var_seq = self.alignment.seqB
        mapper = Oncosplice.build_position_mapper(ref_seq)
        deletion_positions = []
        insertion_positions = []
        missense_positions = []

        for i in range(len(ref_seq)):
            r = ref_seq[i]
            v = var_seq[i]
            if r != '-' and v == '-':
                deletion_positions.append(mapper[i])
            elif r == '-' and v != '-':
                pos = mapper[i - 1] if i > 0 else 0
                insertion_positions.append(pos)
            elif r != '-' and v != '-' and r != v:
                missense_positions.append(mapper[i])

        deletion_positions = sorted(set(deletion_positions))
        insertion_positions = sorted(set(insertion_positions))
        missense_positions = sorted(set(missense_positions))

        # Add vertical markers for the mutation events.
        for pos in deletion_positions:
            ax.axvline(x=pos, color='red', linestyle='--', alpha=0.7,
                       label='Deletion' if pos == deletion_positions[0] else "")
        for pos in insertion_positions:
            ax.axvline(x=pos, color='blue', linestyle='--', alpha=0.7,
                       label='Insertion' if pos == insertion_positions[0] else "")
        for pos in missense_positions:
            ax.axvline(x=pos, color='magenta', linestyle='--', alpha=0.7,
                       label='Missense' if pos == missense_positions[0] else "")

        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')

        # If domain annotations are provided, create a small axes above for the domains.
        if domain_annotations is not None:
            domain_ax = fig.add_axes([0.125, 0.9, 0.775, 0.06])
            domain_ax.set_xlim(0, len(self.conservation_vector))
            domain_ax.set_xticks([])
            domain_ax.set_yticks([])
            for spine in domain_ax.spines.values():
                spine.set_visible(False)
            # Draw a base rectangle for the entire protein.
            domain_ax.add_patch(Rectangle((0, 0), len(self.conservation_vector), 0.9,
                                          facecolor='lightgray', edgecolor='none'))
            for domain in domain_annotations:
                start, end, label = domain
                domain_ax.add_patch(Rectangle((start, 0), end - start, 0.9,
                                              facecolor='orange', edgecolor='none', alpha=0.5))
                domain_ax.text((start + end) / 2, 1.2, label, ha='center', va='center', color='black', size=8)

        plt.title("Combined Conservation and Mutation Analysis")
        plt.show()

    def get_analysis_series(self) -> pd.Series:
        """
        Returns a pandas Series summarizing the Oncosplice analysis.

        The output includes:
          - The reference protein sequence,
          - The variant protein sequence,
          - Their respective lengths,
          - The alignment length,
          - The computed Oncosplice score,
          - The percentile,
          - Counts of deletions and insertions,
          - The total count of modified positions.

        Returns:
            pd.Series: A series containing the summary of the analysis.
        """
        analysis_dict = {
            'reference_protein': self.reference_protein,
            'variant_protein': self.variant_protein,
            'aligned_reference_protein': self.alignment.seqA,
            'aligned_variant_protein': self.alignment.seqB,
            'reference_length': len(self.reference_protein),
            'variant_length': len(self.variant_protein),
            'oncosplice_score': self.score,
            'percentile': self.percentile,
            'number_of_deletions': len(self.deletions),
            'number_of_insertions': len(self.insertions),
            'modified_positions_count': int(np.sum(self.modified_positions))
        }
        return pd.Series(analysis_dict)




if __name__ == "__main__":
    ref_seq = "MKTAYIAKQRQISFVKSHFSRQDILDLIYQY"
    var_seq = "MKTAYIAKQ--ISFVKSHFSRQD"
    cons_vector = np.random.rand(len(ref_seq))
    oncosplice = Oncosplice(ref_seq, var_seq, cons_vector)
    print(oncosplice.get_analysis_series()) 
    