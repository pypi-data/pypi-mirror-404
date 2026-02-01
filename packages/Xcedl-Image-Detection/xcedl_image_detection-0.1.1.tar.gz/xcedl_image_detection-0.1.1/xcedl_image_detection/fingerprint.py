"""
Image Fingerprinting Module

This module implements advanced image fingerprinting techniques utilizing perceptual hashing
algorithms and multi-signal verification for robust image similarity detection and analysis.
"""

import io
import logging
from typing import Dict, List, Optional, Tuple, Any

import imagehash
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class MilitaryGradeFingerprinter:
    """
    High-precision image fingerprinting system designed to simulate Discord's image
    compression pipeline, generating perceptual hashes resilient to common image manipulations.

    The fingerprinting pipeline consists of:
    1. Dual JPEG compression simulation at 85% quality
    2. Multiple perceptual hash generation (phash, whash, dhash)
    3. Color histogram analysis with 24-bin quantization
    """

    @staticmethod
    def nuclear_normalize(img: Image.Image) -> Tuple[Image.Image, bytes, float, float]:
        """
        Normalize input image through a simulated Discord compression pipeline.

        Applies dual JPEG compression cycles at 85% quality followed by resizing to 512x512
        pixels to ensure canonical representation matching Discord's image processing.

        Args:
            img: Input PIL Image object in any supported format

        Returns:
            Tuple containing:
            - Normalized PIL Image in RGB format
            - Sorted pixel byte sequence for statistical analysis
            - Mean pixel intensity value
            - Pixel intensity standard deviation
        """
        # Execute first compression cycle
        buffer = io.BytesIO()
        img.convert('RGB').save(buffer, 'JPEG', quality=85, optimize=True)
        current = Image.open(buffer).convert('RGB')

        # Execute second compression cycle
        buffer = io.BytesIO()
        current.save(buffer, 'JPEG', quality=85, optimize=True)
        final_img = Image.open(buffer).convert('RGB').resize((512, 512), Image.Resampling.LANCZOS)

        # Perform statistical analysis of pixel distribution
        pixels = np.array(final_img, dtype=np.uint8)
        flat_pixels = pixels.flatten()
        sorted_pixels = np.sort(flat_pixels).tobytes()
        mean_intensity = float(np.mean(flat_pixels))
        pixel_std = float(np.std(flat_pixels))

        return final_img, sorted_pixels, mean_intensity, pixel_std

    @staticmethod
    def generate_nuclear_fingerprint(img: Image.Image) -> Dict[str, Any]:
        """
        Generate comprehensive image fingerprint dictionary containing multiple perceptual signatures.

        Computes perceptual hashes and color histogram to create a robust multi-dimensional
        representation optimized for similarity comparison and duplicate detection.

        Args:
            img: Input PIL Image object

        Returns:
            Dictionary containing fingerprint components:
            - 'phash': 16x16 perceptual hash string
            - 'whash': Wavelet hash string
            - 'dhash': Difference hash string
            - 'color_hist': Normalized 24-bin color histogram (8 bins per RGB channel)
            - 'master': Primary hash for optimized database lookups
        """
        canonical_img, _, _, _ = MilitaryGradeFingerprinter.nuclear_normalize(img)

        # Generate perceptual hash suite
        ph = imagehash.phash(canonical_img, hash_size=16)
        wh = imagehash.whash(canonical_img)
        dh = imagehash.dhash(canonical_img)

        # Compute quantized color histogram: 8 bins per RGB channel
        arr = np.array(canonical_img)
        hist_bins = 8
        chans = []
        for c in range(3):  # RGB color channels
            h, _ = np.histogram(arr[:, :, c], bins=hist_bins, range=(0, 256))
            chans.append(h)
        hist = np.concatenate(chans).astype(float)
        if hist.sum() > 0:
            hist /= hist.sum()  # L1 normalization

        fp = {
            'phash': str(ph),
            'whash': str(wh),
            'dhash': str(dh),
            'color_hist': hist.tolist(),
        }
        fp['master'] = fp['phash']  # Designate primary hash for fast matching
        return fp


def _hex_hamming(h1_hex: str, h2_hex: str) -> int:
    """
    Compute Hamming distance between two hexadecimal hash representations.

    Args:
        h1_hex: First hash in hexadecimal string format
        h2_hex: Second hash in hexadecimal string format

    Returns:
        Hamming distance as integer value, returns 999 on processing error
    """
    try:
        return int(imagehash.hex_to_hash(h1_hex) - imagehash.hex_to_hash(h2_hex))
    except Exception:
        return 999


