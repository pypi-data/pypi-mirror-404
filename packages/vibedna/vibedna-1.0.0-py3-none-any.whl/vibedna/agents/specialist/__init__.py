# VibeDNA Specialist Tier
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Specialist Tier agents for VibeDNA.

This tier handles domain-specific task execution:
- Encoder Agent: Binary to DNA encoding
- Decoder Agent: DNA to binary decoding
- Error Correction Agent: Reed-Solomon error correction
- Compute Agent: DNA-native computation
- FileSystem Agent: DNA-based file management
- Validation Agent: Sequence validation
- Visualization Agent: Sequence visualization
- Synthesis Agent: DNA synthesis optimization
"""

from vibedna.agents.specialist.encoder_agent import EncoderAgent
from vibedna.agents.specialist.decoder_agent import DecoderAgent
from vibedna.agents.specialist.error_correction_agent import ErrorCorrectionAgent
from vibedna.agents.specialist.compute_agent import ComputeAgent
from vibedna.agents.specialist.filesystem_agent import FileSystemAgent
from vibedna.agents.specialist.validation_agent import ValidationAgent
from vibedna.agents.specialist.visualization_agent import VisualizationAgent
from vibedna.agents.specialist.synthesis_agent import SynthesisAgent

__all__ = [
    "EncoderAgent",
    "DecoderAgent",
    "ErrorCorrectionAgent",
    "ComputeAgent",
    "FileSystemAgent",
    "ValidationAgent",
    "VisualizationAgent",
    "SynthesisAgent",
]
