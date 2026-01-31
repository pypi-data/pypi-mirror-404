# Polychromos

> **πολύχρωμος**
>
> _Greek; adjective_
>
> From **πολύ-** ("many", "much") and **-χρωμος** (from **χρῶμα**, "color").
>
> Multicolored.

Color and palette utility library.

This library provides a set of utilites to handle colors and palettes from an artistic approach,
using color theory and the more human-friendly hue-saturation-lightness components.

## Modules

The library provides three modules:

- `color`, containing the `HSLColor` class, encapsulating a single color in HSL(A) format.
  - `web`, a submodule containing the standard web colors.
- `palette`, with the `HSLColorSequence` type (an alias for a list of `HSLColor`s) and the
  `Palette` class with utility functions to generate and handle sets of colors.
- `easing`, with the easing functions and their IDs, useful when generating color scales.

The main classes can be imported directly from the package root:

```python
from polychromos import HSLColor, Palette
```

Or from their respective modules (as shown in the examples below):

```python
from polychromos.color import HSLColor
from polychromos.palette import Palette
```

## Color fundamentals

Colors in **polychromos** are defined through the HSLA components: hue, saturation, lightness and
alpha/opacity. This is an approach more intuitive to humans, specially to artists and designers.
This is why this library favors this approach.

Colors using these components exist in a cylindrical coordinates space:

- The hue is the angle of a semiplane containing both the color and the cylinder axis, and the
  semiplane representing the hue (0deg angle) containing the cylinder axis. This component is
  cyclical, meaning once its value passes its maximum value (360deg), it "starts" again at 0deg.
- The hue is the distance between the color and the cylinder axis. Colors at the cylinder axis
  (0% saturation) have no chromacity and look gray.
- The lightness is the position of the circle containing the color across the cylinder axis. A
  lightness of 50% is the pure color based on its chromacity and intensity. Values above 50% are
  brighter, and below 50% darker, being 100% and 0% pure white and pure black respectively.
- Alpha, the last component, represents the opacity of the color and is defined outside the
  reference cylindrical coordinate system.

For an artist it is more intuitive to manipulate each of these components separately, instead of
changing the red, green, blue and alpha components to get the exact color they look for.

To define a color in **polychromos**, the following options are implemented:

```python
from polychromos.color import HSLColor

color: HSLColor

# Default construction format: each component in the range [0,.0, 1.0]
color = HSLColor(0.25, 0.85, 0.45) # hsl(90deg 85% 45%)
color = HSLColor(0.25, 0.85, 0.45, 0.6) # hsla(90deg 85% 45% / 60%)

# From absolute HSLA components: hue [0, 360], sat [0, 100], light [0, 100], alpha [0, 100]
color = HSLColor.from_abs_hsla(90, 85, 45)
color = HSLColor.from_abs_hsla(90, 85, 45, 60)

# From RGBA components: each component in the range [0.0, 1.0]
color = HSLColor.from_rgba(0.51, 0.75, 0.1)
color = HSLColor.from_rgba(0.51, 0.75, 0.1, 1.0)

# From absolute RGBA components: each component in the range [0, 255]
color = HSLColor.from_abs_rgba(0x78, 0xac, 0x19)
color = HSLColor.from_abs_rgba(0x78, 0xac, 0x19, 0xff)

# From CSS hexadecimal notation: #RGB, #RGBA, #RRGGBB, #RRGGBBAA
color = HSLColor.from_hex('#78ac19')
color = HSLColor.from_hex('#78ac19ff')
```

HSLA components can be read and written directly, and their values are in the [0.0, 1.0] range.

```python
color.hue = 0.7
color.saturation = 0.95
color.lightness = 0.5
color.opacity = 0.35
color.alpha = 0.35 # Alias of opacity as a convenience for those used to name it alpha instead.
```

A new color can be obtained relative to another applying an absolute shift:

```python
new_color = color.delta(0.02, -0.1, 0.05) # Shift hue 7.2deg, muted by 10%, and brightened 5%.
```

To use them for the web, a convenience method exports the color to CSS3 HSL and RGB format:

```python
color = HSLColor(0.25, 0.85, 0.45)
color.to_css_hsl() # hsl(90deg 85% 45%)
color.to_css_hsl(legacy=True) # hsl(90, 85%, 45%)
color.to_css_rgb()
```

(note the legacy format is discouraged, but some software like Plotly still uses it, so it is
included for that reason).

Web colors can be used by their name (case insensitive):

```python
from polychromos.color.web import get_web_color

color: HSLColor = get_web_color('Crimson')
```

## Color transformations and blend modes

**Polychromos** provides several convenience methods for transforming colors using blend modes:

### Multiply and Screen blend modes

The `multiply_components` and `screen_components` methods apply blend modes to saturation and
lightness components, useful for creating darker/lighter variants:

```python
base_color = HSLColor.from_abs_hsla(200, 80, 60)

# Multiply: darkens and mutes (result = base * factor)
darker = base_color.multiply_components(0.8, 0.5)  # 80% saturation, 50% lightness

# Screen: lightens and brightens (result = 1 - (1 - base) * (1 - factor))
lighter = base_color.screen_components(0.7, 0.8)  # Brighter variant
```

### Lightness inversion

Invert the lightness while preserving hue and saturation:

```python
dark_color = HSLColor.from_abs_hsla(0, 80, 30)
light_version = dark_color.invert_lightness()  # Lightness becomes 70%
```

### Picking contrasting colors

Choose between a dark or light color based on which contrasts better with the current color:

```python
background = HSLColor.from_abs_hsla(200, 70, 50)
dark_text = HSLColor.from_abs_hsla(0, 0, 10)
light_text = HSLColor.from_abs_hsla(0, 0, 95)

# Automatically pick the best contrasting color
text_color = background.pick_contrasting_color(dark_text, light_text, method='auto')
# Methods: 'distance' (LAB color space), 'lightness' (simple), 'auto' (intelligent)
```

This is particularly useful for ensuring readable text on colored backgrounds.

## Perceptual color distance and comparison

Colors can be compared using perceptually accurate CIELAB color space distance:

```python
color1 = HSLColor.from_hex('#ff0000')
color2 = HSLColor.from_hex('#00ff00')

# Calculate perceptual distance (CIE76 Delta E)
distance_squared = color1.squared_distance(color2)  # Faster, for comparisons
distance = color1.distance(color2)  # Euclidean distance in LAB space

# Find the closest color from a collection
colors = [red, green, blue, yellow, cyan, magenta]
closest = my_color.find_closest_color(colors)
```

The LAB color space conversion accounts for human perception, making distance calculations more
accurate than simple RGB Euclidean distance.

## Color harmony

Color harmony schemes set a framework to obtain colors related to other colors in a chromatically
appealing and balanced way. All of these schemes refer to the hue component explicitly.

The first and most basic schemes (primary, secondary and tertiary) refer to the basic pieces to
split a chromatic space into.

There are other more elaborate schemes. **Polychromos** provides the following three:

- Complementary color: A color chromatically opposite (shifted 180deg) to a given color.
- Triadic colors: Two colors that, along the reference color, form an equilateral triangle. That
  is, each color hue is shifted 120deg from the other two.
- Split complementary colors: Two colors halfway between the complementary color and the triadic
  colors of the reference color (i.e., shifted 150deg clocwise and counter-clockwise from the
  reference color in the chromatic wheel).

These methods allow to optionally change the saturation and lightness by a given delta, if desired,
for convenience when building color schemes using these harmonies.

