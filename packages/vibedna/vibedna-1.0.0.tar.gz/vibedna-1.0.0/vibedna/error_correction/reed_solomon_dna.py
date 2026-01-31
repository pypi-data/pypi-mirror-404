"""
VibeDNA Reed-Solomon Error Correction for DNA

Implements Reed-Solomon error correction optimized for DNA sequences,
operating in GF(4) (Galois Field with 4 elements) to match the
4 nucleotide bases.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass

from vibedna.utils.constants import NUCLEOTIDE_VALUE, VALUE_NUCLEOTIDE


@dataclass
class CorrectionResult:
    """Result of error correction operation."""
    corrected_sequence: str
    errors_detected: int
    errors_corrected: int
    uncorrectable: bool
    error_positions: List[int]
    confidence: float  # 0.0 to 1.0


class GF4:
    """
    Galois Field GF(4) arithmetic for DNA.

    GF(4) = {0, 1, α, α+1} where α² = α + 1
    Mapped to nucleotides: A=0, T=1, C=α, G=α+1

    This provides the mathematical foundation for Reed-Solomon
    error correction on DNA sequences.
    """

    # Addition table for GF(4) (XOR-like operation)
    # GF(4) addition: a + b = a XOR b (for elements 0,1,2,3)
    ADD_TABLE = [
        [0, 1, 2, 3],
        [1, 0, 3, 2],
        [2, 3, 0, 1],
        [3, 2, 1, 0],
    ]

    # Multiplication table for GF(4)
    # Using primitive polynomial p(x) = x² + x + 1
    MUL_TABLE = [
        [0, 0, 0, 0],
        [0, 1, 2, 3],
        [0, 2, 3, 1],
        [0, 3, 1, 2],
    ]

    # Multiplicative inverse table
    INV_TABLE = [0, 1, 3, 2]  # inv(0) undefined, inv(1)=1, inv(2)=3, inv(3)=2

    # Power table: α^n for n = 0,1,2,...
    POW_TABLE = [1, 2, 3, 1, 2, 3]  # Cycles with period 3

    # Log table: log_α(n) for n = 1,2,3
    LOG_TABLE = [None, 0, 1, 2]  # log(0) undefined

    @classmethod
    def add(cls, a: int, b: int) -> int:
        """Add two GF(4) elements."""
        return cls.ADD_TABLE[a][b]

    @classmethod
    def sub(cls, a: int, b: int) -> int:
        """Subtract two GF(4) elements (same as add in GF(4))."""
        return cls.add(a, b)

    @classmethod
    def mul(cls, a: int, b: int) -> int:
        """Multiply two GF(4) elements."""
        return cls.MUL_TABLE[a][b]

    @classmethod
    def div(cls, a: int, b: int) -> int:
        """Divide two GF(4) elements."""
        if b == 0:
            raise ZeroDivisionError("Division by zero in GF(4)")
        return cls.mul(a, cls.INV_TABLE[b])

    @classmethod
    def pow(cls, a: int, n: int) -> int:
        """Raise GF(4) element to power n."""
        if a == 0:
            return 0 if n > 0 else 1
        if n == 0:
            return 1
        # Use repeated multiplication
        result = 1
        base = a
        n = n % 3  # Period is 3 for non-zero elements
        for _ in range(n):
            result = cls.mul(result, base)
        return result

    @classmethod
    def eval_poly(cls, coeffs: List[int], x: int) -> int:
        """Evaluate polynomial at x."""
        result = 0
        for coeff in coeffs:
            result = cls.add(cls.mul(result, x), coeff)
        return result


class DNAReedSolomon:
    """
    Reed-Solomon error correction adapted for DNA sequences.

    Standard RS operates on bytes (GF(2^8)), but DNA naturally
    operates in GF(4). This implementation uses GF(4) directly
    for efficient error correction.

    Capabilities:
    - Detect up to 2t errors
    - Correct up to t errors
    - Default t=8 provides correction of up to 8 nucleotide errors
      per block with 16 parity nucleotides overhead

    Example:
        >>> rs = DNAReedSolomon(nsym=16)
        >>> encoded = rs.encode("ATCGATCG")
        >>> # Introduce an error
        >>> corrupted = "ATCGATCG"[0] + "A" + encoded[2:]
        >>> result = rs.decode(corrupted)
        >>> print(result.corrected_sequence)
        ATCGATCG...
    """

    def __init__(self, nsym: int = 16):
        """
        Initialize Reed-Solomon codec.

        Args:
            nsym: Number of parity symbols (nucleotides).
                  Can correct up to nsym/2 errors.
        """
        self.nsym = nsym
        self.t = nsym // 2  # Error correction capability
        self._generator = self._compute_generator_poly()

    def _compute_generator_poly(self) -> List[int]:
        """
        Compute the generator polynomial.

        g(x) = (x - α^0)(x - α^1)...(x - α^(nsym-1))
        """
        g = [1]

        for i in range(self.nsym):
            # Multiply by (x - α^i) = (x + α^i) in GF(4)
            alpha_i = GF4.pow(2, i)  # α = 2 in our representation
            new_g = [0] * (len(g) + 1)

            for j, coeff in enumerate(g):
                new_g[j] = GF4.add(new_g[j], coeff)
                new_g[j + 1] = GF4.add(new_g[j + 1], GF4.mul(coeff, alpha_i))

            g = new_g

        return g

    def encode(self, sequence: str) -> str:
        """
        Add Reed-Solomon parity to DNA sequence.

        Args:
            sequence: Original DNA sequence

        Returns:
            Sequence with RS parity appended
        """
        # Convert DNA to GF(4) elements
        data = [NUCLEOTIDE_VALUE[n] for n in sequence.upper()]

        # Compute parity (remainder of data * x^nsym / generator)
        # Shift data by nsym positions
        shifted = data + [0] * self.nsym

        # Polynomial division
        for i in range(len(data)):
            coeff = shifted[i]
            if coeff != 0:
                for j, gen_coeff in enumerate(self._generator):
                    shifted[i + j] = GF4.sub(shifted[i + j], GF4.mul(coeff, gen_coeff))

        # Parity is the remainder (last nsym elements)
        parity = shifted[-self.nsym:]

        # Append parity to original data
        encoded_values = data + parity

        # Convert back to DNA
        return "".join(VALUE_NUCLEOTIDE[v] for v in encoded_values)

    def decode(self, sequence: str) -> CorrectionResult:
        """
        Decode and correct errors in DNA sequence.

        Args:
            sequence: DNA sequence with RS parity

        Returns:
            CorrectionResult with corrected sequence and stats
        """
        # Convert DNA to GF(4) elements
        received = [NUCLEOTIDE_VALUE[n] for n in sequence.upper()]

        # Compute syndromes
        syndromes = self._compute_syndromes(received)

        # Check if all syndromes are zero (no errors)
        if all(s == 0 for s in syndromes):
            return CorrectionResult(
                corrected_sequence=sequence,
                errors_detected=0,
                errors_corrected=0,
                uncorrectable=False,
                error_positions=[],
                confidence=1.0,
            )

        # Find error locator polynomial using Berlekamp-Massey
        error_locator = self._berlekamp_massey(syndromes)

        # Find error positions using Chien search
        error_positions = self._chien_search(error_locator, len(received))

        if error_positions is None or len(error_positions) > self.t:
            # Too many errors to correct
            return CorrectionResult(
                corrected_sequence=sequence,
                errors_detected=len(error_positions) if error_positions else self.nsym,
                errors_corrected=0,
                uncorrectable=True,
                error_positions=error_positions or [],
                confidence=0.0,
            )

        # Compute error values using Forney algorithm
        error_values = self._forney_algorithm(
            syndromes, error_locator, error_positions, len(received)
        )

        # Correct errors
        corrected = received.copy()
        for pos, val in zip(error_positions, error_values):
            corrected[pos] = GF4.sub(corrected[pos], val)

        # Convert back to DNA (without parity)
        corrected_data = corrected[:-self.nsym]
        corrected_sequence = "".join(VALUE_NUCLEOTIDE[v] for v in corrected_data)

        return CorrectionResult(
            corrected_sequence=corrected_sequence,
            errors_detected=len(error_positions),
            errors_corrected=len(error_positions),
            uncorrectable=False,
            error_positions=error_positions,
            confidence=1.0 - (len(error_positions) / self.t),
        )

    def _compute_syndromes(self, received: List[int]) -> List[int]:
        """Compute error syndromes S_i = r(α^i)."""
        syndromes = []
        for i in range(self.nsym):
            alpha_i = GF4.pow(2, i)
            s = GF4.eval_poly(received, alpha_i)
            syndromes.append(s)
        return syndromes

    def _berlekamp_massey(self, syndromes: List[int]) -> List[int]:
        """
        Find error locator polynomial using Berlekamp-Massey algorithm.

        Returns coefficients of Λ(x) = 1 + Λ_1*x + Λ_2*x² + ...
        """
        n = len(syndromes)

        # Initialize
        C = [1] + [0] * n  # Current polynomial
        B = [1] + [0] * n  # Previous polynomial
        L = 0  # Current length
        m = 1  # Shift counter
        b = 1  # Previous discrepancy

        for r in range(n):
            # Compute discrepancy
            d = syndromes[r]
            for i in range(1, L + 1):
                if i < len(C) and r - i >= 0:
                    d = GF4.add(d, GF4.mul(C[i], syndromes[r - i]))

            if d == 0:
                m += 1
            elif 2 * L <= r:
                T = C.copy()
                coeff = GF4.div(d, b)
                for i in range(len(B)):
                    if i + m < len(C):
                        C[i + m] = GF4.sub(C[i + m], GF4.mul(coeff, B[i]))
                L = r + 1 - L
                B = T
                b = d
                m = 1
            else:
                coeff = GF4.div(d, b)
                for i in range(len(B)):
                    if i + m < len(C):
                        C[i + m] = GF4.sub(C[i + m], GF4.mul(coeff, B[i]))
                m += 1

        # Return polynomial up to degree L
        return C[:L + 1]

    def _chien_search(
        self, error_locator: List[int], n: int
    ) -> Optional[List[int]]:
        """
        Find error positions using Chien search.

        Evaluates Λ(α^(-i)) for all positions i.
        """
        positions = []

        for i in range(n):
            # Evaluate Λ(α^(-i))
            x = GF4.pow(2, (3 - i) % 3)  # α^(-i) in GF(4), period 3
            val = GF4.eval_poly(error_locator, x)

            if val == 0:
                positions.append(i)

        # Verify we found the expected number of errors
        if len(positions) != len(error_locator) - 1:
            return None

        return positions

    def _forney_algorithm(
        self,
        syndromes: List[int],
        error_locator: List[int],
        positions: List[int],
        n: int,
    ) -> List[int]:
        """
        Compute error values using Forney algorithm.
        """
        # Compute error evaluator polynomial Ω(x)
        # Ω(x) = S(x) * Λ(x) mod x^nsym
        omega = [0] * self.nsym
        for i in range(min(len(syndromes), self.nsym)):
            for j in range(min(len(error_locator), self.nsym - i)):
                if i + j < self.nsym:
                    omega[i + j] = GF4.add(
                        omega[i + j],
                        GF4.mul(syndromes[i], error_locator[j])
                    )

        # Compute formal derivative of error locator Λ'(x)
        # In GF(4), derivative of a*x^n is n*a*x^(n-1), where n is mod 2
        lambda_prime = [0] * len(error_locator)
        for i in range(1, len(error_locator)):
            if i % 2 == 1:  # Odd powers only (coefficient becomes 1)
                lambda_prime[i - 1] = error_locator[i]

        # Compute error values
        error_values = []
        for pos in positions:
            x_inv = GF4.pow(2, pos % 3)  # α^i

            # Evaluate Ω(x_inv)
            omega_val = GF4.eval_poly(omega, x_inv)

            # Evaluate Λ'(x_inv)
            lambda_prime_val = GF4.eval_poly(lambda_prime, x_inv)

            if lambda_prime_val == 0:
                error_values.append(0)
            else:
                error_values.append(GF4.div(omega_val, lambda_prime_val))

        return error_values


class DNAMutationModel:
    """
    Models biological mutation patterns for better error correction.

    DNA has specific mutation patterns:
    - Transitions (A↔G, T↔C) more common than transversions
    - Insertions/deletions in homopolymer regions
    - UV damage patterns (thymine dimers)
    """

    # Mutation probability matrix (simplified)
    # Rows: original, Columns: mutated-to
    # Indices: A=0, T=1, C=2, G=3
    MUTATION_MATRIX = [
        [0.95, 0.01, 0.01, 0.03],  # A: mostly stays A, transitions to G
        [0.01, 0.95, 0.03, 0.01],  # T: mostly stays T, transitions to C
        [0.01, 0.03, 0.95, 0.01],  # C: mostly stays C, transitions to T
        [0.03, 0.01, 0.01, 0.95],  # G: mostly stays G, transitions to A
    ]

    NUCLEOTIDES = ["A", "T", "C", "G"]

    @classmethod
    def estimate_original(cls, mutated: str, position: int) -> str:
        """
        Estimate most likely original nucleotide.

        Uses mutation probabilities to guess the original
        nucleotide given a potentially mutated one.
        """
        mutated_idx = NUCLEOTIDE_VALUE[mutated.upper()]

        # Find the nucleotide most likely to mutate TO this one
        best_original = mutated_idx
        best_prob = 0

        for orig_idx in range(4):
            prob = cls.MUTATION_MATRIX[orig_idx][mutated_idx]
            if prob > best_prob and orig_idx != mutated_idx:
                best_prob = prob
                best_original = orig_idx

        # If staying the same is most likely, return as-is
        if cls.MUTATION_MATRIX[mutated_idx][mutated_idx] > best_prob:
            return mutated.upper()

        return cls.NUCLEOTIDES[best_original]

    @classmethod
    def get_mutation_probability(cls, original: str, mutated: str) -> float:
        """Get probability of specific mutation."""
        orig_idx = NUCLEOTIDE_VALUE[original.upper()]
        mut_idx = NUCLEOTIDE_VALUE[mutated.upper()]
        return cls.MUTATION_MATRIX[orig_idx][mut_idx]

    @classmethod
    def is_transition(cls, original: str, mutated: str) -> bool:
        """Check if mutation is a transition (A↔G or T↔C)."""
        orig = original.upper()
        mut = mutated.upper()

        transitions = {("A", "G"), ("G", "A"), ("T", "C"), ("C", "T")}
        return (orig, mut) in transitions

    @classmethod
    def is_transversion(cls, original: str, mutated: str) -> bool:
        """Check if mutation is a transversion."""
        if original.upper() == mutated.upper():
            return False
        return not cls.is_transition(original, mutated)


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
