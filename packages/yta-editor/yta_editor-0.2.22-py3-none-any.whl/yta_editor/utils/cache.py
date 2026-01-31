from yta_validation.parameter import ParameterValidator
from yta_temp import Temp
from yta_logger import ConsolePrinter
from pathlib import Path
from typing import Union

import av
import subprocess


CACHE_PREFIX: str = 'cache_yta'
"""
The prefix we use for the temporary files we create
by using the cache.
"""

class FramesCacheFactory:
    """
    Factory to simplify the access to our cached frames.

    Use its static methods to obtain the frames.
    """

    @staticmethod
    def black_video_frame(
        size: tuple[int, int],
        video_fps: float,
        transparency: Union[float, None] = None
    ):
        """
        Get a black video frame by using the cache system. The
        frame will be transparent if the `transparency` value
        provided is a float (between 0.0 and 1.0), or opaque 
        if it is None.
        """
        return BlackFrameCache.get(
            size = size,
            video_fps = video_fps,
            transparency = transparency
        )

    @staticmethod
    def silent_audio_frame(
        audio_fps: float,
        audio_layout: str,
        audio_format: str,
        audio_samples_per_frame: float
    ):
        """
        Get a silent audio frame by using the cache system.
        """
        return SilentAudioFrameCache.get(
            audio_fps = audio_fps,
            audio_layout = audio_layout,
            audio_format = audio_format,
            audio_samples_per_frame = audio_samples_per_frame
        )

class BlackFrameCache:
    """
    A black video frames cached generator, useful when we
    need the same black frames again and again.

    This class will create temporary files (in the WIP folder)
    to load them directly with the pyav library.
    """

    _cache = {}
    """
    The cache that is able to store all the black frames that
    we create during the process. The frame specifications 
    will be the key to access it in the dict.
    """

    @staticmethod
    def get(
        size: tuple[int, int],
        video_fps: float,
        transparency: Union[float, None] = None
    ) -> 'VideoFrame':
        """
        Get a black video frame (transparent or not, according
        to the `transparency` parameter provided) of the given
        `size` and with the also provided `video_fps` and
        `pixel_format`.

        The video frames will be cached so the access the
        next time is instantaneous.

        TODO: This seems to be unnecessary as we can generate
        the frame in memory and we don't need to write it...
        """
        ParameterValidator.validate_number_between('transparency', transparency, 0.0, 1.0)
        
        pixel_format = (
            'rgb24'
            if transparency is None else
            'rgba'
        )

        key = (size[0], size[1], video_fps, pixel_format)

        if key in BlackFrameCache._cache:
            return BlackFrameCache._cache[key]

        width, height = size

        # Temporary specific file
        filename = (
            f'{CACHE_PREFIX}_black_{width}x{height}_{video_fps}_{pixel_format}.mp4'
            if transparency is None else
            f'{CACHE_PREFIX}_transparent_{str(transparency)}_black_{width}x{height}_{video_fps}_{pixel_format}.mp4'
        )
        filename = Temp.get_custom_wip_filename(filename)

        # 'black@0.0' means fully transparent, so we transform
        # our parameter to fit the str we need
        transparency = 1.0 - transparency

        color = (
            'black'
            if transparency is None else
            # Color must be something like 'black@0.0'
            f'black@{str(transparency)}'
        )

        if not Path(filename).exists():
            cmd = [
                'ffmpeg',
                '-y',
                '-f',
                'lavfi',
                '-i',
                f'color=size={width}x{height}:color={color}',
                '-pix_fmt',
                pixel_format,
                '-frames:v',
                '1',
                '-r',
                str(video_fps),
                str(filename)
            ]
            # TODO: We shouldn't do this with a subprocess... it
            # is not a good thing when we want APIs...
            subprocess.run(
                cmd,
                stdout = subprocess.DEVNULL,
                stderr = subprocess.DEVNULL
            )

            ConsolePrinter().print(f'The black cached (transparency={str(transparency)}) frame has been created as "{filename}"')

        # Load decoded frame
        container = av.open(str(filename))
        frame = next(container.decode(video = 0))

        # Store in cache
        BlackFrameCache._cache[key]: 'VideoFrame' = frame

        return frame

class SilentAudioFrameCache:
    """
    A silent audio frames cached generator, useful when we
    need the same silent frames again and again.

    This class will create temporary files (in the WIP folder)
    to load them directly with the pyav library.
    """

    _cache = {}
    """
    The cache that is able to store all the silent frames that
    we create during the process. The frame specifications 
    will be the key to access it in the dict.
    """

    @staticmethod
    def get(
        # TODO: Review the parameter types and that...
        audio_fps: float,
        audio_layout: str,
        audio_format: str,
        audio_samples_per_frame: float
    ):
        """
        Get a silent audio frame with the provided `audio_fps`,
        `audio_layout`, `audio_format` and `audio_samples_per_frame`.

        The audio frames will be cached so the access the
        next time is instantaneous.
        """
        key = (audio_fps, audio_layout, audio_format, audio_samples_per_frame)

        if key in SilentAudioFrameCache._cache:
            return SilentAudioFrameCache._cache[key]

        # Temporary specific file
        filename = f'{CACHE_PREFIX}_silence_{audio_fps}_{audio_layout}_{audio_format}_{audio_samples_per_frame}.wav'
        filename = Temp.get_custom_wip_filename(filename)

        if not Path(filename).exists():
            duration = audio_samples_per_frame / audio_fps

            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'anullsrc=channel_layout={audio_layout}:sample_rate={audio_fps}',
                '-t', str(duration),
                #'-c:a', audio_format,
                # TODO: What about this forced format (?)
                '-c:a', 'pcm_f32le',
                # Apparently this '-frames:a' is stupid and we need the '-t' instead
                #'-frames:a', '1',
                str(filename)
            ]
            # TODO: We should do this with a subprocess... it is
            # not a good thing when we want to create services
            subprocess.run(cmd, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

            ConsolePrinter().print(f'The silent audio cached frame has been created as "{filename}"')

        # Load decoded frame
        container = av.open(str(filename))
        frame = next(container.decode(audio = 0))

        # Store in cache
        SilentAudioFrameCache._cache[key]: 'AudioFrame' = frame

        return frame