```python
from polychromos.color import HSLColor
from polychromos.palette import Palette

ref_color: HSLColor = HSLColor(0.25, 1.0, 0.5) # hsl(90, 100%, 50%)

complementary_color: HSLColor
complementary_color = Palette.complementary(ref_color)
complementary_color = Palette.complementary(ref_color, mute_saturation=0.3) # 30% less saturated
complementary_color = Palette.complementary(ref_color, mute_lightness=0.2) # 20% darker
complementary_color = Palette.complementary(ref_color, mute_lightness=-0.15) # 15% brighter

triadic_color_1: HSLColor
triadic_color_2: HSLColor
(triadic_color_1, triadic_color_2) = Palette.triadic(ref_color)
(triadic_color_1, triadic_color_2) = Palette.triadic(ref_color, mute_saturation=0.3) # 30% less sat
(triadic_color_1, triadic_color_2) = Palette.triadic(ref_color, mute_lightness=0.2) # 20% darker
(triadic_color_1, triadic_color_2) = Palette.triadic(ref_color, mute_lightness=-0.15) # 15% brighter

split_comp_color_1: HSLColor
split_comp_color_2: HSLColor
(triadic_color_1, triadic_color_2) = Palette.triadic(ref_color)
(triadic_color_1, triadic_color_2) = Palette.triadic(ref_color, mute_saturation=0.3) # 30% less sat
(triadic_color_1, triadic_color_2) = Palette.triadic(ref_color, mute_lightness=0.2) # 20% darker
(triadic_color_1, triadic_color_2) = Palette.triadic(ref_color, mute_lightness=-0.15) # 15% brighter
```

There are other color harmony schemes like the tetradic or rectangular, that are not provided with
this software. The analogous colors scheme is not implemented as such, but can be obtained easily
by constructing a color sequence from a reference color as shown in the next section.

## Color sequences

**Polychromos** `Palette` contains a series of facilites to build color sequences: lists of
colors in HSL format. These facilities can be divided in two subtypes: those that build from a
single reference color and those that build from two or more colors.

### Based on a reference color

The first kind use a reference color and deltas for each component, obtaining a shifted color for
each of the steps based on the previous color (starting with the reference color). This is done
with the method `sequence_from_deltas`:

```python
from polychromos.color import HSLColor
from polychromos.palette import Palette, HSLColorSequence

ref_color: HSLColor = HSLColor(0.25, 1.0, 0.5) # hsl(90, 100%, 50%)

new_sequence: HSLColorSequence = Palette.sequence_from_deltas(
    ref_color,
    3, # Three steps before
    3, # Three steps after
    0.025, # 9deg hue shift per step (backwards in the steps before, forwards in the steps after)
    0.0, # No saturation shift
    -0.05, # -5% lightness shift per step (brighter before, darker after)
)
```

In the example above, a sequence of seven colors (three before, the reference color, and three
after) is built, calculated as a gradient in both the hue and lightness components, with a constant
saturation.

As a special case, the analogous color harmony scheme can be obtained with this function:

```python
analogous_colors: HSLColorSequence = Palette.sequence_from_deltas(
    ref_color,
    2,
    2,
    15.0 / 360.0,
    0.0,
    0.0,
)
```

### Based on two or more colors

The second kind of color sequences are defined by interpolating between colors.

There are two kinds of color interpolations implemented in **polychromos**:

- Linear interpolation (lerp): Colors from the cylindrical coordinate system are projected onto a
  cartesian coordinate system, tracing a linear segment between both colors, and obtaining a color
  of that segment in a relative distance from start (0.0) to end (1.0). When the starting and final
  colors are opposing in hue, the middle colors are desaturated or even gray (e.g., red-gray-cyan).
- Cylindrical "spherical" interpolation (cylindrical slerp): Colors are interpolated linearly in
  the cylindrical coordinate space, meaning each HSLA component is interpolated separately. In this
  case, intermediate color saturations will not be outside the minimum and maximum saturations of
  the starting and final colors (e.g., red-yellow-green-cyan).

  In this interpolation, as there are two paths to go from the starting hue to the final hue, one
  of four interpolation path strategies must be chosen: always forward in the wheel(e.g.
  red-yellow-green, red-yellow-green-cyan-blue), always backwards (e.g.,
  red-magenta-blue-cyan-green, red-magenta-blue), shortes path (e.g., red-yellow-green,
  red-magenta-blue), or longest path (e.g., red-magenta-blue-cyan-green,
  red-yellow-green-cyan-blue).

The library provides two interpolation functions:

```python
from polychromos.color import HSLColor
from polychromos.palette import Palette, HSLColorSequence

red: HSLColor = HSLColor.from_abs_hsla(0, 100, 50)
yellow: HSLColor = HSLColor.from_abs_hsla(60, 100, 50)
green: HSLColor = HSLColor.from_abs_hsla(120, 100, 50)
cyan: HSLColor = HSLColor.from_abs_hsla(180, 100, 50)
blue: HSLColor = HSLColor.from_abs_hsla(240, 100, 50)
magenta: HSLColor = HSLColor.from_abs_hsla(300, 100, 50)

Palette.lerp(red, cyan, 0.4) # Reddish gray
Palette.lerp(red, cyan, 0.6) # Cyanish gray

Palette.cylindrical_slerp(red, green, 0.5) # Yellow; shortest path by default
Palette.cylindrical_slerp(red, blue, 0.5) # Magenta; shortest path by default
```

For convenience, methods to construct the whole sequenece using interpolation are implemented as
well, given the colors and a number of steps in the sequence:

```python
# Red, reddish gray, gray, cyanish gray, cyan
Palette.sequence_from_linear_interpolation(red, cyan, 5)

# Red, yellow, green
Palette.sequence_from_cylindrical_interpolation(
  red, green, 3,
  path_strategy=Palette.CylindricalInterpolationPath.FORWARD,
)
# Red, yellow, green, cyan, blue
Palette.sequence_from_cylindrical_interpolation(
  red, green, 5,
  path_strategy=Palette.CylindricalInterpolationPath.FORWARD,
)
# Red, magenta, blue, cyan, green
Palette.sequence_from_cylindrical_interpolation(
  red, green, 5,
  path_strategy=Palette.CylindricalInterpolationPath.BACKWARD,
)
# Red, magenta, blue
Palette.sequence_from_cylindrical_interpolation(
  red, green, 3,
  path_strategy=Palette.CylindricalInterpolationPath.BACKWARD,
)
# Red, yellow, green
Palette.sequence_from_cylindrical_interpolation(
  red, green, 3,
  path_strategy=Palette.CylindricalInterpolationPath.SHORTEST,
)
# Red, magenta, blue
Palette.sequence_from_cylindrical_interpolation(
  red, green, 3,
  path_strategy=Palette.CylindricalInterpolationPath.SHORTEST,
)
# Red, magenta, blue, cyan, green
Palette.sequence_from_cylindrical_interpolation(
  red, green, 5,
  path_strategy=Palette.CylindricalInterpolationPath.LONGEST,
)
# Red, yellow, green, cyan, blue
Palette.sequence_from_cylindrical_interpolation(
  red, green, 5,
  path_strategy=Palette.CylindricalInterpolationPath.LONGEST,
)
```

There is an hybrid approach to build these sequences as well: the elliptical interpolation. It is
an intermediate point between the linear and cylindrical interpolations, with each color being
interpolated between the linear and the cylindrical interpolations by a `straightening` factor,
where `0.0` means purely cylindrical interpolation, and `1.0` a purely linear interpolation. This
is recommended when the linear interpolation is too harsly muted and the cylindrical interpolation
is too vivid.

These sequence factory methods accept another parameter, `open_ended`, boolean and `False` by
default, to prevent the factory to include the final color in the sequence. This is useful to
concatenate sequences where the final color of the current is the starting color of the next.

For this reason a variation of each of the previous sequence factories is provided as well:
`sequence_from_multiple_linear_interpolation`, `sequence_from_multiple_cylindrical_interpolation`
and `sequence_from_multiple_elliptical_interpolation`. These methods, instead of a starting color,
a final color and a number of steps, receive a list of N colors and a list of N-1 steps to
construct a sequence comprised of N-1 subsequences. For each subsequence a color and the next color
are selected as the start and end of a subsequence of the number of steps given in the second list.

