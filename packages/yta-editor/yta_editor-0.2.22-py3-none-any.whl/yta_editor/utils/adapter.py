"""
TODO: Check if this class can be refactored, moved
to somewhere else or put in other library.
"""
from yta_constants.enum import YTAEnum as Enum
import numpy as np


class FrameAdapterMode(Enum):
    """
    The different modes we have to adapt the frames to
    a specific resolution.
    """

    ALPHA_BACKGROUND = 'alpha_background'
    """
    A full transparent frame will be created with the
    expected resolution and the original frame will be
    placed in the middle.
    """

class FrameAdapter:
    """
    A class to modify the frames and adapt them to the 
    resolution we need for the timeline. This is needed
    to be able to use them as inputs in the nodes.
    """

    @staticmethod
    def adapt(
        frame: np.ndarray,
        resolution: tuple[int, int] = (1920, 1080),
        mode: FrameAdapterMode = FrameAdapterMode.ALPHA_BACKGROUND
    ) -> np.ndarray:
        """
        Adapt the `frame` provided to fit the expected and
        also given `resolution` by using the `adapt_mode`
        provided as parameter.
        """
        mode = FrameAdapterMode.to_enum(mode)

        if frame.size == resolution:
            return frame

        # TODO: Improve this, please
        if mode == FrameAdapterMode.ALPHA_BACKGROUND:
            return _adapt_with_alpha(
                frame = frame,
                resolution = resolution
            )

# Specific methods below
def _adapt_with_alpha(
    frame: np.ndarray,
    resolution: tuple[int, int]
) -> np.ndarray:
    """
    Creates a fully alpha background with the `resolution`
    given and puts the `frame` provided in the middle of
    it.

    This is the functionality to be done when using the
    `ALPHA_BACKGROUND` option.
    """
    if frame.ndim != 3:
        raise Exception('The frame must be HxWxC.')

    src_h, src_w, src_c = frame.shape

    if src_c not in (3, 4):
        raise Exception('The frame must be RGB or GBA.')

    # Final transparent frame
    dst = np.zeros((resolution[1], resolution[0], 4), dtype = frame.dtype)

    # RGBA if necessary
    if src_c == 3:
        src_rgba = np.empty((src_h, src_w, 4), dtype = frame.dtype)
        src_rgba[..., :3] = frame
        src_rgba[..., 3] = np.iinfo(frame.dtype).max
    else:
        src_rgba = frame

    # Offsets to center
    offset_x = (resolution[0] - src_w) // 2
    offset_y = (resolution[1] - src_h) // 2

    if (
        offset_x < 0 or
        offset_y < 0
    ):
        # TODO: Do rescale and crop if needed
        raise Exception('Original frame is bigger than the resolution requested.')

    # Copy it
    dst[
        offset_y:offset_y + src_h,
        offset_x:offset_x + src_w
    ] = src_rgba

    return dst

# TODO: Create the GPU node that does this
