"""
Xcedl Image Detection Library

A comprehensive Python library for advanced image fingerprinting and similarity detection,
utilizing perceptual hashing algorithms and multi-signal verification techniques optimized
for content moderation and duplicate detection applications.

This package provides production-ready components for:
- Robust image fingerprint generation with compression simulation
- Multi-modal similarity verification using perceptual hashes
- Efficient database matching with optimized lookup strategies
- Configurable threshold parameters for accuracy tuning

Version: 0.1.1
"""

from .fingerprint import MilitaryGradeFingerprinter, verify_multisignal, find_matching_scam

__version__ = "0.1.1"
__all__ = ["MilitaryGradeFingerprinter", "verify_multisignal", "find_matching_scam"]