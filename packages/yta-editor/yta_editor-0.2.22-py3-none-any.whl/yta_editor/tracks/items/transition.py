# from yta_editor.tracks.items.abstract import TrackItemWithAudioMedia, _TrackItemWithVideo
from yta_editor.utils.transition_calculator import _TransitionCalculator
from yta_editor.tracks.items.video import _VideoTrackItem
from yta_editor.tracks.items.abstract import _TrackItemWithVideo, _TrackItemWithAudio
from yta_constants.enum import YTAEnum as Enum
from quicktions import Fraction
from typing import Union


# TODO: Move it
class TransitionMode(Enum):
    """
    The modes the TransitionTrackItem accept as mode to
    implement it, that is the way you handle the frames
    of the previous and the next clip.
    """

    TRIM = 'trim'
    """
    The transition will use the real frames of both the
    previous and the next clip, which will make both 
    clips last less time.

    It means that from:
    - `[ClipA] [Gap] [ClipB]`
    We will move to:
    - `[ClipA_trimmed] [Transition] [ClipB_trimmed]`
    """
    FREEZE_TAIL = 'freeze_tail'
    """
    The transition will use the last frame of the 
    previous clip but frozen, which means that it will
    be used for the whole transition duration. The next
    clip 'start' time moment will be increased because
    the previous clip is not trimmed and the transition
    will last an additional amount of time.

    It means that from:
    - `[ClipA] [Gap] [ClipB]`
    We will move to:
    - `[ClipA] [Transition] [ClipB_delayed]`
    """
    FREEZE_HEAD = 'freeze_head'
    """
    The transition will use the first frame of the next
    clip but frozen, which means that it will be used
    for the whole transition duration. The next clip
    'start' time moment will be increased because the
    previous clip is not trimmed and the transition will
    last an additional amount of time.

    It means that from:
    - `[ClipA] [Gap] [ClipB]`
    We will move to:
    - `[ClipA] [Transition] [ClipB_delayed]`
    """
    FREEZE_BOTH = 'freeze_both'
    """
    The transition will use the last frame of the
    previous clip and the first frame of the next one,
    but frozen, which means that they will be used for
    the whole transition duration. The next clip 'start'
    time moment will be increased because the previous
    clip is not trimmed and the transition will last an
    additional amount of time.

    It means that from:
    - `[ClipA] [Gap] [ClipB]`
    We will move to:
    - `[ClipA] [Transition] [ClipB_delayed]`
    """

