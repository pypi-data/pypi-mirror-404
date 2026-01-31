from yta_editor.transformations.effects.abstract import Effect


class AudioEffect(Effect):
    """
    An effect for an audio input.

    This class is just to be able to identify the
    hierarchy and which effect is designed for 
    the audio.
    """

    pass

class AudioEffects:
    """
    A set of effects to apply in an audio input.
    """

    # TODO: This is not as simple as a list, it must be
    # managed with the specific nodes we designed that
    # are able to combine and are time-concerned.

    def __init__(
        self,
        effects: list[AudioEffect] = []
    ):
        self.effects: list[AudioEffect] = effects
        """
        The list of the effects to apply in the audio.
        """

    def apply(
        self,
        frame,
        t: float
    # TODO: Set the type
    ) -> any:
        """
        Apply all the effects that should be applied at the
        given `t` time moment to the provided video `frame`.
        """
        for effect in self.effects:
            frame = effect.apply(
                frame = frame,
                t = t
            )

        return frame