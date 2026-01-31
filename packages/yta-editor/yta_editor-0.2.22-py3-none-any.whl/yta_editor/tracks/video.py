"""
The video track module.
"""
from yta_editor.tracks.abstract import _TrackWithAudio, _TrackWithVideo


class VideoTrack(_TrackWithVideo, _TrackWithAudio):
    """
    Class to represent a track in which we place
    videos to build a video project.
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