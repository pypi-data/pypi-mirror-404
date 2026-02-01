# SoulEyez Detection Validation
# Correlates attacks with SIEM detections

from .attack_signatures import ATTACK_SIGNATURES
from .validator import DetectionValidator

__all__ = ["DetectionValidator", "ATTACK_SIGNATURES"]
