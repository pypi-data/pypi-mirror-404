"""Color profile analysis for e-ink display compatibility."""

from io import BytesIO
from typing import ClassVar

from coloraide import Color  # type: ignore[import-untyped]
from PIL import Image


class ColorProfileAnalyzer:
    """Analyze image color compatibility with limited palette displays.

    Designed for Inky Impression 13.3" (2025) with Spectra 6 palette.
    Uses Delta E (CIE76) for perceptual color distance calculation.
    """

    # Spectra 6 palette - measured values from actual display
    # Source: https://forums.pimoroni.com/t/what-rgb-colors-are-you-using-for-the-colors-on-the-impression-spectra-6/27942
    SPECTRA_6_PALETTE: ClassVar[list[Color]] = [
        Color("srgb", [0.0, 0.0, 0.0]),  # Black #000000
        Color("srgb", [1.0, 1.0, 1.0]),  # White #ffffff
        Color("srgb", [0.627, 0.125, 0.125]),  # Red #a02020
        Color("srgb", [0.941, 0.878, 0.314]),  # Yellow #f0e050
        Color("srgb", [0.376, 0.502, 0.314]),  # Green #608050
        Color("srgb", [0.314, 0.502, 0.722]),  # Blue #5080b8
    ]

    @classmethod
    def calculate_compatibility_score(cls, image_data: bytes) -> float:
        """Score image compatibility with Spectra 6 palette.

        Algorithm:
        1. Resize image to 100x100 for speed
        2. Quantize to extract 8 dominant colors
        3. Calculate weighted Delta E distance to nearest palette color
        4. Convert to 0-1 score (higher = better fit)

        Args:
            image_data: Image bytes (JPEG, PNG, HEIC, etc.)

        Returns:
            Compatibility score 0.0-1.0 (1.0 = perfect match)

        """
        with Image.open(BytesIO(image_data)) as img:
            # Convert and resize for speed
            resized = img.convert("RGB").resize((100, 100))

            # Quantize to get dominant colors
            quantized = resized.quantize(colors=8, method=Image.Quantize.MEDIANCUT)
            palette_data = quantized.getpalette()
            if palette_data is None:
                return 0.5  # Default score if quantization fails

            palette = palette_data[:24]  # 8 colors x 3 (RGB)
            colors_with_counts = quantized.getcolors()

        if not colors_with_counts:
            return 0.5  # Default score if no colors found

        # Calculate weighted average Delta E to nearest palette color
        total_pixels = sum(count for count, _ in colors_with_counts)
        weighted_distance = 0.0

        for count, color_idx in colors_with_counts:
            # color_idx is palette index (int) for quantized P-mode images
            idx = int(color_idx)  # type: ignore[arg-type]
            r, g, b = palette[idx * 3 : idx * 3 + 3]
            img_color = Color("srgb", [r / 255, g / 255, b / 255])

            # Find minimum Delta E to any Spectra 6 color
            min_delta = min(img_color.delta_e(p) for p in cls.SPECTRA_6_PALETTE)
            weighted_distance += (count / total_pixels) * min_delta

        # Convert to 0-1 score
        # Delta E scale: 0 = identical, ~100 = maximally different
        # Divide by 50 to normalize (typical "bad" images score ~30-50)
        score = max(0.0, 1.0 - (weighted_distance / 50.0))
        return round(score, 3)
