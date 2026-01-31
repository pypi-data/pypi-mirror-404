from yta_editor.transformations.time_based_parameter import TimeBasedParameter, ConstantTimeBasedParameter
from yta_editor_nodes.compositor import DisplacementWithRotationNodeCompositor
from yta_validation.parameter import ParameterValidator
from av import VideoFrame
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union

import numpy as np


@dataclass
class AudioTransformState:
    """
    *Dataclass*

    A dataclass to represent the information about the
    state of a transformation we should apply to 
    transform an audio, that has been calculated for a
    specific `t` time moment.
    """

    def __init__(
        self,
        volume: float = 0.0
    ):
        self.volume: float = volume
        """
        The volume to apply at the audio at that moment.
        """

@dataclass
class VideoTransformState:
    """
    *Dataclass*

    A dataclass to represent the information about the
    state of a transformation we should apply to 
    transform a video, that has been calculated for a
    specific `t` time moment.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        rotation: float = 0.0,
        opacity: float = 1.0,
        output_size: tuple[int, int] = (1920, 1080)
    ):
        self.x: float = x
        """
        The `x` coordinate to position the video top left corner.
        """
        self.y: float = y
        """
        The `y` coordinate to position the video top left corner.
        """
        self.scale_x: float = scale_x
        """
        The factor of scale for the `width` we want.
        """
        self.scale_y: float = scale_y
        """
        The factor of scale for the `height` we want.
        """
        self.rotation: float = rotation
        """
        The `rotation` we want, expressed in degrees (to the right).
        """
        self.opacity: float = opacity
        """
        The `opacity` we want in the frame.
        """
        self.output_size: tuple[int, int] = output_size
        """
        The output size we want to be able to reshape the frame
        after the transformation.
        """

class Transform(ABC):
    """
    *Abstract class*

    Abstract class to be inherited by the `Transform`
    implementation related to audio and video.
    """

    @abstractmethod
    def _get_state_at(
        self,
        t: float
    ) -> Union[VideoTransformState, AudioTransformState]:
        """
        Get the `TransformState` dataclass that will indicate
        the values we have to apply to transform the timeline
        for the `t` time moment provided.
        """
        pass

    @abstractmethod
    def apply(
        self,
        # TODO: Set the type
        frame: any,
        t: float
    # TODO: Set the type
    ) -> any:
        """
        Apply the transformation to the given `frame` at the also
        provided `t` (which will be used to obtain the transform
        state to apply).
        """
        pass

class VideoTransform(Transform):
    """
    The transformation conditions to define how we want
    to modify the different time moments of a video in
    the timeline.

    This is attached to a timeline video track item and
    will be applied on it. This is useful to apply the
    basic modifications.

    These values are time functions, and the values
    change according to the `t` time moment in which
    the values are requested: position, rotation,
    scale, opacity, etc.

    TODO: I think we should have 't_start' and 't_end'
    for another version that is applied on the track
    instead.
    """

    @property
    def copy(
        self
    ) -> 'VideoTransform':
        """
        Get a copy of it.
        """
        return VideoTransform(
            t_start = self.t_start,
            t_end = self.t_end,
            # TODO: Maybe we need a '.copy' of these below (?)
            x = self.x,
            y = self.y,
            scale_x = self.scale_x,
            scale_y = self.scale_y,
            rotation = self.rotation,
            opacity = self.opacity
        )

    def __init__(
        self,
        # TODO: Maybe this 't_start' has to be removed
        t_start: Union[float, None] = None,
        # TODO: Maybe this 't_end' has to be removed
        t_end: Union[float, None] = None,
        #  TODO: I don't like giving these fps
        x: TimeBasedParameter = ConstantTimeBasedParameter(0),
        y: TimeBasedParameter = ConstantTimeBasedParameter(0),
        scale_x: TimeBasedParameter = ConstantTimeBasedParameter(1),
        scale_y: TimeBasedParameter = ConstantTimeBasedParameter(1),
        rotation: TimeBasedParameter = ConstantTimeBasedParameter(0),
        opacity: TimeBasedParameter = ConstantTimeBasedParameter(1),
        output_size: tuple[int, int] = (1920, 1080)
    ):
        ParameterValidator.validate_positive_float('t_start', t_start, do_include_zero = True)
        ParameterValidator.validate_positive_float('t_end', t_end, do_include_zero = True)
        ParameterValidator.validate_mandatory_instance_of('x', x, TimeBasedParameter)
        ParameterValidator.validate_mandatory_instance_of('y', y, TimeBasedParameter)
        ParameterValidator.validate_mandatory_instance_of('scale_x', scale_x, TimeBasedParameter)
        ParameterValidator.validate_mandatory_instance_of('scale_y', scale_y, TimeBasedParameter)
        ParameterValidator.validate_mandatory_instance_of('rotation', rotation, TimeBasedParameter)
        ParameterValidator.validate_mandatory_instance_of('opacity', opacity, TimeBasedParameter)

        self.t_start: Union[float, None] = t_start
        """
        The specific time moment in which we should start
        applying the transformation. If `None`, it will be
        applied since the begining of the item associated
        to this transformation.
        """
        self.t_end: Union[float, None] = t_end
        """
        The specific time moment in which we should stop
        applying the transformation. If `None`, it will be
        applied until the end of the item associated to this
        transformation.
        """
        self.x: TimeBasedParameter = x
        self.y: TimeBasedParameter = y
        self.scale_x: TimeBasedParameter = scale_x
        self.scale_y: TimeBasedParameter = scale_y
        self.rotation: TimeBasedParameter = rotation
        self.opacity: TimeBasedParameter = opacity
        self.output_size: tuple[int, int] = output_size
        """
        The output size we want to be able to reshape the frame
        after the transformation, that must fit the output of
        the track in which the item is placed.
        """

    def _get_state_at(
        self,
        t: float
    ) -> VideoTransformState:
        """
        Get the `TransformState` dataclass that will indicate
        the values we have to apply to transform the timeline
        for the `t` time moment provided.
        """
        return VideoTransformState(
            x = self.x.get_value_at(t),
            y = self.y.get_value_at(t),
            scale_x = self.scale_x.get_value_at(t),
            scale_y = self.scale_y.get_value_at(t),
            rotation = self.rotation.get_value_at(t),
            opacity = self.opacity.get_value_at(t),
        )
    
    def apply(
        self,
        # TODO: Set the type
        frame: any,
        t: float
    # TODO: Set the type
    ) -> Union[VideoFrame, any]:
        """
        Apply the transformation to the given `frame` at the also
        provided `t` (which will be used to obtain the transform
        state to apply).
        """
        transform_state = self._get_state_at(t)

        # Apply the effects to the 'frame' if needed
        if (
            transform_state.x != 0 or
            transform_state.y != 0 or
            transform_state.scale_x != 1 or
            transform_state.scale_y != 1 or
            transform_state.rotation != 0
        ):
            # TODO: Maybe we should receive here not a VideoFrame
            # yet...
            # 1. Here we receive a pyav.VideoFrame
            width, height = frame.width, frame.height
            frame_as_rgba = frame.to_ndarray(format = 'rgba')

            # 2. We process (transform) the frame
            # TODO: Should I use the 'DisplayAtOver' node instead (?)
            processed_frame = DisplacementWithRotationNodeCompositor(
                # TODO: Where do I have the context (?)
                opengl_context = None
            ).process(
                base_input = None,
                overlay_input = frame_as_rgba,
                position = (transform_state.x, transform_state.y),
                size = (transform_state.scale_x * width, transform_state.scale_y * height),
                rotation = transform_state.rotation,
                output_size = self.output_size
            )

            # 3. We need to transform it back to a pyav.VideoFrame,
            # but now it is a moderngl.Texture

            # TODO: This is also being done in the'transition.py',
            # so we should think about refactoring the code and
            # reusing it...
            
            """
            We have to reshape the processed frame, that comes
            as a moderngl.Texture, to the output format, so we
            need to receive it from somewhere to force it.
            """
            data = processed_frame.read()
            data = np.frombuffer(data, dtype = np.uint8)
            # The shape has to be the expected by the timeline
            data = data.reshape(self.output_size[1], self.output_size[0], 4)
            # OpenGL uses textures flipped, so...
            data = np.flip(data, axis = 0)

            # TODO: I'm removing the alpha channel here...
            # processed_frame = data[:, :, :3]
            
            frame = VideoFrame.from_ndarray(
                # TODO: Force this with the 'yta-numpy' utils to 'np.uint8'
                array = data,
                #format = 'rgb24'
                format = 'rgba'
            )

            # TODO: This above is maybe slow, but is there other way (?)

        # TODO: By now I'm not handling the 'opacity' as it is
        # not very important
        # if transform_state.opacity != 1:
        #     # TODO: Apply the opacity transformation
        #     pass
        # TODO: Apply the 'opacity' somehow

        return frame
    
    @staticmethod
    def default(
    ) -> 'VideoTransform':
        """
        Get an instance with the default values. Useful to
        instantiate it when `None` provided.
        """
        return VideoTransform(
            t_start = None,
            t_end = None,
            x = ConstantTimeBasedParameter(0),
            y = ConstantTimeBasedParameter(0),
            scale_x = ConstantTimeBasedParameter(1),
            scale_y = ConstantTimeBasedParameter(1),
            rotation = ConstantTimeBasedParameter(0),
            opacity = ConstantTimeBasedParameter(1),
            output_size = (1920, 1080)
        )
    
class AudioTransform(Transform):
    """
    The transformation conditions to define how we want
    to modify the different time moments of an audio in
    the timeline.

    This is attached to a timeline audio track item and
    will be applied on it. This is useful to apply the
    basic modifications.

    These values are time functions, and the values
    change according to the `t` time moment in which
    the values are requested: volume, intensity,
    equalization, noise reduction, etc.

    TODO: I think we should have 't_start' and 't_end'
    for another version that is applied on the track
    instead.
    """

    @property
    def copy(
        self
    ) -> 'AudioTransform':
        """
        Get a copy of it.
        """
        return AudioTransform(
            t_start = self.t_start,
            t_end = self.t_end,
            # TODO: Maybe we need a '.copy' of these below (?)
            volume = self.volume
        )

    def __init__(
        self,
        # TODO: Maybe this 't_start' has to be removed
        t_start: Union[float, None] = None,
        # TODO: Maybe this 't_end' has to be removed
        t_end: Union[float, None] = None,
        # TODO: By now I'm only modifying the volume
        # TODO: I don't like giving this fps
        volume: TimeBasedParameter = ConstantTimeBasedParameter(0)
    ):
        ParameterValidator.validate_positive_float('t_start', t_start, do_include_zero = True)
        ParameterValidator.validate_positive_float('t_end', t_end, do_include_zero = True)
        ParameterValidator.validate_mandatory_instance_of('volume', volume, TimeBasedParameter)

        self.t_start: Union[float, None] = t_start
        """
        The specific time moment in which we should start
        applying the transformation. If `None`, it will be
        applied since the begining of the item associated
        to this transformation.
        """
        self.t_end: Union[float, None] = t_end
        """
        The specific time moment in which we should stop
        applying the transformation. If `None`, it will be
        applied until the end of the item associated to this
        transformation.
        """
        self.volume: TimeBasedParameter = volume

    def _get_state_at(
        self,
        t: float
    ) -> AudioTransformState:
        """
        Get the `TransformState` dataclass that will indicate
        the values we have to apply to transform the timeline
        for the `t` time moment provided.
        """
        return AudioTransformState(
            volume = self.volume.get_value_at(t),
        )
    
    def apply(
        self,
        # TODO: Set the type
        frame: any,
        t: float
    # TODO: Set the type
    ) -> any:
        """
        Apply the transformation to the given `frame` at the also
        provided `t` (which will be used to obtain the transform
        state to apply).
        """
        transform_state = self._get_state_at(t)

        # Apply the effects to the 'frame' if needed
        if transform_state.volume != 1:
            # TODO: Apply the audio modifications
            # TODO: We don't have any audio modification node
            pass

        return frame
    
    @staticmethod
    def default(
    ) -> 'AudioTransform':
        """
        Get an instance with the default values. Useful to
        instantiate it when `None` provided.
        """
        return AudioTransform(
            t_start = None,
            t_end = None,
            volume = ConstantTimeBasedParameter(0)
        )