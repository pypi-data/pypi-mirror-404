from yta_editor_nodes.processor.video.transitions import CircleOpeningTransitionProcessor
from yta_editor_common.frame.helper import FrameHelper
from yta_validation.parameter import ParameterValidator
from yta_validation import PythonValidator
from yta_math_easings.enums import EasingFunctionName
from yta_math_easings.abstract import EasingFunction
from av.video.frame import VideoFrame
from quicktions import Fraction
from typing import Union

import numpy as np


# TODO: This class below could be repeated and I just
# created because I needed to (at least by now)
class _TransitionCalculator:
    """
    *For internal use only*

    A class to simplify the way we make the calculations
    related to a transition. This class must be used within
    a transition item that needs these kind of calculations.

    The `easing_function_name` will define the transition
    speed, that is `linear` by default.
    """

    def __init__(
        self,
        transition_item: 'TransitionTrackItem',
        duration: float,
        easing_function_name: EasingFunctionName = EasingFunctionName.LINEAR,
    ):
        easing_function_name = EasingFunctionName.to_enum(easing_function_name)

        self._transition_item: 'TransitionTrackItem' = transition_item
        """
        The transition item this helper was instantiated for.
        """
        self.duration: float = duration
        """
        The duration of the transition.
        """
        self.easing_function: EasingFunction = EasingFunction.get(easing_function_name)()
        """
        The easing function to be applied in the transition
        progress to handle its speed.
        """
        # TODO: This depends on each node implementation and the
        # arguments are different. By now I'm forcing this
        self._transition_node: CircleOpeningTransitionProcessor = CircleOpeningTransitionProcessor(
            # TODO: What do I do with the 'opengl_context' here (?)
            opengl_context = None
        )
        """
        The node that will process the transition, that must
        be implemented by the child class.
        """

    def get_progress_at(
        self,
        t: float
    ) -> float:
        """
        Get the transition progress value, that will
        be in the `[0.0, 1.0]` range, according to the
        `t` time moment provided and the `rate_function`
        that must be applied in this transition.

        This method should be called only when the
        transition has to be applied, so the `t` is
        a time moment in which the two frames are 
        being played together.

        The `t` value here must be a value in the range
        [0, self.duration] and it must be calculated
        before calling this method.
        """

        """
        By now, the transition we are applying is
        as simple as being in the middle of the 2
        clips provided and lasting the 'duration'
        provided, being executed with a linear t.
        """
        # TODO: We force it, by now, to be calculated
        # outside as in this [0, self.duration] range
        ParameterValidator.validate_mandatory_number_between('t', t, 0, self.duration)

        # Obtain the 't' as a normalized value
        t_normalized = max(
            0.0,
            min(
                1.0,
                t / self.duration
            )
        )

        return (
            0.0
            if t < 0 else
            1.0
            if t > self.duration else
            self.easing_function.ease(
                t_normalized = t_normalized
            )
        )
    
    # TODO: This method can be overwritten to change
    # its behaviour if the specific transition needs
    # it
    def _process_frame(
        self,
        frame_a: Union['moderngl.Texture', 'np.ndarray'],
        frame_b: Union['moderngl.Texture', 'np.ndarray'],
        t_progress: float,
    ) -> VideoFrame:
        # TODO: Maybe this can be placed in the general
        # class if it doesn't change

        # TODO: This can be a texture
        processed_frame = self._get_process_frame_array(
            frame_a = frame_a,
            frame_b = frame_b,
            t_progress = t_progress
        # TODO: Force this with the 'yta-numpy' utils to 'np.uint8'
        )

        if PythonValidator.is_numpy_array(processed_frame):
            processed_frame = processed_frame.astype(np.uint8)

            # frame = VideoFrame.from_ndarray(
            #     # TODO: Force this with the 'yta-numpy' utils to 'np.uint8'
            #     array = processed_frame,
            #     format = 'rgb24'
            # )
        elif PythonValidator.is_instance_of(processed_frame, 'Texture'):
            processed_frame, has_alpha = FrameHelper.texture_to_ndarray(
                frame = processed_frame
            
            )
            
            # TODO: Removing the alpha channel here but, should I (?)
            if has_alpha:
                processed_frame = processed_frame[:, :, :3]

        else:
            # TODO: Wtf? This should not happen
            raise Exception('Wowowowooo, no texture, no np.ndarray... wtf?')
        
        frame = FrameHelper.ndarray_to_videoframe(
            frame = processed_frame,
            do_include_alpha = False,
            pts = None,
            # TODO: This is hardcoded and shouldn't be
            time_base = Fraction(1, 60)
        )
        
        # TODO: If I return this as a numpy and make the
        # transformations and then we want to use that
        # same frame within other GPU processor... we are
        # f**cked
        return frame
    
    # TODO: Overwrite this method to make it custom (?)
    def _get_process_frame_array(
        self,
        frame_a: Union['moderngl.Texture', 'np.ndarray'],
        frame_b: Union['moderngl.Texture', 'np.ndarray'],
        t_progress: float,
    ) -> Union[np.ndarray, 'moderngl.Texture']:
        """
        Get the numpy array that will be used to build the
        pyav VideoFrame that will be returned.
        """
        return self._transition_node.process(
            first_input = frame_a,
            second_input = frame_b,
            progress = t_progress,
            # TODO: What do we do with these parameters (?)
            do_use_gpu = True,
            output_size = (1920, 1080)
        )
    
    def _get_process_audio_frames(
        self,
        audio_frames_a: list['AudioFrameWrapped'],
        audio_frames_b: list['AudioFrameWrapped'],
        t_progress: float
    ) -> list['AudioFrame']:
        """
        Get the numpy array that will be used to build the
        pyav AudioFrame that will be returned.
        """

        """
        TODO: I don't know how to handle the audio within the
        transitions, because each transition works in a specific
        way and making the audio behave like the video movement
        is not easy... It could be based on the 't_progress',
        using something like this below (based on S-Curve Crossfade
        weights):

        weight_a = 0.5 * (1 + math.cos(t_progress * math.pi))
        weight_b = 1 - weight_a
        mixed_audio_frames = audio_frames_a * weight_a + audio_frames_b * weight_b

        But, as I don't know actually how to do it, by now we are
        just mixing both of them during the transition time in the
        same way as the video frames are accessed.
        """
        # TODO: Move this to top (?)
        from yta_editor.utils.frame_combinator import AudioFrameCombinator
        from yta_editor.timeline import concatenate_audio_frames

        collapsed_frames = [
            concatenate_audio_frames(frames)
            for frames in [audio_frames_a, audio_frames_b]
        ]

        # We keep only the non-silent frames because
        # we will sum them after and keeping them will
        # change the results.
        non_empty_collapsed_frames = [
            frame._frame
            for frame in collapsed_frames
            if not frame.is_from_gap
        ]

        if len(non_empty_collapsed_frames) == 0:
            # If they were all silent, just keep one
            non_empty_collapsed_frames = [collapsed_frames[0]._frame]

        frames = [
            AudioFrameCombinator.sum_tracks_frames(
                tracks_frames = non_empty_collapsed_frames,
                sample_rate = self._transition_item._track.audio_fps,
                # TODO: This was not being sent before
                layout = self._transition_item._track.audio_layout,
                format = self._transition_item._track.audio_format
            )
        ]

        # for audio_frame in frames:
        #     yield audio_frame
        # TODO: Should I yield (?)
        return frames