```python
# Red, orange, yellow
#              yellow, green, cyan, blue
# --------------------------------------
# Red, orange, yellow, green, cyan, blue
Palette.sequence_from_multiple_cylindrical_interpolation(
  colors=[red, yellow, blue],
  steps=[3, 4],
)

# Red, muted yellow, green
#                    green, muted cyan, blue
#                                       blue, muted magenta, red
# --------------------------------------------------------------
# Red, muted yellow, green, muted cyan, blue, muted magenta, red
Palette.sequence_from_multiple_linear_interpolation(
  colors=[red, green, blue, red],
  steps=[3, 3, 3],
)
```

## Shuffling for unordered categorical data

As the colors in the sequences generated by this library are sometimes too similar to their
neighbors, they may be not suitable to place them side-by-side in a plot, for instance.

A method `alternate_colors` is provided by the `Palette` class for this purpose. It alternates
the colors in the sequence, "shuffling" it so no color is too similar to its neighbors (relatively)

This splits the sequence in two halves, picking one color from each in alternating order. For
instance, for a sequence of N colors, the resulting sequence is: `1, N/2+1, 2, N/2+2 ... N/2, N`

## Mixing sequences

Sometimes is useful to generate a sequence by picking colors from two different color sequences.
For instance, when plotting a set of categorical data where two different sets of categories are
to be colored differently.

The method `Palette.mix_color_sequences` does exactly this. It takes two sequences to pick the
colors from (sequence A and sequence B), and a list of "selectors" that determine which of the
sequences to pick the colors from, depending on the selector value.

The resulting sequence will have the same size as the list of selectors. For each of the entries
in the sequence, it will pick a color from sequence A if the selector is `False`, or from sequence
B if the selector is `True`.

The color from each sequence can be picked in one of these ways:

- By position: the color picked matches the position of the element in the resulting sequence.
- By use: colors are picked iteratively from each sequence separately (e.g., it will pick the third
  color if two colors were previously picked from that sequence).

If the color to pick is outside the bounds of the length of the source sequence, it will start over
again.

```python
col_seq_a: HSLColorSequence = [
    get_web_color('silver'),
    get_web_color('gray'),
]
col_seq_b: HSLColorSequence = [
    colors['crimson'],
    colors['gold'],
    colors['seagreen'],
]

# Selector: False   , True    , True    , False   , True    , False   , True    , False
# Index A:  0       , 1       , 0       , 1       , 0       , 1       , 0       , 1
# Index B:  0       , 1       , 2       , 0       , 1       , 2       , 0       , 1
# Color:    silver  , gold    , seagreen, gray    , gold    , gray    , crimson , gray
Palette.mix_color_sequences(
    col_seq_a,
    col_seq_b,
    [False, True, True, False, True, False, True, False],
    indexing=Palette.MixIndexing.BY_POSITION,
)
# Selector: False   , True    , True    , False   , True    , False   , True    , False
# Index A:  0       , 1       , 1       , 1       , 0       , 0       , 1       , 1
# Index B:  0       , 0       , 1       , 2       , 2       , 0       , 0       , 1
# Color:    silver  , crimson , gold    , gray    , seagreen, silver  , crimson , gray
Palette.mix_color_sequences(
    col_seq_a,
    col_seq_b,
    [False, True, True, False, True, False, True, False],
    indexing=Palette.MixIndexing.BY_USE,
)
```

## Color scales

For some uses, discrete color steps are not enough and continuous color scales are required.

The class `Palette` provides a method `to_color_scale`, that maps a color sequence to a color
scale, a list of tuples with the first element of each being a relative position in the scale
(rank [0.0, 1.0]), and the second element the corresponding color in the sequence.

This method supports easing, when colors should be more concentrated at the start, at the end,
both, or evenly distributed (i.e., no easing; the default behavior).

```python
from polychromos.color import HSLColor
from polychromos.palette import Palette, HSLColorSequence, HSLColorGradient
from polychromos.easing import EasingFunctionId, get_easing_function

danger: HSLColor = HSColor.from_abs_hsla(335, 70, 50)
warning: HSLColor = HSColor.from_abs_hsla(45, 100, 50)
fine: HSLColor = HSColor.from_abs_hsla(150, 70, 30)

semaphore: HSLColorSequence = Palette.sequence_from_multiple_cylindrical_interpolation(
  colors=[danger, warning, fine],
  steps=[4, 4],
)

# Semaphore color scale, with colors more concentrated at the ends than the middle area.
semaphore_scale: HSLColorScale = Palette.to_color_scale(
  semaphore,
  get_easing_function(EasingFunctionId.EASE_IN_OUT_QUAD),
)
```

