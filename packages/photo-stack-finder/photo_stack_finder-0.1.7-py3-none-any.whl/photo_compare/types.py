"""Type aliases for photo comparison arrays.

This module defines common numpy array type aliases used throughout the
photo comparison subsystem. Using these aliases makes type signatures
more readable while maintaining strict type safety.
"""

import numpy as np
import numpy.typing as npt

# Image arrays (H, W, C) - typically uint8 RGB images
ImageArray = npt.NDArray[np.uint8]

# Grayscale images (H, W) - typically uint8 single channel
GrayscaleArray = npt.NDArray[np.uint8]

# Histogram arrays (1D) - typically float64 normalized histograms
HistogramArray = npt.NDArray[np.float64]

# Feature descriptor arrays (N, D) - typically float32 feature vectors
# where N is the number of keypoints and D is the descriptor dimension
DescriptorArray = npt.NDArray[np.float32]

# Hash arrays - boolean arrays representing perceptual hashes
HashArray = npt.NDArray[np.bool_]

# Structural comparison arrays (H, W) - float64 SSIM maps
StructuralArray = npt.NDArray[np.float64]
