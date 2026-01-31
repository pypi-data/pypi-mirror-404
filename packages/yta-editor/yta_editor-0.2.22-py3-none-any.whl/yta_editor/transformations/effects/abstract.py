from abc import ABC, abstractmethod


class Effect(ABC):
    """
    *Abstract class*

    Class to represent an effect that we will apply in
    a specific time moment, considering the params
    defined for it.

    An effect is something that uses a frame as an input
    and returns another input based on the changes, such
    as: blur, color correction, mask, chroma, etc.
    """

    @abstractmethod
    def _get_params_at(
        self,
        t: float
    ):
        """
        *For internal use only*

        Get the value of the parameters to apply at the given
        `t` time moment.    
        """
        pass

    @abstractmethod
    def apply(
        self,
        frame,
        t: float
    ):
        """
        Apply the effect to the given `frame` for the specific
        `t` time moment.
        """
        pass

class EffectParams(ABC):
    """
    *Abstract class*

    Class to represent the parameters to use when
    applying an effect.
    """

    pass



from dataclasses import dataclass

@dataclass
class EffectInstance:
    """
    *Dataclass*

    Dataclass to include the information about the
    effect we want to apply.
    """

    def __init__(
        self,
        node_graph: 'NodeGraph',
        t_start: float,
        t_end: float,
        # blend_in: float = 0.0,
        # blend_out: float = 0.0
    ):
        self.node_graph: 'NodeGraph' = node_graph
        """
        The node that will be applied.
        """
        self.t_start: float = t_start
        """
        The time moment in which the effect must start
        being applied.
        """
        self.t_end: float = t_end
        """
        The time moment in which the effect must end
        being applied.
        """