class TransitionTrackItem(_TrackItemWithVideo, _TrackItemWithAudio):
    """
    A track item that is built by joining 2 different video
    items that are consecutive.
    """

    @property
    def copy(
        self
    ) -> '_TrackItem':
        """
        A copy of the current instance.
        """
        return TransitionTrackItem(
            track = self._track,
            t_start = self.t_start,
            duration = self.duration,
            type = self.type,
            mode = self.mode,
            item_in = self.item_in,
            item_out = self.item_out
        )
    
    @property
    def is_unchanged(
        self
    ) -> bool:
        """
        *For internal use only*

        Internal boolean flag to indicate if the source has
        been modified (or not), useful when we want to 
        optimize the way we access to the frames to render.

        If the original source has not been modified, we
        don't need to read frame by frame and apply any
        change so we can do it faster.

        (!) This property is useless here as it is a
        transition.
        """
        return True

    def __init__(
        self,
        track: 'VideoTrack',
        t_start: Union[int, float, Fraction],
        # TODO: We need to be able to handle options
        # different than the 50% of each clip
        duration: Union[int, float, Fraction],
        # TODO: How do we handle the type? Maybe a full config instead (?)
        type: str,
        mode: TransitionMode = TransitionMode.TRIM,
        # TODO: This is a special one so this should be different
        item_in: Union['_AudioTrackItem', '_VideoTrackItem', 'TransitionTrackItem', 'GapTrackItem', None] = None,
        item_out: Union['_AudioTrackItem', '_VideoTrackItem', 'TransitionTrackItem', 'GapTrackItem', None] = None
    ):
        mode = TransitionMode.to_enum(mode)

        super().__init__(
            track = track,
            t_start = t_start,
            duration = duration,
            item_in = item_in,
            item_out = item_out,
            # TODO: I think I don't need these transition fields
            # in this kind of item
            transition_in = None,
            transition_out = None
        )

        self.mode: TransitionMode = mode
        """
        The mode in which the transition must be implemented.
        """
        self._transition_calculator: _TransitionCalculator = _TransitionCalculator(
            transition_item = self,
            duration = self.duration
            #  TODO: The 'rate_function' has to come in the configuration
        )
        """
        *For internal use only*

        A transition calculator to simplify the way we handle
        the calculations to obtain the frames we need.
        """

    def _get_audio_frames_at(
        self,
        t_track: Union[int, float, Fraction],
        # TODO: Ignore this, we have 'self.fps' here
        video_fps: Union[int, float, Fraction] = None,
        # TODO: Ignore this, we don't need it...
        do_use_source_limits: bool = True
    ) -> Union['AudioFrame', None]:
        """
        Get the audio frames of the provided `t_track`
        global time moment according to the internal
        configuration of the track item.

        TODO: This method must be overwritten by the
        specific class implementations.
        """
        # TODO: Is this the correct way? Is it generating
        # audio frames for a whole video frame (?)
        item_in_audio_frames = (
            list(self.item_in.get_audio_frames_at(
                t_track = t_track,
                # TODO: We should not receive the param
                do_use_source_limits = True
            ))
            if self.mode not in [TransitionMode.FREEZE_HEAD, TransitionMode.FREEZE_BOTH] else
            self._track.audio_silent
        )

        item_out_audio_frames = (
            list(self.item_out.get_audio_frames_at(
                # t_track = t_track + self.duration,
                t_track = t_track,
                # TODO: We should not receive the param
                do_use_source_limits = True
            ))
            if self.mode not in [TransitionMode.FREEZE_TAIL, TransitionMode.FREEZE_BOTH] else
            self._track.audio_silent
        )

        # Obtain the local 't_transition' to calculate the progress
        t_transition = t_track - self.t_start

        t_progress = self._transition_calculator.get_progress_at(t_transition)

        audio_frames = self._transition_calculator._get_process_audio_frames(
            audio_frames_a = item_in_audio_frames,
            audio_frames_b = item_out_audio_frames,
            t_progress = t_progress
        )

        # # TODO: Implement this as a combination of the audio
        # # coming from clips at the same time, but by now I'm
        # # just returning something
        # frames = [
        #     AudioFrameCombinator.sum_tracks_frames(
        #         tracks_frames = non_empty_collapsed_frames,
        #         sample_rate = self.audio_fps,
        #         # TODO: This was not being sent before
        #         layout = self.audio_layout,
        #         format = self.audio_format
        #     )
        # ]

        # for audio_frame in frames:
        #     yield audio_frame

        return audio_frames

        return item_in_audio_frames

    def _get_video_frame_at(
        self,
        t_track: Union[int, float, Fraction],
        do_use_source_limits: bool = False
    ) -> Union['VideoFrame', None]:
        """
        Get the frame of the transition for the global
        `t_track` time moment provided.
        """
        # TODO: The 't' must be the global value of the timeline
        # Obtain the frames from each video
        # TODO: I actually need to obtain a frame that will be
        # out of the current 'item_in' valid time interval, as
        # it has been trimmed because of this transition, and 
        # the part we are using is just after (for the
        # 'item_in', before for the 'item_out') the last part
        # we are showing in the video
        # TODO: Calculate the 't' based on the 'item_in' t_end
        # TODO: We need to read the 'item_in.t_end' + 'local_t'
        # for the transition

        """
        Imagine this context:
        - item_in: [0, 2)   Transition: [2, 3)   item_out: [3, 4)
        The global t=2.5 is actually the 0.5 inside the 
        transition, that should read the 'item_in.t_end+0.5' (out
        of the time interval that is being shown) of the item_in.

        Now imagine that the item_in is [0, 2) but the media 
        inside is actually [0, 8) and it is reading from [3, 5).
        That means that the transition for the global t=2.5, 
        is a local_t=0.5, should be reading the t=2.5 (out of
        time interval), that is actually the t_media=5.5.
        """

        """
        As the media has been enshortened due to the transition,
        we need to use `t_track` values that are out of the 
        current item media limits, thats why we force the values
        to be allowed with the `do_use_source_limits` parameter.

        But, as the transition could be based on frozen frames,
        we 
        """
        frame_item_in = (
            self.item_in.get_video_frame_at(
                t_track = t_track,
                do_use_source_limits = True
            )
            if self.mode not in [TransitionMode.FREEZE_HEAD, TransitionMode.FREEZE_BOTH] else
            # TODO: Return as the one on top is doing
            self.item_in._last_video_frame
        ).as_rgba_numpy

        frame_item_out = (
            self.item_out.get_video_frame_at(
                #t_track = t_track + self.duration,
                t_track = t_track,
                do_use_source_limits = True
            )
            if self.mode not in [TransitionMode.FREEZE_TAIL, TransitionMode.FREEZE_BOTH] else
            # TODO: Return as the one on top is doing
            self.item_out._first_video_frame
        ).as_rgba_numpy

        # Obtain the local 't_transition' to calculate the progress
        t_transition = t_track - self.t_start

        """
        *Representacion con t(global) de clips*
        Clip A: [0, 3)   Clip B: [3, 5)
        - Añadimos transition de 1s
        Clip A: [0, 2)   Transition: [2, 3)   Clip B: [3, 4)
        - La 'Transition' tiene [2, 3) de A y [0, 1) de B
        - El t(global)=2.5 ahora cae en la transición, que se
          convierte a t(local)=2.5-(3.0-1.0)=0.5, y dado que
          la duration es 1.0; 0.5 es el t_progress=0.5
        """
        t_progress = self._transition_calculator.get_progress_at(t_transition)

        frame = self._transition_calculator._process_frame(
            frame_a = frame_item_in,
            frame_b = frame_item_out,
            t_progress = t_progress
        )

        # TODO: Improve this
        from yta_editor.utils.frame_wrapper import VideoFrameWrapped

        return VideoFrameWrapped(frame)
    
    # TODO: What if I have another abstract class to inherit
    # from that is different having not the transitions 
    # instead of blocking these methods here? Maybe a 
    # TrackItem, TrackItemWithTransitions (?)
    #  TODO: Should I remove this (?)
    def set_transition_in(self, transition):
        raise Exception('This class can not have transitions')
    
    def set_transition_out(self, transition):
        raise Exception('This class can not have transitions')
    
    def unset_transition_in(self):
        raise Exception('This class can not have transitions')
    
    def unset_transition_out(self):
        raise Exception('This class can not have transitions')  
