"""
Classes encapsulating colors in different formats.
"""

import colorsys
import copy
import dataclasses
import math
from collections.abc import Iterable
from typing import Literal


@dataclasses.dataclass(slots=True)
class HSLColor:
    """
    A color in HSLA format (Hue, Saturation, Lightness, and optional Alpha).

    These colors are defined in cylindrical coordinates, with hue and saturation being defined in
    polar coordinates (angle φ and radius ρ, respectively), and the lightness in a cartesian
    coordinate.
    """
    __hue: float
    __saturation: float
    __lightness: float
    __opacity: float

    def __init__(
        self,
        hue: float,
        saturation: float,
        lightness: float,
        opacity: float = 1.0,
    ) -> None:
        """
        Initializes a color.

        :param hue: The hue component of the color in the range [0, 1].
        :type hue: float
        :param saturation: The saturation component of the color in the range [0, 1].
        :type saturation: float
        :param lightness: The lightness component of the color in the range [0, 1].
        :type lightness: float
        :param opacity: The optional opacity in the range [0, 1]; defaults to 1.0
        :type opacity: float, optional
        """
        self.hue = hue
        self.saturation = saturation
        self.lightness = lightness
        self.opacity = opacity

    @staticmethod
    def from_abs_hsla(
        abs_hue: int,
        abs_saturation: int,
        abs_lightness: int,
        abs_alpha: int = 100,
    ) -> 'HSLColor':
        """
        Factory method that instantiates a color from its absolute HSL components.

        :param abs_hue: The absolute hue in the range [0, 360]
        :type abs_hue: int
        :param abs_saturation: The absolute saturation in the range [0, 100]
        :type abs_saturation: int
        :param abs_lightness: The absolute lightness in the range [0, 100]
        :type abs_lightness: int
        :param abs_alpha: The absolute opacity in the range [0, 100], defaults to 100
        :type abs_alpha: int, optional
        :return: The new color.
        :rtype: HSLColor
        """
        abs_hue = ((abs_hue % 360) + 360) % 360
        abs_saturation = min(max(abs_saturation, 0), 100)
        abs_lightness = min(max(abs_lightness, 0), 100)
        abs_alpha = min(max(abs_alpha, 0), 100)

        return HSLColor(
            abs_hue / 360.0,
            abs_saturation / 100.0,
            abs_lightness / 100.0,
            abs_alpha / 100.0,
        )

    @staticmethod
    def from_rgba(red: float, green: float, blue: float, alpha: float = 1.0) -> 'HSLColor':
        """
        Factory method that instantiates a color from its decimal RGB or RGBA components.

        :param red: The red component of the color in the range [0, 1].
        :type red: float
        :param green: The green component of the color in the range [0, 1].
        :type green: float
        :param blue: The blue component of the color in the range [0, 1].
        :type blue: float
        :param alpha: The optional alpha component of the color in the range [0, 1]; Defaults to 1.0
        :type alpha: float, optional
        :return: The new color.
        :rtype: HSLColor
        """
        red = min(max(red, 0.0), 1.0)
        green = min(max(green, 0.0), 1.0)
        blue = min(max(blue, 0.0), 1.0)
        alpha = min(max(alpha, 0.0), 1.0)

        hls: tuple[float, float, float] = colorsys.rgb_to_hls(red, green, blue)
        return HSLColor(hls[0], hls[2], hls[1], alpha)

    @staticmethod
    def from_abs_rgba(
        abs_red: int,
        abs_green: int,
        abs_blue: int,
        abs_alpha: int = 255,
    ) -> 'HSLColor':
        """
        Factory method that instantiates a color from its absolute HSL components.

        :param abs_red: The absolute red component in the range [0, 255]
        :type abs_red: int
        :param abs_green: The absolute green component in the range [0, 255]
        :type abs_green: int
        :param abs_blue: The absolute blue component in the range [0, 255]
        :type abs_blue: int
        :param abs_alpha: The absolute alpha component in the range [0, 255], defaults to 255
        :type abs_alpha: int, optional
        :return: The new color.
        :rtype: HSLColor
        """
        abs_red = min(max(abs_red, 0), 255)
        abs_green = min(max(abs_green, 0), 255)
        abs_blue = min(max(abs_blue, 0), 255)
        abs_alpha = min(max(abs_alpha, 0), 255)

        return HSLColor.from_rgba(
            abs_red / 255.0,
            abs_green / 255.0,
            abs_blue / 255.0,
            abs_alpha / 255.0,
        )

    @staticmethod
    def from_hex(hex_color: str) -> 'HSLColor':
        """
        Factory method that instantiates a color from its hexadecimal RGB or RGBA representation.

        :param hex_color: The hexadecimal representation of the color.
        :type hex_color: str
        :raises ValueError: When a non-valid hexadecimal representation is passed.
        :return: The new color.
        :rtype: HSLColor
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = (
                f'{hex_color[0]}{hex_color[0]}'
                f'{hex_color[1]}{hex_color[1]}'
                f'{hex_color[2]}{hex_color[2]}'
            )
        elif len(hex_color) == 4:
            hex_color = (
                f'{hex_color[0]}{hex_color[0]}'
                f'{hex_color[1]}{hex_color[1]}'
                f'{hex_color[2]}{hex_color[2]}'
                f'{hex_color[3]}{hex_color[3]}'
            )
        if len(hex_color) == 6:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return HSLColor.from_abs_rgba(r, g, b, 255)
        elif len(hex_color) == 8:
            r, g, b, a = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
            return HSLColor.from_abs_rgba(r, g, b, a)
        raise ValueError(f'{hex_color} is not a valid color in hexadecimal format')

    @property
    def hue(self) -> float:
        """
        The hue component of the color [0.0, 1.0].
        """
        return self.__hue

    @hue.setter
    def hue(self, hue: float) -> None:
        self.__hue = (hue + int(hue)) % 1.0

    @property
    def saturation(self) -> float:
        """
        The saturation component of the color [0.0, 1.0].
        """
        return self.__saturation

    @saturation.setter
    def saturation(self, saturation: float) -> None:
        self.__saturation = min(max(saturation, 0.0), 1.0)

    @property
    def lightness(self) -> float:
        """
        The lightness component of the color [0.0, 1.0].
        """
        return self.__lightness

    @lightness.setter
    def lightness(self, lightness: float) -> None:
        self.__lightness = min(max(lightness, 0.0), 1.0)

    @property
    def opacity(self) -> float:
        """
        The opacity of the color [0.0, 1.0].
        """
        return self.__opacity

    @opacity.setter
    def opacity(self, opacity: float) -> None:
        self.__opacity = min(max(opacity, 0.0), 1.0)

    @property
    def alpha(self) -> float:
        """
        The opacity of the color [0.0, 1.0].

        Alias of the opacity property.
        """
        return self.opacity

    @alpha.setter
    def alpha(self, alpha: float) -> None:
        self.opacity = min(max(alpha, 0.0), 1.0)

    def delta(
        self,
        hue_delta: float,
        saturation_delta: float,
        lightness_delta: float,
        opacity_delta: float = 0.0,
    ) -> 'HSLColor':
        """
        Obtains a new color by shifting the components of this color.

        :param hue_delta: The increase of the hue component (negative values to decrease).
        :type hue_delta: float
        :param saturation_delta: The increase of the saturation component (negative values to
        decrease).
        :type saturation_delta: float
        :param lightness_delta: The increase of the lightness component (negative values to
        decrease).
        :type lightness_delta: float
        :param opacity_delta: The increase of the opacity component (negative values to
        decrease).
        :type opacity_delta: float
        :return: The resulting shifted color.
        :rtype: HSLColor
        """
        new_color: HSLColor = copy.deepcopy(self)
        new_color.hue = new_color.hue + hue_delta
        new_color.saturation = new_color.saturation + saturation_delta
        new_color.lightness = new_color.lightness + lightness_delta
        new_color.opacity = new_color.opacity + opacity_delta
        return new_color

    def squared_distance(self, another: 'HSLColor') -> float:
        """
        Calculates the squared Euclidean distance in CIELAB color space (Delta E squared).

        This implements the CIE76 Delta E formula (squared), which measures perceptual
        color difference. Only the L, a, b components are used; alpha is ignored.

        This is a convenience method, faster to calculate than the actual Euclidean distance,
        although equally useful to perform distance comparisons.

        :param another: The color to calculate the squared distance to.
        :type another: HSLColor
        :return: The squared Euclidean distance (Delta E² in CIE76)
        :rtype: float
        """
        L1, a1, b1, _ = self.to_lab()
        L2, a2, b2, _ = another.to_lab()

        # Delta E squared (CIE76 formula)
        delta_L = L1 - L2
        delta_a = a1 - a2
        delta_b = b1 - b2

        return delta_L ** 2 + delta_a ** 2 + delta_b ** 2

    def distance(self, another: 'HSLColor') -> float:
        """
        Calculates the Euclidean distance in CIELAB color space (Delta E).

        This implements the CIE76 Delta E formula, which measures perceptual
        color difference. Only the L, a, b components are used; alpha is ignored.

        :param another: The color to calculate the Euclidean distance to.
        :type another: HSLColor
        :return: The Euclidean distance (Delta E in CIE76)
        :rtype: float
        """
        return math.sqrt(self.squared_distance(another))

    def find_closest_color(self, colors: Iterable['HSLColor']) -> 'HSLColor':
        """
        Finds the closest color from a collection using LAB color space distance.

        :param colors: Collection of colors to search
        :type colors: Iterable[HSLColor]
        :return: The color with minimum perceptual distance
        :rtype: HSLColor
        """
        return min(colors, key=lambda c: self.squared_distance(c))

    def multiply_components(
        self,
        saturation_factor: float,
        lightness_factor: float,
    ) -> 'HSLColor':
        """
        Applies multiply blend mode to saturation and lightness components.

        In multiply blending, the result is base * factor. This darkens/mutes the color.
        For example, multiply_components(0.9, 0.5) scales saturation to 90% and lightness to 50%.

        :param saturation_factor: Factor to multiply saturation by (typically in [0.0, 1.0])
        :type saturation_factor: float
        :param lightness_factor: Factor to multiply lightness by (typically in [0.0, 1.0])
        :type lightness_factor: float
        :return: New color with multiplied components
        :rtype: HSLColor
        """
        new_color = copy.deepcopy(self)
        new_color.saturation = new_color.saturation * saturation_factor
        new_color.lightness = new_color.lightness * lightness_factor
        return new_color

    def screen_components(
        self,
        saturation_factor: float,
        lightness_factor: float,
    ) -> 'HSLColor':
        """
        Applies screen blend mode to saturation and lightness components.

        In screen blending, the result is 1 - (1 - base) * (1 - factor). This lightens/brightens.
        Screen is the inverse of multiply and always produces lighter results.

        :param saturation_factor: Factor for screen blending saturation (typically in [0.0, 1.0])
        :type saturation_factor: float
        :param lightness_factor: Factor for screen blending lightness (typically in [0.0, 1.0])
        :type lightness_factor: float
        :return: New color with screened components
        :rtype: HSLColor
        """
        new_color = copy.deepcopy(self)
        new_color.saturation = 1.0 - (1.0 - new_color.saturation) * (1.0 - saturation_factor)
        new_color.lightness = 1.0 - (1.0 - new_color.lightness) * (1.0 - lightness_factor)
        return new_color

    def invert_lightness(self) -> 'HSLColor':
        """
        Inverts the lightness component of the color.

        Dark colors become light, light colors become dark. Hue and saturation remain unchanged.

        :return: New color with inverted lightness
        :rtype: HSLColor
        """
        new_color = copy.deepcopy(self)
        new_color.lightness = 1.0 - new_color.lightness
        return new_color

    def pick_contrasting_color(
        self,
        dark_color: 'HSLColor',
        light_color: 'HSLColor',
        method: Literal['distance', 'lightness', 'auto'] = 'auto',
    ) -> 'HSLColor':
        """
        Picks either a dark or light color based on which contrasts better with this color.

        This is useful for choosing readable text colors on a background, or vice versa.

        :param dark_color: The dark color option
        :type dark_color: HSLColor
        :param light_color: The light color option
        :type light_color: HSLColor
        :param method: Contrast evaluation method:
            - 'distance': Use LAB color space distance (most accurate, slower)
            - 'lightness': Use simple lightness difference (faster, simpler)
            - 'auto': Use both and pick the method that gives better results (default)
        :type method: Literal['distance', 'lightness', 'auto']
        :return: Either dark_color or light_color, whichever contrasts better
        :rtype: HSLColor
        """
        if method == 'distance':
            # Use LAB color space distance for perceptually accurate contrast
            dark_distance = self.squared_distance(dark_color)
            light_distance = self.squared_distance(light_color)
            return dark_color if dark_distance > light_distance else light_color

        elif method == 'lightness':
            # Use simple lightness difference
            dark_diff = abs(self.lightness - dark_color.lightness)
            light_diff = abs(self.lightness - light_color.lightness)
            return dark_color if dark_diff > light_diff else light_color

        else:  # method == 'auto'
            # Try both methods and use the one that gives maximum contrast
            # Calculate contrast using both methods
            dark_distance = self.squared_distance(dark_color)
            light_distance = self.squared_distance(light_color)

            dark_lightness_diff = abs(self.lightness - dark_color.lightness)
            light_lightness_diff = abs(self.lightness - light_color.lightness)

            # Normalize distances to compare them
            # Use the method that shows the clearest winner
            distance_ratio = max(dark_distance, light_distance) / (min(dark_distance, light_distance) + 1e-10)
            lightness_ratio = max(dark_lightness_diff, light_lightness_diff) / (min(dark_lightness_diff, light_lightness_diff) + 1e-10)

            # Use the method with the highest confidence (ratio)
            if distance_ratio >= lightness_ratio:
                return dark_color if dark_distance > light_distance else light_color
            else:
                return dark_color if dark_lightness_diff > light_lightness_diff else light_color

    def to_rgba(self) -> tuple[float, float, float, float]:
        """
        Converts the HSL color to a tuple with the RGBA components in the range [0.0, 1.0].

        :return: A tuple with the RGBA components
        :rtype: tuple[float, float, float, float]
        """
        rgb: tuple[float, float, float] = colorsys.hls_to_rgb(
            self.hue,
            self.lightness,
            self.saturation,
        )
        return (rgb[0], rgb[1], rgb[2], self.opacity)

    def to_abs_rgba(self) -> tuple[int, int, int, int]:
        """
        Converts the HSL color to a tuple with the RGBA components in the range [0, 255].

        :return: A tuple with the RGBA absolute components
        :rtype: tuple[int, int, int, int]
        """
        r, g, b, a = self.to_rgba()
        return (int(r * 255), int(g * 255), int(b * 255), int(a * 255))

    def to_css_hsl(self, legacy: bool = False) -> str:
        """
        Returns this color as an HSL string formatted for CSS3.

        :param legacy: Whether to return the color in legacy format (True) or modern, absolute
        value format (False, default)
        :type legacy: bool
        :return: The color HSL representation for CSS3.
        :rtype: str
        """
        if legacy:
            components = (
                f'{int(self.hue * 360)},{int(self.saturation * 100)}%,{int(self.lightness * 100)}%'
            )
            if self.opacity < 1.0:
                return f'hsla({components},{int(self.opacity * 100)}%)'
            return f'hsl({components})'

        components = (
            f'{int(self.hue * 360)}deg {int(self.saturation * 100)}% {int(self.lightness * 100)}%'
        )
        if self.opacity < 1.0:
            return f'hsl({components} / {int(self.opacity * 100)}%)'
        return f'hsl({components})'

    def to_css_rgb(self) -> str:
        """
        Returns this color as an RGB string formatted for CSS3.

        :return: The color RGB representation for CSS3.
        :rtype: str
        """
        rgba: tuple[float, float, float, float] = self.to_rgba()
        components = (
            f'{rgba[0] * 100:.1f}% {rgba[1] * 100:.1f}% {rgba[2] * 100:.1f}%'
        )
        if self.opacity < 1.0:
            return f'rgb({components} / {rgba[3] * 100:.1f}%)'
        return f'rgb({components})'

    def to_css_hex(self) -> str:
        """
        Returns this color as a hexadecimal string formatted for CSS3.

        :return: The color hex representation for CSS3.
        :rtype: str
        """
        rgba: tuple[float, float, float, float] = self.to_rgba()
        hex_str: str = (
            '#'
            f'{round(rgba[0] * 255):02x}'
            f'{round(rgba[1] * 255):02x}'
            f'{round(rgba[2] * 255):02x}'
        )
        if rgba[3] < 1.0:
            hex_str += f'{round(rgba[3] * 255):02x}'
        return hex_str

    def to_lab(self) -> tuple[float, float, float, float]:
        """
        Converts the HSL color to CIELAB color space (D65 illuminant).

        Returns L (lightness), a (green-red), b (blue-yellow), and alpha.

        :return: A tuple with the LAB components and alpha
        :rtype: tuple[float, float, float, float]
        """
        r, g, b, alpha = self.to_rgba()

        # Step 1: sRGB to linear RGB (inverse gamma correction)
        def srgb_to_linear(c: float) -> float:
            return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92

        r_linear, g_linear, b_linear = map(srgb_to_linear, (r, g, b))

        # Step 2: Linear RGB to XYZ (D65 illuminant)
        x = r_linear * 0.4124564 + g_linear * 0.3575761 + b_linear * 0.1804375
        y = r_linear * 0.2126729 + g_linear * 0.7151522 + b_linear * 0.0721750
        z = r_linear * 0.0193339 + g_linear * 0.1191920 + b_linear * 0.9503041

        # Step 3: XYZ to LAB
        # D65 standard illuminant reference white point
        xn, yn, zn = 0.95047, 1.00000, 1.08883

        # Normalize by reference white
        xr, yr, zr = x / xn, y / yn, z / zn

        # Apply LAB transformation function
        epsilon = 216.0 / 24389.0  # 6^3 / 29^3
        kappa = 24389.0 / 27.0     # 903.3

        def lab_f(t: float) -> float:
            return t ** (1.0/3.0) if t > epsilon else (kappa * t + 16.0) / 116.0

        fx, fy, fz = lab_f(xr), lab_f(yr), lab_f(zr)

        # Calculate LAB values
        L = 116.0 * fy - 16.0
        a = 500.0 * (fx - fy)
        b_lab = 200.0 * (fy - fz)

        return L, a, b_lab, alpha

    def to_ansi_color(self, foreground: bool, bits: Literal[3, 4, 8, 24] = 24) -> str:
        """
        Converts this color to an ANSI escape code.

        :param foreground: Whether this is a foreground (True) or background (False) color
        :type foreground: bool
        :param bits: Color depth - 3 (8 colors), 4 (16 colors), 8 (256 colors), or 24 (true color)
        :type bits: Literal[3, 4, 8, 24]
        :return: ANSI escape code string
        :rtype: str
        """
        if bits not in [3, 4, 8, 24]:
            raise NotImplementedError(f'{bits}-bits terminal colors are not supported')

        if bits == 3:
            return self.__to_ansi_8_color(foreground)
        elif bits == 4:
            return self.__to_ansi_16_color(foreground)
        elif bits == 8:
            return self.__to_ansi_256_color(foreground)

        # 24-bit true color
        r, g, b, _ = self.to_abs_rgba()
        command: str = '38' if foreground else '48'
        return f'\033[{command};2;{r};{g};{b}m'

    def __to_ansi_8_color(self, foreground: bool) -> str:
        """
        Finds the closest 3-bit ANSI color (8 basic colors).

        The 8 basic ANSI colors are: black, red, green, yellow, blue, magenta, cyan, white.

        :param foreground: Whether this is a foreground (True) or background (False) color
        :type foreground: bool
        :return: ANSI escape code for the closest 3-bit color
        :rtype: str
        """
        # 3-bit colors use codes 30-37 (foreground) or 40-47 (background)
        base_code = 30 if foreground else 40

        # 8 basic colors (colors 0-7 from the 256-color palette)
        colors: dict[HSLColor, int] = {
            HSLColor.from_abs_rgba(  0,   0,   0): 0,  # black
            HSLColor.from_abs_rgba(128,   0,   0): 1,  # red
            HSLColor.from_abs_rgba(  0, 128,   0): 2,  # green
            HSLColor.from_abs_rgba(128, 128,   0): 3,  # yellow
            HSLColor.from_abs_rgba(  0,   0, 128): 4,  # blue
            HSLColor.from_abs_rgba(128,   0, 128): 5,  # magenta
            HSLColor.from_abs_rgba(  0, 128, 128): 6,  # cyan
            HSLColor.from_abs_rgba(192, 192, 192): 7,  # white
        }

        closest_color = self.find_closest_color(colors.keys())
        color_code = colors[closest_color]
        return f'\033[{base_code + color_code}m'

    def __to_ansi_16_color(self, foreground: bool) -> str:
        """
        Finds the closest 4-bit ANSI color (16 colors: 8 basic + 8 bright).

        :param foreground: Whether this is a foreground (True) or background (False) color
        :type foreground: bool
        :return: ANSI escape code for the closest 4-bit color
        :rtype: str
        """
        # 4-bit colors: 30-37 (normal) or 90-97 (bright) for foreground
        #               40-47 (normal) or 100-107 (bright) for background

        # 16 colors (colors 0-15 from the 256-color palette)
        colors: dict[HSLColor, tuple[int, bool]] = {
            # Normal colors (30-37 / 40-47)
            HSLColor.from_abs_rgba(  0,   0,   0): (0, False),  # black
            HSLColor.from_abs_rgba(128,   0,   0): (1, False),  # red
            HSLColor.from_abs_rgba(  0, 128,   0): (2, False),  # green
            HSLColor.from_abs_rgba(128, 128,   0): (3, False),  # yellow
            HSLColor.from_abs_rgba(  0,   0, 128): (4, False),  # blue
            HSLColor.from_abs_rgba(128,   0, 128): (5, False),  # magenta
            HSLColor.from_abs_rgba(  0, 128, 128): (6, False),  # cyan
            HSLColor.from_abs_rgba(192, 192, 192): (7, False),  # white
            # Bright colors (90-97 / 100-107)
            HSLColor.from_abs_rgba(128, 128, 128): (0, True),   # bright black (gray)
            HSLColor.from_abs_rgba(255,   0,   0): (1, True),   # bright red
            HSLColor.from_abs_rgba(  0, 255,   0): (2, True),   # bright green
            HSLColor.from_abs_rgba(255, 255,   0): (3, True),   # bright yellow
            HSLColor.from_abs_rgba(  0,   0, 255): (4, True),   # bright blue
            HSLColor.from_abs_rgba(255,   0, 255): (5, True),   # bright magenta
            HSLColor.from_abs_rgba(  0, 255, 255): (6, True),   # bright cyan
            HSLColor.from_abs_rgba(255, 255, 255): (7, True),   # bright white
        }

        closest_color = self.find_closest_color(colors.keys())
        color_code, is_bright = colors[closest_color]

        if is_bright:
            base_code = 90 if foreground else 100
        else:
            base_code = 30 if foreground else 40

        return f'\033[{base_code + color_code}m'

    def __to_ansi_256_color(self, foreground: bool) -> str:
        """
        Finds the closest ANSI 256-color palette color to this color.

        The ANSI 256-color palette consists of:
        - 16 basic colors (0-15)
        - 216 colors in a 6x6x6 RGB cube (16-231)
        - 24 grayscale colors (232-255)

        :param foreground: Whether this is a foreground (True) or background (False) color
        :type foreground: bool
        :return: ANSI escape code for the closest color
        :rtype: str
        """
        command: str = '38' if foreground else '48'

        # Standard ANSI 16 colors (0-15)
        basic_colors: dict[HSLColor, str] = {
            HSLColor.from_abs_rgba(  0,   0,   0): f'\033[{command};5;0m',
            HSLColor.from_abs_rgba(128,   0,   0): f'\033[{command};5;1m',
            HSLColor.from_abs_rgba(  0, 128,   0): f'\033[{command};5;2m',
            HSLColor.from_abs_rgba(128, 128,   0): f'\033[{command};5;3m',
            HSLColor.from_abs_rgba(  0,   0, 128): f'\033[{command};5;4m',
            HSLColor.from_abs_rgba(128,   0, 128): f'\033[{command};5;5m',
            HSLColor.from_abs_rgba(  0, 128, 128): f'\033[{command};5;6m',
            HSLColor.from_abs_rgba(192, 192, 192): f'\033[{command};5;7m',
            HSLColor.from_abs_rgba(128, 128, 128): f'\033[{command};5;8m',
            HSLColor.from_abs_rgba(255,   0,   0): f'\033[{command};5;9m',
            HSLColor.from_abs_rgba(  0, 255,   0): f'\033[{command};5;10m',
            HSLColor.from_abs_rgba(255, 255,   0): f'\033[{command};5;11m',
            HSLColor.from_abs_rgba(  0,   0, 255): f'\033[{command};5;12m',
            HSLColor.from_abs_rgba(255,   0, 255): f'\033[{command};5;13m',
            HSLColor.from_abs_rgba(  0, 255, 255): f'\033[{command};5;14m',
            HSLColor.from_abs_rgba(255, 255, 255): f'\033[{command};5;15m',
        }

        # 6x6x6 RGB color cube (colors 16-231)
        # RGB values: 0, 95, 135, 175, 215, 255
        cube_values = [0, 95, 135, 175, 215, 255]
        cube_colors: dict[HSLColor, str] = {
            HSLColor.from_abs_rgba(cube_values[r], cube_values[g], cube_values[b]):
                f'\033[{command};5;{16 + 36 * r + 6 * g + b}m'
            for r in range(6)
            for g in range(6)
            for b in range(6)
        }

        # Grayscale ramp (colors 232-255): 24 shades from dark to light
        grayscale_colors: dict[HSLColor, str] = {
            HSLColor.from_abs_rgba(8 + level * 10, 8 + level * 10, 8 + level * 10):
                f'\033[{command};5;{232 + level}m'
            for level in range(24)
        }

        # Combine all palettes
        lut: dict[HSLColor, str] = {**basic_colors, **cube_colors, **grayscale_colors}

        # Find and return the closest color
        closest_color = self.find_closest_color(lut.keys())
        return lut[closest_color]

    def __repr__(self) -> str:
        return f'HSLColor({self.hue}, {self.saturation}, {self.lightness}, {self.opacity})'

    def __hash__(self) -> int:
        return hash(self.hue + 2 * self.saturation + 4 * self.lightness + 8 * self.opacity)


__all__ = [
    'HSLColor',
]
