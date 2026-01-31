"""Trust decay functions for temporal trust dynamics.

This module provides various decay functions that model how trust
diminishes over time when not reinforced by new interactions.

Decay functions follow the signature:
    f(initial: float, time_elapsed: float, half_life: float) -> float

Where:
    - initial: The initial trust score (0.0 to 1.0)
    - time_elapsed: Time since last trust update (in days)
    - half_life: Time for trust to decay to half its value (in days)

Example:
    >>> from rotalabs_graph.temporal.decay import exponential_decay, DecayFunction
    >>> # Trust of 0.8 after 30 days with 30-day half-life
    >>> exponential_decay(0.8, 30.0, 30.0)
    0.4
    >>> # Get decay function by type
    >>> decay_fn = get_decay_function(DecayFunction.LINEAR)
    >>> decay_fn(0.9, 15.0, 30.0)
    0.45
"""

from enum import Enum
from typing import Callable
import math


class DecayFunction(str, Enum):
    """Enumeration of available trust decay functions.

    Attributes:
        LINEAR: Trust decreases linearly with time
        EXPONENTIAL: Trust decreases exponentially (most common)
        LOGARITHMIC: Trust decreases slowly at first, then faster
        STEP: Trust drops in discrete steps at fixed intervals
        NONE: Trust does not decay over time

    Example:
        >>> from rotalabs_graph.temporal.decay import DecayFunction
        >>> decay_type = DecayFunction.EXPONENTIAL
        >>> decay_type.value
        'exponential'
    """

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    STEP = "step"
    NONE = "none"


def linear_decay(initial: float, time_elapsed: float, half_life: float) -> float:
    """Linear decay: trust decreases linearly with time.

    Trust decreases at a constant rate until it reaches zero.
    The decay rate is calculated such that trust reaches half
    its initial value at the half-life point.

    Formula: trust = initial * (1 - 0.5 * time_elapsed / half_life)

    Args:
        initial: Initial trust score (0.0 to 1.0)
        time_elapsed: Time since last trust update (days)
        half_life: Time for trust to decay to half its value (days)

    Returns:
        Decayed trust score, clamped to [0.0, initial]

    Example:
        >>> linear_decay(0.8, 0.0, 30.0)  # No time elapsed
        0.8
        >>> linear_decay(0.8, 30.0, 30.0)  # At half-life
        0.4
        >>> linear_decay(0.8, 60.0, 30.0)  # At full decay
        0.0
    """
    if half_life <= 0:
        raise ValueError("half_life must be positive")
    if time_elapsed < 0:
        raise ValueError("time_elapsed cannot be negative")

    # Calculate decay rate such that trust = initial/2 at half_life
    decay_rate = 0.5 / half_life
    decayed = initial * (1.0 - decay_rate * time_elapsed)

    # Clamp to valid range
    return max(0.0, min(initial, decayed))


def exponential_decay(initial: float, time_elapsed: float, half_life: float) -> float:
    """Exponential decay: trust = initial * exp(-lambda * t).

    This is the most common and natural decay model, where trust
    decreases rapidly at first and then more slowly over time.
    The decay constant lambda is derived from the half-life.

    Formula: trust = initial * 2^(-time_elapsed / half_life)

    Args:
        initial: Initial trust score (0.0 to 1.0)
        time_elapsed: Time since last trust update (days)
        half_life: Time for trust to decay to half its value (days)

    Returns:
        Decayed trust score

    Example:
        >>> exponential_decay(0.8, 0.0, 30.0)  # No time elapsed
        0.8
        >>> exponential_decay(0.8, 30.0, 30.0)  # At half-life
        0.4
        >>> exponential_decay(0.8, 60.0, 30.0)  # At two half-lives
        0.2
        >>> exponential_decay(1.0, 90.0, 30.0)  # At three half-lives
        0.125
    """
    if half_life <= 0:
        raise ValueError("half_life must be positive")
    if time_elapsed < 0:
        raise ValueError("time_elapsed cannot be negative")

    # Using the formula: N(t) = N0 * (1/2)^(t/half_life)
    # Equivalent to: N(t) = N0 * exp(-lambda * t) where lambda = ln(2) / half_life
    decay_factor = math.pow(0.5, time_elapsed / half_life)

    return initial * decay_factor


def logarithmic_decay(initial: float, time_elapsed: float, half_life: float) -> float:
    """Logarithmic decay: slower decay for older trust relationships.

    This decay function models trust that is initially resistant to
    decay but eventually degrades. Useful for long-established trust
    relationships that have built up resilience.

    Formula: trust = initial * (1 - log(1 + time_elapsed) / log(1 + 2*half_life))

    Args:
        initial: Initial trust score (0.0 to 1.0)
        time_elapsed: Time since last trust update (days)
        half_life: Approximate time for trust to decay to half (days)

    Returns:
        Decayed trust score, clamped to [0.0, initial]

    Example:
        >>> logarithmic_decay(0.8, 0.0, 30.0)  # No time elapsed
        0.8
        >>> logarithmic_decay(0.8, 30.0, 30.0)  # Around half-life
        0.4...
    """
    if half_life <= 0:
        raise ValueError("half_life must be positive")
    if time_elapsed < 0:
        raise ValueError("time_elapsed cannot be negative")

    if time_elapsed == 0:
        return initial

    # Scale factor to achieve approximately half decay at half_life
    # Using natural log for smoother decay
    scale = math.log(1.0 + 2.0 * half_life)
    decay_factor = math.log(1.0 + time_elapsed) / scale
    decayed = initial * (1.0 - decay_factor)

    return max(0.0, min(initial, decayed))


