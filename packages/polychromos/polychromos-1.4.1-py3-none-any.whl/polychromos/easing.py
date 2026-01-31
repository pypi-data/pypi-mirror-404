"""
Various easing functions.
"""

import enum
import math
from collections.abc import Callable


class EasingFunctionId(enum.Enum):
    """
    Identifiers for the easing functions.
    """
    NO_EASING = enum.auto()
    EASE_IN_SINE = enum.auto()
    EASE_OUT_SINE = enum.auto()
    EASE_IN_OUT_SINE = enum.auto()
    EASE_IN_QUAD = enum.auto()
    EASE_OUT_QUAD = enum.auto()
    EASE_IN_OUT_QUAD = enum.auto()
    EASE_IN_CUBIC = enum.auto()
    EASE_OUT_CUBIC = enum.auto()
    EASE_IN_OUT_CUBIC = enum.auto()
    EASE_IN_CIRC = enum.auto()
    EASE_OUT_CIRC = enum.auto()
    EASE_IN_OUT_CIRC = enum.auto()
    EASE_IN_EXPO = enum.auto()
    EASE_OUT_EXPO = enum.auto()
    EASE_IN_OUT_EXPO = enum.auto()

def __no_easing(t: float) -> float:
    return t

def __ease_in_sine(t: float) -> float:
    return 1 - math.cos((t * math.pi) / 2)

def __ease_out_sine(t: float) -> float:
    return math.sin((t * math.pi) / 2)

def __ease_in_out_sine(t: float) -> float:
    return -0.5 * (math.cos(math.pi * t) - 1)

def __ease_in_quad(t: float) -> float:
    return t * t

def __ease_out_quad(t: float) -> float:
    return 1 - (1 - t) * (1 - t)

def __ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2 * t * t
    else:
        return 1 - 2 * (1 - t) * (1 - t)

def __ease_in_cubic(t: float) -> float:
    return t**3

def __ease_out_cubic(t: float) -> float:
    return 1 - (1 - t)**3

def __ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4 * t**3
    else:
        return 1 - 4 * (1 - t)**3

def __ease_in_circ(t: float) -> float:
    return 1 - math.sqrt(1 - t * t)

def __ease_out_circ(t: float) -> float:
    return math.sqrt(1 - (t - 1) * (t - 1))

def __ease_in_out_circ(t: float) -> float:
    if t < 0.5:
        return 0.5 * (1 - math.sqrt(1 - 4 * t * t))
    else:
        return 0.5 * (1 + math.sqrt(1 - 4 * (1 - t) * (1 - t)))

def __ease_in_expo(t: float) -> float:
    if t == 0:
        return 0
    return math.pow(2, 10 * (t - 1))

def __ease_out_expo(t: float) -> float:
    if t == 1:
        return 1
    return 1 - math.pow(2, -10 * t)

def __ease_in_out_expo(t: float) -> float:
    if t == 0:
        return 0
    if t == 1:
        return 1
    if t < 0.5:
        return 0.5 * math.pow(2, 20 * t - 10)
    else:
        return 1 - 0.5 * math.pow(2, -20 * t + 10)

def get_easing_function(easing_function_id: EasingFunctionId) -> Callable[[float], float]:
    """
    Gets an easing function.

    :param easing_function_id: The identifier of the easing function to get.
    :type easing_function_id: EasingFunctionId
    :return: The requested easing function.
    :rtype: Callable[[float], float]
    """
    easing_functions: dict[EasingFunctionId, Callable[[float], float]] = {
        EasingFunctionId.NO_EASING: __no_easing,
        EasingFunctionId.EASE_IN_SINE: __ease_in_sine,
        EasingFunctionId.EASE_OUT_SINE: __ease_out_sine,
        EasingFunctionId.EASE_IN_OUT_SINE: __ease_in_out_sine,
        EasingFunctionId.EASE_IN_QUAD: __ease_in_quad,
        EasingFunctionId.EASE_OUT_QUAD: __ease_out_quad,
        EasingFunctionId.EASE_IN_OUT_QUAD: __ease_in_out_quad,
        EasingFunctionId.EASE_IN_CUBIC: __ease_in_cubic,
        EasingFunctionId.EASE_OUT_CUBIC: __ease_out_cubic,
        EasingFunctionId.EASE_IN_OUT_CUBIC: __ease_in_out_cubic,
        EasingFunctionId.EASE_IN_CIRC: __ease_in_circ,
        EasingFunctionId.EASE_OUT_CIRC: __ease_out_circ,
        EasingFunctionId.EASE_IN_OUT_CIRC: __ease_in_out_circ,
        EasingFunctionId.EASE_IN_EXPO: __ease_in_expo,
        EasingFunctionId.EASE_OUT_EXPO: __ease_out_expo,
        EasingFunctionId.EASE_IN_OUT_EXPO: __ease_in_out_expo,
    }
    return easing_functions[easing_function_id]


__all__ = [
    'EasingFunctionId',
    'get_easing_function',
]