def _hist_cosine_sim(a: List[float], b: List[float]) -> float:
    """
    Calculate cosine similarity coefficient between two normalized histogram vectors.

    Args:
        a: First histogram vector with L1 normalization
        b: Second histogram vector with L1 normalization

    Returns:
        Cosine similarity coefficient in range [0.0, 1.0]
    """
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    if a_arr.sum() == 0 or b_arr.sum() == 0:
        return 0.0
    # Compute cosine similarity metric
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)


# Tuned threshold parameters optimized for scam detection accuracy
_PHASH_TOL = 20  # Hamming distance threshold for perceptual hash comparison
_WHASH_TOL = 30  # Hamming distance threshold for wavelet hash comparison
_DHASH_TOL = 30  # Hamming distance threshold for difference hash comparison
_HIST_SIM_THR = 0.85  # Cosine similarity threshold for color histogram matching


def verify_multisignal(test_fp: Dict[str, Any], db_fp: Dict[str, Any],
                       phash_tol: int = _PHASH_TOL,
                       whash_tol: int = _WHASH_TOL,
                       dhash_tol: int = _DHASH_TOL,
                       hist_thr: float = _HIST_SIM_THR) -> bool:
    """
    Execute multi-signal verification protocol to determine image fingerprint similarity.

    Implements hierarchical verification strategy: initial perceptual hash distance check
    followed by secondary signal validation requiring consensus from at least one additional
    perceptual metric to minimize false positive detections while maintaining tolerance for
    common image transformations.

    Args:
        test_fp: Fingerprint dictionary of the image under analysis
        db_fp: Reference fingerprint dictionary from database
        phash_tol: Maximum permissible Hamming distance for perceptual hash
        whash_tol: Maximum permissible Hamming distance for wavelet hash
        dhash_tol: Maximum permissible Hamming distance for difference hash
        hist_thr: Minimum required cosine similarity for color histograms

    Returns:
        Boolean indicating whether fingerprints represent the same source image
    """
    # Fast-path exact match verification for backward compatibility
    if test_fp.get('phash') == db_fp.get('phash'):
        return True

    # Primary verification: perceptual hash distance assessment
    db_ph = db_fp.get('phash')
    test_ph = test_fp.get('phash')
    if not db_ph or not test_ph:
        return False
    ph_dist = _hex_hamming(test_ph, db_ph)
    if ph_dist > phash_tol:
        return False

    # Secondary verification protocol: require consensus from at least one additional signal
    secondary_verified = False

    # Validate wavelet hash signal
    db_wh = db_fp.get('whash')
    test_wh = test_fp.get('whash')
    if db_wh and test_wh:
        try:
            if _hex_hamming(test_wh, db_wh) <= whash_tol:
                secondary_verified = True
        except Exception:
            pass

    # Validate difference hash signal if wavelet verification unsuccessful
    if not secondary_verified:
        db_dh = db_fp.get('dhash')
        test_dh = test_fp.get('dhash')
        if db_dh and test_dh:
            try:
                if _hex_hamming(test_dh, db_dh) <= dhash_tol:
                    secondary_verified = True
            except Exception:
                pass

    # Validate color histogram signal if previous verifications unsuccessful
    if not secondary_verified:
        db_hist = db_fp.get('color_hist')
        test_hist = test_fp.get('color_hist')
        if db_hist and test_hist:
            try:
                if _hist_cosine_sim(test_hist, db_hist) >= hist_thr:
                    secondary_verified = True
            except Exception:
                pass

    return secondary_verified


def find_matching_scam(test_fp: Dict[str, Any], scams: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Perform database search to identify scam entries matching the test fingerprint.

    Utilizes optimized lookup strategy with master hash indexing followed by
    comprehensive multi-signal verification for maximum detection accuracy.

    Args:
        test_fp: Fingerprint dictionary of the image to be analyzed
        scams: Collection of scam database entries containing fingerprint data

    Returns:
        Matching scam database entry if found, None otherwise
    """
    # Execute fast-path master hash lookup
    master = test_fp.get('master')
    if master:
        match = next((s for s in scams if s.get('master') == master), None)
        if match:
            return match

    # Perform comprehensive multi-signal verification scan
    candidates = []
    for scam in scams:
        try:
            if verify_multisignal(test_fp, scam):
                candidates.append(scam)
        except Exception:
            logger.exception('Multi-signal verification error encountered')

    if not candidates:
        # Diagnostic logging for closest match analysis
        if scams:
            closest = min(scams, key=lambda s: _hex_hamming(test_fp.get('phash', ''), s.get('phash', '')))
            dist = _hex_hamming(test_fp.get('phash', ''), closest.get('phash', ''))
            logger.debug("No matches identified; nearest phash distance: %d to %s", dist, closest.get('filename', 'unknown'))
        return None

    # Select optimal candidate based on minimum perceptual hash distance
    best = min(candidates, key=lambda s: _hex_hamming(test_fp.get('phash', ''), s.get('phash', '')))
    return best