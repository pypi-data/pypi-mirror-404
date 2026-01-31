import copy
import enum
import math
from xml.etree import ElementTree as ET

from polychromos.color import HSLColor
from polychromos.easing import EasingFunctionId, get_easing_function

HSLColorSequence = list[HSLColor]
HSLColorScale = list[tuple[float, HSLColor]]

class Palette:
    """
    Palette generation and utilities toolkit class.
    """
    class CylindricalInterpolationPath(enum.Enum):
        """
        Enumeration of approaches to cylindrical interpolation.
        """
        SHORTEST = enum.auto()
        LONGEST = enum.auto()
        FORWARD = enum.auto()
        BACKWARD = enum.auto()

    class MixIndexing(enum.Enum):
        """
        The different mix indexing strategies.
        """
        BY_POSITION = enum.auto()
        BY_USE = enum.auto()

    @staticmethod
    def complementary(
        color: HSLColor,
        mute_saturation: float = 0.0,
        mute_lightness: float = 0.0,
    ) -> HSLColor:
        """
        Calculates the complementary color of another color.

        :param color: The original color.
        :type color: HSLColor
        :param mute_saturation: How much to decrease the saturation in absolute terms;
        defaults to 0.0
        :type mute_saturation: float, optional
        :param mute_lightness: How much to decrease the lightness in absolute terms;
        defaults to 0.0
        :type mute_lightness: float, optional
        :return: The complementary color.
        :rtype: HSLColor
        """
        return color.delta(0.5, -mute_saturation, -mute_lightness)

    @staticmethod
    def triadic(
        color: HSLColor,
        mute_saturation: float = 0.0,
        mute_lightness: float = 0.0,
    ) -> tuple[HSLColor, HSLColor]:
        """
        Calculates the triadic color scheme.

        :param color: The original color.
        :type color: HSLColor
        :param mute_saturation: How much to decrease the saturation in absolute terms;
        defaults to 0.0
        :type mute_saturation: float, optional
        :param mute_lightness: How much to decrease the lightness in absolute terms;
        defaults to 0.0
        :type mute_lightness: float, optional
        :return: A tuple with the other two colors of the scheme.
        :rtype: Tuple[HSLColor, HSLColor]
        """
        return (
            color.delta(-1.0/3, -mute_saturation, -mute_lightness),
            color.delta(1.0/3, -mute_saturation, -mute_lightness)
        )

    @staticmethod
    def split_complementary(
        color: HSLColor,
        mute_saturation: float = 0.0,
        mute_lightness: float = 0.0,
    ) -> tuple[HSLColor, HSLColor]:
        """
        Calculates the split complementary color scheme.

        :param color: The original color.
        :type color: HSLColor
        :param mute_saturation: How much to decrease the saturation in absolute terms;
        defaults to 0.0
        :type mute_saturation: float, optional
        :param mute_lightness: How much to decrease the lightness in absolute terms;
        defaults to 0.0
        :type mute_lightness: float, optional
        :return: A tuple with the other two colors of the scheme.
        :rtype: Tuple[HSLColor, HSLColor]
        """
        return (
            color.delta(-5.0/12, -mute_saturation, -mute_lightness),
            color.delta(5.0/12, -mute_saturation, -mute_lightness)
        )

    @staticmethod
    def sequence_from_deltas(
        base_color: HSLColor,
        steps_before: int,
        steps_after: int,
        hue_delta: float,
        saturation_delta: float,
        lightness_delta: float,
    ) -> HSLColorSequence:
        """
        Generates a color sequence from a base color and the step increments of the components.

        :param base_color: The base color.
        :type base_color: HSLColor
        :param steps_before: How many steps to generate before the base color.
        :type steps_before: int
        :param steps_after: How many steps to generate after the base color.
        :type steps_after: int
        :param hue_delta: The hue increment per step, in absolute terms.
        :type hue_delta: float
        :param saturation_delta: The saturation increment per step, in absolute terms.
        :type saturation_delta: float
        :param lightness_delta: The lightness increment per step, in absolute terms.
        :type lightness_delta: float
        :raises ValueError: When a negative number of steps is given.
        :return: The color sequence.
        :rtype: HSLColorSequence
        """
        if steps_before < 0:
            raise ValueError(f'steps_before cannot be a negative number; {steps_before} given')
        if steps_after < 0:
            raise ValueError(f'steps_after cannot be a negative number; {steps_after} given')
        colors: HSLColorSequence = [base_color]
        prev_color: HSLColor = base_color
        for _ in range(steps_before):
            prev_color = prev_color.delta(-hue_delta, -saturation_delta, -lightness_delta)
            colors.append(prev_color)
        colors.reverse()
        prev_color = base_color
        for _ in range(steps_after):
            prev_color = prev_color.delta(hue_delta, saturation_delta, lightness_delta)
            colors.append(prev_color)
        return colors

    @staticmethod
    def __lerp_value(s: float, e: float, x: float) -> float:
        return s + (e - s) * x

    @staticmethod
    def lerp(
        start_color: HSLColor,
        end_color: HSLColor,
        delta: float,
    ) -> HSLColor:
        """
        Linearly interppolates between two colors.

        :param start_color: The starting color.
        :type start_color: HSLColor
        :param end_color: The final color.
        :type end_color: HSLColor
        :param delta: The relative position between the start and the end, in the range [0, 1].
        :type delta: float
        :return: The linearly interpolated color.
        :rtype: HSLColor
        """
        if start_color == end_color:
            return start_color
        def to_cartesian(h: float, s: float) -> tuple[float, float]:
            x: float = math.cos(h * 2 * math.pi) * s
            y: float = math.sin(h * 2 * math.pi) * s
            return (x, y)
        def from_cartesian(x: float, y: float) -> tuple[float, float]:
            s: float = math.sqrt(x * x + y * y)
            if s == 0.0:
                return (0.0, 0.0)
            h: float = math.acos(x / s) / (2 * math.pi)
            if y < 0:
                h = 1.0 - h
            return (h, s)
        start_cartesian: tuple[float, float] = to_cartesian(start_color.hue, start_color.saturation)
        end_cartesian: tuple[float, float] = to_cartesian(end_color.hue, end_color.saturation)
        lerp_cartesian: tuple[float, float] = (
            Palette.__lerp_value(start_cartesian[0], end_cartesian[0], delta),
            Palette.__lerp_value(start_cartesian[1], end_cartesian[1], delta),
        )
        lerp_polar: tuple[float, float] = from_cartesian(lerp_cartesian[0], lerp_cartesian[1])
        return HSLColor(
            lerp_polar[0],
            lerp_polar[1],
            Palette.__lerp_value(start_color.lightness, end_color.lightness, delta),
            Palette.__lerp_value(start_color.opacity, end_color.opacity, delta),
        )

    @staticmethod
    def cylindrical_slerp(
        start_color: HSLColor,
        end_color: HSLColor,
        delta: float,
        path_strategy: CylindricalInterpolationPath,
    ) -> HSLColor:
        """
        Cylindrically interppolates between two colors.

        :param start_color: The starting color.
        :type start_color: HSLColor
        :param end_color: The final color.
        :type end_color: HSLColor
        :param delta: The relative position between the start and the end, in the range [0, 1].
        :type delta: float
        :param path_strategy: The interpolation path strategy.
        Defaults to ``CylindricalInterpolationPath.SHORTEST``
        :type path_strategy: CylindricalInterpolationPath, optional
        :return: The cylindrically interpolated color.
        :rtype: HSLColor
        """
        if start_color == end_color:
            return start_color
        new_hue: float = 0.0
        start_hue: float = start_color.hue
        end_hue: float = end_color.hue
        start_hue_plus_one: float = start_hue + 1.0
        end_hue_plus_one: float = end_hue + 1.0
        if path_strategy == Palette.CylindricalInterpolationPath.SHORTEST:
            if start_hue == end_hue:
                new_hue = start_hue
            elif start_hue < end_hue:
                if abs(end_hue - start_hue) < abs(end_hue - start_hue_plus_one):
                    path_strategy = Palette.CylindricalInterpolationPath.FORWARD
                else:
                    path_strategy = Palette.CylindricalInterpolationPath.BACKWARD
            else:
                if abs(end_hue - start_hue) < abs(end_hue_plus_one - start_hue):
                    path_strategy = Palette.CylindricalInterpolationPath.BACKWARD
                else:
                    path_strategy = Palette.CylindricalInterpolationPath.FORWARD
        elif path_strategy == Palette.CylindricalInterpolationPath.LONGEST:
            if start_hue == end_hue:
                new_hue = (start_hue + delta) % 1.0
            elif start_hue < end_hue:
                if abs(end_hue - start_hue) > abs(end_hue - start_hue_plus_one):
                    path_strategy = Palette.CylindricalInterpolationPath.FORWARD
                else:
                    path_strategy = Palette.CylindricalInterpolationPath.BACKWARD
            else:
                if abs(end_hue - start_hue) >= abs(end_hue_plus_one - start_hue):
                    path_strategy = Palette.CylindricalInterpolationPath.BACKWARD
                else:
                    path_strategy = Palette.CylindricalInterpolationPath.FORWARD

        if path_strategy == Palette.CylindricalInterpolationPath.FORWARD:
            if end_hue > start_hue:
                new_hue = Palette.__lerp_value(start_hue, end_hue, delta)
            else:
                new_hue = Palette.__lerp_value(start_hue, end_hue_plus_one, delta)
        elif path_strategy == Palette.CylindricalInterpolationPath.BACKWARD:
            if end_hue >= start_hue:
                new_hue = Palette.__lerp_value(start_hue_plus_one, end_hue, delta)
            else:
                new_hue = Palette.__lerp_value(start_hue, end_hue, delta)
        return HSLColor(
            new_hue,
            Palette.__lerp_value(start_color.saturation, end_color.saturation, delta),
            Palette.__lerp_value(start_color.lightness, end_color.lightness, delta),
            Palette.__lerp_value(start_color.opacity, end_color.opacity, delta),
        )

    @staticmethod
    def sequence_from_linear_interpolation(
        start_color: HSLColor,
        end_color: HSLColor,
        steps: int,
        open_ended: bool = False,
    ) -> HSLColorSequence:
        """
        Generates a color sequence interpolating linearly between a start and end color.

        Being "linear" in a straight line, if the start and end colors have opposing hues, the
        intermediate colors will become desaturated, passing through the "center" of the
        hue-saturation wheel.

        :param start_color: The starting color.
        :type start_color: HSLColor
        :param end_color: The final color.
        :type end_color: HSLColor
        :param steps: How many steps the sequence should have (min. 2).
        :type steps: int
        :param open_ended: If ``True``, the final color is not included. Defaults to ``False``
        :type open_ended: bool, optional
        :raise ValueError: When a number of steps lower than 2 is given.
        :return: The color sequence
        :rtype: HSLColorSequence
        """
        if steps < 2:
            raise ValueError(f'steps cannot be less than two; {steps} given')
        colors: HSLColorSequence = []
        for i in range(steps - (1 if open_ended else 0)):
            colors.append(
                Palette.lerp(
                    start_color,
                    end_color,
                    i * 1.0 / (steps - 1),
                )
            )
        return colors

    @staticmethod
    def sequence_from_cylindrical_interpolation(
        start_color: HSLColor,
        end_color: HSLColor,
        steps: int,
        path_strategy: CylindricalInterpolationPath = CylindricalInterpolationPath.SHORTEST,
        open_ended: bool = False,
    ) -> HSLColorSequence:
        """
        Generates a color sequence interpolating cylindrically between two given colors.

        In the "cylindrical" interpolation the hue and the saturation are interpolated
        independently, meaning that regardless of the relative hues, no color in the interpolation
        will go nearer to the "center" of the hue-saturation wheel than the less saturated of the
        ends.

        :param start_color: The starting color.
        :type start_color: HSLColor
        :param end_color: The final color.
        :type end_color: HSLColor
        :param steps: How many steps the sequence should have (min. 2)
        :type steps: int
        :param path_strategy: The interpolation path strategy.
        Defaults to ``CylindricalInterpolationPath.SHORTEST``
        :type path_strategy: CylindricalInterpolationPath, optional
        :param open_ended: If ``True`` the final color is not included in the sequence.
        Defaults to ``False``
        :raise ValueError: When a number of steps lower than 2 is given.
        :type open_ended: bool, optional
        :return: The color sequence
        :rtype: HSLColorSequence
        """
        if steps < 2:
            raise ValueError(f'steps cannot be less than two; {steps} given')
        colors: HSLColorSequence = []
        for i in range(steps - (1 if open_ended else 0)):
            colors.append(
                Palette.cylindrical_slerp(
                    start_color,
                    end_color,
                    i * 1.0 / (steps - 1),
                    path_strategy,
                )
            )
        return colors

    @staticmethod
    def sequence_from_elliptical_interpolation(
        start_color: HSLColor,
        end_color: HSLColor,
        steps: int,
        straightening: float = 0.5,
        open_ended: bool = False,
    ) -> HSLColorSequence:
        """
        Generates a color sequence interpolating elliptically between a start and an end color.

        Is a combination between a cylindrical (shortest path) and a linear interpolation.

        :param start_color: The starting color.
        :type start_color: HSLColor
        :param end_color: The final color.
        :type end_color: HSLColor
        :param steps: How many steps the sequence should have (min. 2)
        :type steps: int
        :param straightening: The straightening factor in the range [0, 1]. A factor of 0.0 is
        equivalent to a cylindrical interpolation. A factor of 1.0 is equivalent to a linear
        interpolation. Defaults to 0.5
        :type straightening: float, optional
        :param open_ended: If ``True``, the final color is not included in the sequence.
        Defaults to False
        :type open_ended: bool, optional
        :return: The color sequence.
        :rtype: HSLColorSequence
        """
        straightening = max(min(straightening, 1.0), 0.0)
        linear: HSLColorSequence = Palette.sequence_from_linear_interpolation(
            start_color,
            end_color,
            steps,
            open_ended=open_ended,
        )
        cylindrical: HSLColorSequence = Palette.sequence_from_cylindrical_interpolation(
            start_color,
            end_color,
            steps,
            path_strategy=Palette.CylindricalInterpolationPath.SHORTEST,
            open_ended=open_ended,
        )
        elliptical: HSLColorSequence = [
            Palette.lerp(colors[0], colors[1], straightening)
            for colors in zip(cylindrical, linear, strict=False)
        ]
        return elliptical

    @staticmethod
    def sequence_from_multiple_linear_interpolation(
        colors: HSLColorSequence,
        steps: list[int],
        open_ended: bool = False,
    ) -> HSLColorSequence:
        """
        Generates a color sequence from the linear interpolations between several colors.

        The intermediate colors are the end colors of the previous subsequences and the start colors
        of the next subsequences.

        :param colors: A list of N colors.
        :type colors: HSLColorSequence
        :param steps: A list of N-1 steps for each of the subsequences.
        :type steps: List[int]
        :param open_ended: If ``True`` the last color of the ``colors`` parameter is not included in
        the complete sequence. Defaults to ``False``
        :type open_ended: bool, optional
        :raises ValueError: When the size of the colors and steps lists do not follow a N:N-1 ratio,
        or when an invalid value is passed to one of the subsequences (e.g. a negative number of
        steps)
        :return: The complete sequence.
        :rtype: HSLColorSequence
        """
        if len(steps) != len(colors) - 1:
            raise ValueError(
                f'Length of steps array ({len(steps)}) must be exactly one less than '
                f'the length of colors array ({len(colors)})'
            )

        gradient: HSLColorSequence = []
        for i, partial_steps in enumerate(steps):
            partial_gradient: HSLColorSequence = Palette.sequence_from_linear_interpolation(
                colors[i],
                colors[i + 1],
                partial_steps,
                open_ended=True,
            )
            gradient.extend(partial_gradient)

        if not open_ended:
            gradient.append(colors[len(colors) - 1])

        return gradient

    @staticmethod
    def sequence_from_multiple_cylindrical_interpolation(
        colors: HSLColorSequence,
        steps: list[int],
        strategy: CylindricalInterpolationPath = CylindricalInterpolationPath.SHORTEST,
        open_ended: bool = False,
    ) -> HSLColorSequence:
        """
        Generates a color sequence from the cylindrical interpolations between several colors.

        The intermediate colors are the end colors of the previous subsequences and the start colors
        of the next subsequences.

        :param colors: A list of N colors.
        :type colors: HSLColorSequence
        :param steps: A list of N-1 steps for each of the subsequences.
        :type steps: List[int]
        :param open_ended: If ``True`` the last color of the ``colors`` parameter is not included in
        the complete sequence. Defaults to ``False``
        :type open_ended: bool, optional
        :raises ValueError: When the size of the colors and steps lists do not follow a N:N-1 ratio,
        or when an invalid value is passed to one of the subsequences (e.g. a negative number of
        steps)
        :return: The complete sequence.
        :rtype: HSLColorSequence
        """
        if len(steps) != len(colors) - 1:
            raise ValueError(
                f'Length of steps array ({len(steps)}) must be exactly one less than '
                f'the length of colors array ({len(colors)})'
            )

        gradient: HSLColorSequence = []
        for i, partial_steps in enumerate(steps):
            partial_gradient: HSLColorSequence = Palette.sequence_from_cylindrical_interpolation(
                colors[i],
                colors[i + 1],
                partial_steps,
                path_strategy=strategy,
                open_ended=True,
            )
            gradient.extend(partial_gradient)

        if not open_ended:
            gradient.append(colors[len(colors) - 1])

        return gradient

    @staticmethod
    def sequence_from_multiple_elliptical_interpolation(
        colors: HSLColorSequence,
        steps: list[int],
        straightening: float = 0.5,
        open_ended: bool = False,
    ) -> HSLColorSequence:
        """
        Generates a color sequence from the elliptical interpolations between several colors.

        The intermediate colors are the end colors of the previous subsequences and the start colors
        of the next subsequences.

        :param colors: A list of N colors.
        :type colors: HSLColorSequence
        :param steps: A list of N-1 steps for each of the subsequences.
        :type steps: List[int]
        :param straightening: The straightening factor in the range [0, 1]. A factor of 0.0 is
        equivalent to a cylindrical interpolation. A factor of 1.0 is equivalent to a linear
        interpolation. Defaults to 0.5
        :type straightening: float, optional
        :param open_ended: If ``True`` the last color of the ``colors`` parameter is not included in
        the complete sequence. Defaults to ``False``
        :type open_ended: bool, optional
        :raises ValueError: When the size of the colors and steps lists do not follow a N:N-1 ratio,
        or when an invalid value is passed to one of the subsequences (e.g. a negative number of
        steps)
        :return: The complete sequence.
        :rtype: HSLColorSequence
        """
        if len(steps) != len(colors) - 1:
            raise ValueError(
                f'Length of steps array ({len(steps)}) must be exactly one less than '
                f'the length of colors array ({len(colors)})'
            )

        gradient: HSLColorSequence = []
        for i, partial_steps in enumerate(steps):
            partial_gradient: HSLColorSequence = Palette.sequence_from_elliptical_interpolation(
                colors[i],
                colors[i + 1],
                partial_steps,
                straightening=straightening,
                open_ended=True,
            )
            gradient.extend(partial_gradient)

        if not open_ended:
            gradient.append(colors[len(colors) - 1])

        return gradient

    @staticmethod
    def to_css_hsl_list(colors: HSLColorSequence) -> list[str]:
        """
        Generates a sequence of CSS HSL colors from a sequence of colors.

        :param colors: The original colors sequence.
        :type colors: HSLColorSequence
        :return: The sequence of CSS HSL colors.
        :rtype: List[str]
        """
        return [c.to_css_hsl() for c in colors]

    @staticmethod
    def alternate_colors(colors: HSLColorSequence) -> HSLColorSequence:
        """
        Alternates the colors of the sequence so there is a significant difference between each
        step and its neighbors.

        This assumes the colors in the sequence are ordered somehow (e.g., by hue, by saturation...)
        The shuffling/alternating sequence, for a sequence of N colors, is:
        ``1, N/2+1, 2, N/2+2 ... N/2, N``

        It is particularly useful when the sequence is used to plot categorical data that will be
        placed side-by-side in no particular order.

        :param colors: The original color sequence.
        :type colors: HSLColorSequence
        :return: The new, "shuffled" color sequence.
        :rtype: HSLColorSequence
        """
        old_colors: HSLColorSequence = copy.copy(colors)
        new_colors: HSLColorSequence = []
        flag: bool = False
        for i in range(len(old_colors)):
            new_colors.append(
                old_colors[math.floor(math.ceil(len(old_colors) / 2) + i / 2 if flag else i / 2)]
            )
            flag = not flag
        return new_colors

    @staticmethod
    def to_color_scale(
        colors: HSLColorSequence,
        easing_function: EasingFunctionId = EasingFunctionId.NO_EASING,
    ) -> HSLColorScale:
        """
        Generates a color scale (a sequence of tuples, each with a position in the range [0, 1] and
        a color) from a color sequence, so it can be interpolated linearly as color gradients.

        If colors are to be more concentrated at one (or both) of the scale sequence, easing
        functions can be used.

        :param colors: The color sequence to generate the scale from.
        :type colors: HSLColorSequence
        :param easing_function: An optional easing function. Defaults to
        ``EasingFunctionId.NO_EASING``, meaning the colors of the sequence are distributed evenly
        across the scale.
        :type easing_function: EasingFunctionId, optional
        :raises ValueError: When less than two colors are provided in the sequence.
        :return: The new color scale.
        :rtype: HSLColorScale
        """
        if len(colors) < 2:
            raise ValueError('At least two colors are required to create a scale')
        color_scale: HSLColorScale = []
        position_delta: float = 1.0 / (len(colors) - 1)
        for i, color in enumerate(colors):
            color_scale.append((i * position_delta, color))
        for i, color_stop in enumerate(color_scale):
            color_scale[i] = (get_easing_function(easing_function)(color_stop[0]), color_stop[1])
        return color_scale

    @staticmethod
    def mix_color_sequences(
        col_seq_a: HSLColorSequence,
        col_seq_b: HSLColorSequence,
        selectors: list[bool],
        indexing: MixIndexing = MixIndexing.BY_POSITION,
    ) -> HSLColorSequence:
        """
        Combines two sequences into a single one.

        The resulting sequence will contain as many colors as selectors in the parameter
        ``selectors``, picking colors from the sequence A ``col_seq_a`` or the sequence B
        ``col_seq_b``, depending on the value of each of the selectors.

        :param col_seq_a: The colors to use for the ``False`` selectors.
        :type col_seq_a: HSLColorSequence
        :param col_seq_b: The colors to use for the ``True`` selectors.
        :type col_seq_b: HSLColorSequence
        :param selectors: The list of selectors (``False`` to pick colors from ``col_seq_a``,
        ``True`` to pick colors from ``col_seq_b``).
        :type selectors: List[bool]
        :param indexing: How to pick the colors from the sequences. Picking them by position means
        that the color depends only on the position inside the resulting sequence, cycling,
        regardless of how many times that sequence has been picked colors from. Picking them by use
        means that the colors are picked in order, regardless of the position in the resulting
        sequence. Defaults to MixIndexing.BY_POSITION
        :type indexing: MixIndexing, optional
        :return: A new sequence mixing colors from the other two.
        :rtype: HSLColorSequence
        """
        mixed: HSLColorSequence = []
        a_cur: int = 0
        b_cur: int = 0
        for i, selector in enumerate(selectors):
            if selector:
                mixed.append(col_seq_b[b_cur])
            else:
                mixed.append(col_seq_a[a_cur])

            if indexing == Palette.MixIndexing.BY_POSITION:
                a_cur = i + 1
                b_cur = i + 1
            elif indexing == Palette.MixIndexing.BY_USE:
                if selector:
                    b_cur += 1
                else:
                    a_cur += 1
            a_cur = a_cur % len(col_seq_a)
            b_cur = b_cur % len(col_seq_b)

        return mixed

    @staticmethod
    def concatenate_scales(
        scales: list[HSLColorScale],
        stops: set[float],
    ) -> HSLColorScale:
        """
        Concatenates several scales/gradients.

        Identical duplicate stops are removed. Note that two different colors can still share
        their position (this is, effectively, a step in the gradient).

        :param scales: A list of scales to concatenate (in order; at least two).
        :type scales: List[HSLColorScale]
        :param stops: A set of stops (in the range (0.0, 1.0), not including these; exactly one
        less than the number of scales)
        :type stops: Set[float]
        :raises ValueError: If an incorrect number of scales or stops is given, or a stop outside
        the (0.0, 1.0) excluding range is given.
        :return: The concatenated scale.
        :rtype: HSLColorScale
        """
        if len(scales) < 2:
            raise ValueError(f'At least two scales are required. {len(scales)} given')
        if len(stops) != len(scales) - 1:
            raise ValueError(
                'The number of stops must be exactly one less than the number of scales. '
                f'{len(stops)} given'
            )
        for i, stop in enumerate(stops):
            if stop <= 0.0:
                raise ValueError(f'No stops can be less or equal than 0.0. Stop at {i}: {stop}')
            if stop >= 1.0:
                raise ValueError(f'No stops can be more or equal than 1.0. Stop at {i}: {stop}')

        final_stops = [0.0, *sorted(stops), 1.0]

        concatenated_scale: HSLColorScale = []

        for i, scale in enumerate(scales):
            for scale_stop in scale:
                concatenated_scale.append(
                    (
                        Palette.__lerp_value(final_stops[i], final_stops[i + 1], scale_stop[0]),
                        scale_stop[1],
                    ),
                )

        def stops_are_equal(
            stop1: tuple[float, HSLColor],
            stop2: tuple[float, HSLColor],
        ) -> bool:
            if stop1[0] != stop2[0]:
                return False
            if stop1[1].hue != stop2[1].hue:
                return False
            if stop1[1].saturation != stop2[1].saturation:
                return False
            if stop1[1].lightness != stop2[1].lightness:
                return False
            return stop1[1].opacity == stop2[1].opacity

        i = 0
        while i < len(concatenated_scale) - 1:
            if stops_are_equal(concatenated_scale[i], concatenated_scale[i + 1]):
                concatenated_scale.remove(concatenated_scale[i + 1])
            i += 1

        return concatenated_scale

    @staticmethod
    def scale_lerp(
        scale: HSLColorScale,
        scale_range: tuple[float, float],
        position: float,
    ) -> HSLColor:
        """
        Gets the interpolated color at a given position in a color scale/gradient.

        :param scale: The color scale or gradient.
        :type scale: HSLColorScale
        :param scale_range: The color range (cannot have zero length)
        :type scale_range: Tuple[float, float]
        :param position: The position in the range for the color to interpolate.
        :type position: float
        :raises ValueError: If an invalid parameter is given.
        :return: The interpolated color.
        :rtype: HSLColor
        """
        if scale_range[0] == scale_range[1]:
            raise ValueError('A zero-length range cannot be used')
        if scale_range[0] > scale_range[1]:
            scale_range = (scale_range[1], scale_range[0])

        position = min(max(position, scale_range[0]), scale_range[1])
        normalized_position: float = (position - scale_range[0]) / (scale_range[1] - scale_range[0])

        def binary_search_scale_segment(scale: HSLColorScale, pos: float) -> tuple[int, int]:
            low: int = 0
            high: int = len(scale) - 1

            while low <= high:
                mid: int = (low + high) // 2
                mid_pos: float = scale[mid][0]
                if mid_pos == pos:
                    return mid, mid
                elif mid_pos < pos:
                    low = mid + 1
                else:
                    high = mid - 1

            return high, low

        prev_stop, next_stop = binary_search_scale_segment(scale, normalized_position)
        if prev_stop == next_stop:
            return scale[prev_stop][1]

        prev_pos, prev_col = scale[prev_stop]
        next_pos, next_col = scale[next_stop]

        delta = (normalized_position - prev_pos) / (next_pos - prev_pos)

        return Palette.lerp(prev_col, next_col, delta)

    @staticmethod
    def color_scale_to_svg_linear_gradient(
        color_scale: HSLColorScale,
        gradient_id: str,
        start_pos: tuple[float, float] = (0.0, 0.0),
        end_pos: tuple[float, float] = (1.0, 0.0),
    ) -> str:
        """
        Creates an SVG linear gradient string from a color scale.

        :param color_scale: The color scale for the gradient.
        :type color_scale: HSLColorScale
        :param gradient_id: The id for the gradient.
        :type gradient_id: str
        :param start_pos: The relative starting position. Defaults to (0.0, 0.0) (top-left).
        :type start_pos: Tuple[float, float], optional
        :param end_pos: The relative ending position. Defaults to (1.0, 0.0) (top-right).
        :type end_pos: Tuple[float, float], optional
        :return: A string with the SVG linear gradient.
        :rtype: str
        """
        return ET.tostring(
            Palette.color_scale_to_svg_linear_gradient_etree(
                color_scale,
                gradient_id,
                start_pos,
                end_pos,
            ),
            encoding='unicode',
        )

    @staticmethod
    def color_scale_to_svg_linear_gradient_etree(
        color_scale: HSLColorScale,
        gradient_id: str,
        start_pos: tuple[float, float] = (0.0, 0.0),
        end_pos: tuple[float, float] = (1.0, 0.0),
    ) -> ET.Element:
        """
        Creates an SVG linear gradient Element tree from a color scale.

        :param color_scale: The color scale for the gradient.
        :type color_scale: HSLColorScale
        :param gradient_id: The id for the gradient.
        :type gradient_id: str
        :param start_pos: The relative starting position. Defaults to (0.0, 0.0) (top-left).
        :type start_pos: Tuple[float, float], optional
        :param end_pos: The relative ending position. Defaults to (1.0, 0.0) (top-right).
        :type end_pos: Tuple[float, float], optional
        :return: An XML root element with the SVG linear gradient.
        :rtype: str
        """
        root_element: ET.Element = ET.Element(
            'linearGradient',
            {
                'id': gradient_id,
                'x1': str(start_pos[0]),
                'y1': str(start_pos[1]),
                'x2': str(end_pos[0]),
                'y2': str(end_pos[1]),
            },
        )
        for stop in color_scale:
            stop_element: ET.Element = ET.Element(
                'stop',
                {
                    'offset': f'{stop[0]:.3f}',
                    'stop-color': stop[1].to_css_hex()[:7],
                },
            )
            if stop[1].opacity < 1.0:
                stop_element.set('stop-opacity', f'{stop[1].opacity:.3f}')
            root_element.append(stop_element)
        return root_element

    @staticmethod
    def color_scale_to_plotly(
        color_scale: HSLColorScale,
    ) -> list[tuple[float, str]]:
        """
        Converts a color scale to a format compatible with Plotly.

        :param color_scale: The color scale to convert.
        :type color_scale: HSLColorScale
        :return: The color scale in Plotly format.
        :rtype: List[Tuple[float, str]]
        """
        return [(s[0], s[1].to_css_hex()) for s in color_scale]

    @staticmethod
    def color_scale_to_color_sequence(
        color_scale: HSLColorScale,
        steps: int,
    ) -> HSLColorSequence:
        """
        Generates a new color sequence picking colors in regular intervals from an existing color
        scale.

        :param color_scale: The color scale to pick the colors from.
        :type color_scale: HSLColorScale
        :param steps: The number of colors to pick. At least 2.
        :type steps: int
        :raises ValueError: When a number of steps lesser than 2 is requested.
        :return: The new color sequence.
        :rtype: HSLColorSequence
        """
        if steps < 2:
            raise ValueError(f'At least two steps are required. {steps} given.')

        return [
            Palette.scale_lerp(
                color_scale,
                (0, 1),
                i / (steps - 1),
            )
            for i
            in range(steps)
        ]


__all__ = [
    'Palette',
    'HSLColorSequence',
    'HSLColorScale',
]
