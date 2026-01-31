"""
The audio track module.
"""
from yta_editor.tracks.abstract import _TrackWithAudio


class AudioTrack(_TrackWithAudio):
    """
    Class to represent a track in which we place
    audios to build a video project.
    """

    def __init__(
        self,
        timeline: 'Timeline',
        index: int
    ):
        super().__init__(
            timeline = timeline,
            index = index
        )