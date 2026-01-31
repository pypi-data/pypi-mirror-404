from yta_math_progression import Progression
from yta_math_easings.enums import EasingFunctionName
from abc import ABC, abstractmethod

import math


class TimeBasedParameter(ABC):
    """
    *Abstract class*

    Class to represent a parameter whose values change
    according to the time moment provided as parameter.
    """

    @abstractmethod
    def get_value_at(
        self,
        # TODO: Maybe a context instead (?)
        t: float
    ):
        """
        Get the value at the `t` time moment provided.
        """
        pass

class ConstantTimeBasedParameter(TimeBasedParameter):
    """
    A parameter based on a specific time moment that
    has always the same value.
    """

    def __init__(
        self,
        value: float
    ):
        self.value: float = value
        """
        The constant value that will be returned every
        time a value is requested.
        """

    def get_value_at(
        self,
        # TODO: Maybe a context instead (?)
        t: float
    ):
        return self.value
    
class EasedTimeBasedParameter(TimeBasedParameter):
    """
    A parameter based on a specific time moment that
    has different values, from `start_value` to
    `end_value`, in the lapse of time defined by the
    `t_start` and the `t_end` time moments provided,
    using the easing function associated to the
    `easing_function_name` provided.

    The `fps` provided are used to be able to get
    all the values for the exact frames we will need.
    """

    def __init__(
        self,
        fps: float,
        start_value: float,
        end_value: float,
        t_start: float,
        t_end: float,
        easing_function_name: EasingFunctionName = EasingFunctionName.LINEAR
    ):
        easing_function_name = EasingFunctionName.to_enum(easing_function_name)

        # TODO: Maybe we should use a context instead
        self.fps: float = fps
        """
        The number of frames per second associated to
        this time function.
        """
        self.t_start: float = t_start
        """
        The time moment in which the linear time function
        should start.
        """
        self.t_end: float = t_end
        """
        The time moment in which the linear time function
        should end.
        """
        self._progression: Progression = Progression(
            start_value = start_value,
            end_value = end_value,
            number_of_values = math.ceil(self.fps * (self.t_end - self.t_start)),
            easing_function_name = easing_function_name
        )
        """
        *For internal use only*

        The internal progression to be able to calculate 
        the values.
        """

    def get_value_at(
        self,
        t: float
    ):
        # TODO: Should we raise exception if 't' is out of bounds (?)
        if t <= self.t_start:
            return self._progression.start_value
        
        if t >= self.t_end:
            return self._progression.end_value
        
        # TODO: The '0.000001' can be avoided with Fraction
        t_local_normalized = (t + 0.000001 - self.t_start) / (self.t_end - self.t_start)

        return self._progression.get_value_from_progress(t_local_normalized)