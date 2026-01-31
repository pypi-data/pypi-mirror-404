from yta_editor.transformations.effects.abstract import Effect
from av.video import VideoFrame

import numpy as np


class VideoEffect(Effect):
    """
    An effect for a video input.

    This class is just to be able to identify the
    hierarchy and which effect is designed for 
    the video.
    """

    pass

class VideoEffects:
    """
    A set of effects to apply in a video input.
    """

    # TODO: This is not as simple as a list, it must be
    # managed with the specific nodes we designed that
    # are able to combine and are time-concerned.

    def __init__(
        self,
        effects: list[VideoEffect] = []
    ):
        self.effects: list[VideoEffect] = effects
        """
        The list of the effects to apply in the video.
        """

    def apply(
        self,
        frame,
        t: float
    # TODO: Set the type
    ) -> any:
        """
        Apply all the effects that should be applied at the
        given `t` time moment to the provided audio `frame`.
        """
        width, height = frame.width, frame.height

        if len(self.effects) > 0:
            # TODO: Only if 'frame' is 'av.VideoFrame'
            processed_frame = frame.to_ndarray(format = 'rgba')

            for effect in self.effects:
                # TODO: The effect has to be a real input (numpy or texture)
                processed_frame = effect.apply(
                    frame = processed_frame,
                    t = t
                )

            # TODO: Only if texture:
            # data = processed_frame.read()
            # data = np.frombuffer(data, dtype = np.uint8)
            # # The shape has to be the expected by the timeline
            # # TODO: Do I need the 'output_size' here? It should be
            # # defined before the 'transform' processing...
            # # data = data.reshape(self.output_size[1], self.output_size[0], 4)
            # data = data.reshape(height, width, 4)
            # # OpenGL uses textures flipped, so...
            # data = np.flip(data, axis = 0)
            # # TODO: I'm removing the alpha channel here...
            # # processed_frame = data[:, :, :3]

            # If numpy
            data = processed_frame.astype(np.uint8)
            
            frame = VideoFrame.from_ndarray(
                # TODO: Force this with the 'yta-numpy' utils to 'np.uint8'
                array = data,
                #format = 'rgb24'
                format = 'rgba'
            )

        return frame
