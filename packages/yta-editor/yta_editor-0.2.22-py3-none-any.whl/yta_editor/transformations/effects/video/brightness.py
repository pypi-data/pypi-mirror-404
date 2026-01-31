from yta_editor.transformations.effects.abstract import EffectParams
from yta_editor.transformations.effects.video import VideoEffect
from yta_editor.transformations.time_based_parameter import TimeBasedParameter, ConstantTimeBasedParameter
from yta_editor_nodes.processor import BrightnessNodeProcessor
from yta_editor_utils.texture import TextureUtils
from yta_validation import PythonValidator
from dataclasses import dataclass


# TODO: We need to define all the specific effect
# params to be able to build them properly missing
# no fields
@dataclass
class BrightnessVideoEffectParams(EffectParams):
    """
    The parameters to use when applying the effect
    that changes the brightness for a specific `t`
    time moment.

    This will be returned by the effect when
    calculated, for a specific `t` time moment.
    """

    def __init__(
        self,
        brightness: float
    ):
        self.brightness: float = brightness
        """
        The value to apply as brightness.
        """
        

class BrightnessVideoEffect(VideoEffect):
    """
    The effect that will change the brightness of the
    element according to the provided conditions.
    """

    def __init__(
        self,
        do_use_gpu: bool = True,
        # TODO: I don't like giving this fps
        brightness: TimeBasedParameter = ConstantTimeBasedParameter(2.0)
    ):
        self.do_use_gpu: bool = do_use_gpu
        """
        Flag to indicate if using GPU or not.
        """
        self.brightness: TimeBasedParameter = brightness
        """
        The `TimeBasedParameter` that defines the value that should
        be applied for the specific `t` time moment requested.
        """

    def _get_params_at(
        self,
        t: float
    ) -> BrightnessVideoEffectParams:
        """
        *For internal use only*

        Get the parameters that must be applied at the given
        `t` time moment.
        """
        return BrightnessVideoEffectParams(
            brightness = self.brightness.get_value_at(t)
        )

    def apply(
        self,
        # TODO: Set the type
        frame,
        t: float,
    ):
        """
        Apply the effect to the given `frame` at the `t` time
        moment provided.
        """
        params = self._get_params_at(t)

        if params.brightness == 1.0:
            return TextureUtils.numpy_to_uint8(frame)
        
        frame_processed = BrightnessNodeProcessor(
            # TODO: What do I do with the 'opengl_context' (?)
            opengl_context = None
        ).process(
            input = frame,
            do_use_gpu = self.do_use_gpu,
            factor = params.brightness
        )

        # TODO: We should be doing this in another way maybe...
        if PythonValidator.is_instance_of(frame_processed, 'Texture'):
            from yta_editor_common.frame.helper import FrameHelper
            frame_processed = FrameHelper.texture_to_ndarray(frame_processed)[0]

        frame_processed = TextureUtils.numpy_to_uint8(frame_processed)

        # The output is forced to be 'uint8'
        return frame_processed