# VibeDNA Agent Skills
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Skill definitions for VibeDNA agents.

Skills are comprehensive capability bundles that agents can use
to perform complex operations.
"""

from vibedna.agents.skills.encoding_skill import EncodingSkill
from vibedna.agents.skills.error_correction_skill import ErrorCorrectionSkill

__all__ = [
    "EncodingSkill",
    "ErrorCorrectionSkill",
]