def step_decay(initial: float, time_elapsed: float, half_life: float) -> float:
    """Step decay: trust drops at fixed intervals.

    Trust remains constant between steps, then drops by a fixed
    percentage at each step interval. Useful for modeling trust
    that degrades in discrete review periods.

    The step interval is half_life/2, with trust dropping by 25%
    at each step.

    Args:
        initial: Initial trust score (0.0 to 1.0)
        time_elapsed: Time since last trust update (days)
        half_life: Time for trust to decay to approximately half (days)

    Returns:
        Decayed trust score

    Example:
        >>> step_decay(0.8, 0.0, 30.0)  # No time elapsed
        0.8
        >>> step_decay(0.8, 14.0, 30.0)  # Before first step (15 days)
        0.8
        >>> step_decay(0.8, 16.0, 30.0)  # After first step
        0.6
        >>> step_decay(0.8, 31.0, 30.0)  # After second step
        0.45
    """
    if half_life <= 0:
        raise ValueError("half_life must be positive")
    if time_elapsed < 0:
        raise ValueError("time_elapsed cannot be negative")

    # Step interval is half of the half-life
    step_interval = half_life / 2.0

    # Number of complete steps
    num_steps = int(time_elapsed / step_interval)

    # Each step reduces trust by 25% (multiplies by 0.75)
    # Two steps approximately halves the trust (0.75^2 = 0.5625)
    decay_factor = math.pow(0.75, num_steps)

    return initial * decay_factor


def no_decay(initial: float, time_elapsed: float, half_life: float) -> float:
    """No decay: trust remains constant over time.

    Use this when trust should not diminish automatically,
    only through explicit updates.

    Args:
        initial: Initial trust score (0.0 to 1.0)
        time_elapsed: Ignored
        half_life: Ignored

    Returns:
        The initial trust score unchanged

    Example:
        >>> no_decay(0.8, 1000.0, 30.0)  # Trust never changes
        0.8
    """
    return initial


# Mapping of decay types to functions
_DECAY_FUNCTIONS: dict[DecayFunction, Callable[[float, float, float], float]] = {
    DecayFunction.LINEAR: linear_decay,
    DecayFunction.EXPONENTIAL: exponential_decay,
    DecayFunction.LOGARITHMIC: logarithmic_decay,
    DecayFunction.STEP: step_decay,
    DecayFunction.NONE: no_decay,
}


def get_decay_function(
    decay_type: DecayFunction | str,
) -> Callable[[float, float, float], float]:
    """Get a decay function by type.

    Args:
        decay_type: The type of decay function to retrieve.
            Can be a DecayFunction enum or a string matching
            one of the decay function names.

    Returns:
        A callable decay function with signature
        (initial, time_elapsed, half_life) -> decayed_trust

    Raises:
        ValueError: If the decay type is not recognized

    Example:
        >>> decay_fn = get_decay_function(DecayFunction.EXPONENTIAL)
        >>> decay_fn(1.0, 30.0, 30.0)
        0.5
        >>> decay_fn = get_decay_function("linear")
        >>> decay_fn(1.0, 30.0, 30.0)
        0.5
    """
    # Convert string to enum if needed
    if isinstance(decay_type, str):
        try:
            decay_type = DecayFunction(decay_type.lower())
        except ValueError:
            valid_types = [d.value for d in DecayFunction]
            raise ValueError(
                f"Unknown decay type: {decay_type}. "
                f"Valid types: {valid_types}"
            )

    if decay_type not in _DECAY_FUNCTIONS:
        raise ValueError(f"Unknown decay type: {decay_type}")

    return _DECAY_FUNCTIONS[decay_type]


def apply_decay(
    initial: float,
    time_elapsed: float,
    half_life: float,
    decay_type: DecayFunction | str = DecayFunction.EXPONENTIAL,
) -> float:
    """Apply trust decay using the specified decay function.

    This is a convenience function that combines get_decay_function
    and function application.

    Args:
        initial: Initial trust score (0.0 to 1.0)
        time_elapsed: Time since last trust update (days)
        half_life: Time for trust to decay to half its value (days)
        decay_type: Type of decay function to use

    Returns:
        Decayed trust score

    Example:
        >>> apply_decay(0.9, 30.0, 30.0, "exponential")
        0.45
        >>> apply_decay(0.9, 30.0, 30.0, DecayFunction.LINEAR)
        0.45
    """
    decay_fn = get_decay_function(decay_type)
    return decay_fn(initial, time_elapsed, half_life)