### Color scales concatenation

Color scales can be concatenated together into a new color scale.

To do so, the concatenation method uses a list of color scales (two at least) and the position of
each stitching point in the new scale (as many as the number of scales minus one).

```python
# Creates a new color scale by concatenating three scales:
# - color_scale_1 in the range [0.0, 0.25]
# - color scale_2 in the range (0.25, 0.5]
# - color_scale_3 in the range (0.5, 1.0]
combined_scale: HSLColorScale = Palette.concatenate_scales(
  [color_scale_1, color_scale_2, color_scale_3],
  [0.25, 0.5]
)
```

### Picking colors from color scales

Colors can be picked from color scales using the method `Palette.scale_lerp`. This method takes a
color scale, a range (a minimum and a maximum values mapping the start and end of the color scale),
and an absolute position in the given range.

The reason to map the scale to a different range is to make it easier to use for data
visualization.

This color is picked by applying a linear interpolation inside of the appropriate scale segment.

```python
picked_color: HSLColor = Palette.scale_lerp(
  color_scale,
  (10.0, 45.5),
  32.6,
)
```

### Converting color scales to other formats

Some helper functions allow to convert color scales to formats suitable for other applications and
uses.

#### SVG

A color scale can be converted to SVG linear gradients using the following methods:

```python
from xml.etree import ElementTree as ET
color_scale_as_string: str = Palette.color_scale_to_svg_linear_gradient(
  color_scale=color_scale,
  gradient_id='color-scale-id', # XML id attribute for the gradient
  start_pos=(0.0, 0.0), # top-left
  end_pos=(1.0, 0.0), # top-right
)
color_scale_as_elements_tree: ET.Element = Palette.color_scale_to_svg_linear_gradient_etree(
  color_scale=color_scale,
  gradient_id='color-scale-id', # XML id attribute for the gradient
  start_pos=(0.0, 0.0), # top-left
  end_pos=(1.0, 0.0), # top-right
)
```

#### Plotly

To use the color scales for Plotly (e.g., for bar charts colored by value), use the method below:

```python
color_scale_for_plotly: List[Tuple[float, str]] = Palette.color_scale_to_plotly(color_scale)
```

#### Terminal colors (ANSI escape codes)

Convert any color to ANSI terminal escape codes at various bit depths:

```python
color = HSLColor.from_abs_rgba(220, 100, 50)

# 3-bit: 8 basic colors (black, red, green, yellow, blue, magenta, cyan, white)
ansi_3bit = color.to_ansi_color(foreground=True, bits=3)

# 4-bit: 16 colors (8 basic + 8 bright variants)
ansi_4bit = color.to_ansi_color(foreground=True, bits=4)

# 8-bit: 256 colors (full palette)
ansi_8bit = color.to_ansi_color(foreground=True, bits=8)

# 24-bit: True color (16.7 million colors)
ansi_24bit = color.to_ansi_color(foreground=True, bits=24)

# Use for colored terminal output
print(f'{ansi_24bit}Colored text\033[0m')
```

The library uses perceptual LAB color space distance to find the closest palette color for 3-bit,
4-bit, and 8-bit modes, ensuring the best possible color approximation.

### Color sequences from color scales

Once color scales are built, color sequences can be extracted from them by picking colors in
regular intervals.

```python
sequence_4: HSLColorSequence = Palette.color_scale_to_color_sequence(color_scale, 4)
sequence_15: HSLColorSequence = Palette.color_scale_to_color_sequence(color_scale, 15)
```

This method is recommended when a new sequence needs to be constructed from an existing one, but
varying the number of total steps, specially when the original was built from several subsequences
using different interpolation methods.

## License

This project is licensed under the MIT license.
