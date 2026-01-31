from __future__ import annotations
import collections.abc
import numpy
import numpy.typing
import typing

__all__: list[str] = [
    "Circle",
    "Color",
    "Path",
    "Polygon",
    "Polyline",
    "Rect",
    "SVG",
    "Text",
    "add",
]

class Circle:
    def __copy__(self, arg0: dict) -> Circle:
        """
        Create a shallow copy of the Circle object
        """
    def __deepcopy__(self, memo: dict) -> Circle:
        """
        Create a deep copy of the Circle object
        """
    def __init__(
        self,
        center: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"],
        r: typing.SupportsFloat = 1.0,
    ) -> None:
        """
        Initialize Circle with center point and radius
        """
    @typing.overload
    def attrs(self) -> str: ...
    @typing.overload
    def attrs(self, arg0: str) -> Circle: ...
    @typing.overload
    def center(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 1]"]:
        """
        Get the center of the Circle
        """
    @typing.overload
    def center(
        self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]
    ) -> Circle:
        """
        Set the center of the Circle
        """
    def clone(self) -> Circle:
        """
        Create a deep copy of the Circle object
        """
    @typing.overload
    def dash_array(self) -> str: ...
    @typing.overload
    def dash_array(self, arg0: str) -> Circle: ...
    @typing.overload
    def fill(self) -> Color: ...
    @typing.overload
    def fill(self, arg0: Color) -> Circle: ...
    @typing.overload
    def r(self) -> float: ...
    @typing.overload
    def r(self, arg0: typing.SupportsFloat) -> Circle: ...
    @typing.overload
    def stroke(self) -> Color: ...
    @typing.overload
    def stroke(self, arg0: Color) -> Circle: ...
    @typing.overload
    def stroke_linecap(self) -> str: ...
    @typing.overload
    def stroke_linecap(self, arg0: str) -> Circle: ...
    @typing.overload
    def stroke_linejoin(self) -> str: ...
    @typing.overload
    def stroke_linejoin(self, arg0: str) -> Circle: ...
    @typing.overload
    def stroke_width(self) -> float: ...
    @typing.overload
    def stroke_width(self, arg0: typing.SupportsFloat) -> Circle: ...
    def to_string(self) -> str:
        """
        Convert Circle to SVG string representation
        """
    @typing.overload
    def transform(self) -> str: ...
    @typing.overload
    def transform(self, arg0: str) -> Circle: ...
    @typing.overload
    def x(self) -> float: ...
    @typing.overload
    def x(self, arg0: typing.SupportsFloat) -> Circle: ...
    @typing.overload
    def y(self) -> float: ...
    @typing.overload
    def y(self, arg0: typing.SupportsFloat) -> Circle: ...

class Color:
    @staticmethod
    def parse(arg0: str) -> Color:
        """
        Parse a color from a string representation
        """
    def __copy__(self, arg0: dict) -> Color:
        """
        Create a shallow copy of the Color object
        """
    def __deepcopy__(self, memo: dict) -> Color:
        """
        Create a deep copy of the Color object
        """
    @typing.overload
    def __init__(self, rgb: typing.SupportsInt = -1) -> None:
        """
        Initialize Color with RGB value
        """
    @typing.overload
    def __init__(
        self,
        r: typing.SupportsInt,
        g: typing.SupportsInt,
        b: typing.SupportsInt,
        a: typing.SupportsFloat = -1.0,
    ) -> None:
        """
        Initialize Color with R, G, B, and optional Alpha values
        """
    def __repr__(self) -> str:
        """
        Return a string representation of the Color object
        """
    @typing.overload
    def a(self) -> float: ...
    @typing.overload
    def a(self, arg0: typing.SupportsFloat) -> Color: ...
    @typing.overload
    def b(self) -> int: ...
    @typing.overload
    def b(self, arg0: typing.SupportsInt) -> Color: ...
    def clone(self) -> Color:
        """
        Create a deep copy of the Color object
        """
    @typing.overload
    def g(self) -> int: ...
    @typing.overload
    def g(self, arg0: typing.SupportsInt) -> Color: ...
    def invalid(self) -> bool:
        """
        Check if the color is invalid
        """
    @typing.overload
    def r(self) -> int: ...
    @typing.overload
    def r(self, arg0: typing.SupportsInt) -> Color: ...
    def to_string(self) -> str:
        """
        Convert color to string representation
        """

class Path:
    def __copy__(self, arg0: dict) -> Path:
        """
        Create a shallow copy of the Path object
        """
    def __deepcopy__(self, memo: dict) -> Path:
        """
        Create a deep copy of the Path object
        """
    def __init__(self, d: str = "") -> None:
        """
        Initialize Path with path data string
        """
    def arc(
        self,
        rx: typing.SupportsFloat,
        ry: typing.SupportsFloat,
        x_axis_rotation: typing.SupportsFloat,
        large_arc_flag: typing.SupportsInt,
        sweep_flag: typing.SupportsInt,
        x: typing.SupportsFloat,
        y: typing.SupportsFloat,
    ) -> Path:
        """
        Add A (arc) command
        """
    @typing.overload
    def attrs(self) -> str: ...
    @typing.overload
    def attrs(self, arg0: str) -> Path: ...
    def clone(self) -> Path:
        """
        Create a deep copy of the Path object
        """
    def close(self) -> Path:
        """
        Add Z (close path) command
        """
    def cubic(
        self,
        c1x: typing.SupportsFloat,
        c1y: typing.SupportsFloat,
        c2x: typing.SupportsFloat,
        c2y: typing.SupportsFloat,
        x: typing.SupportsFloat,
        y: typing.SupportsFloat,
    ) -> Path:
        """
        Add C (cubic bezier) command
        """
    @typing.overload
    def d(self) -> str: ...
    @typing.overload
    def d(self, arg0: str) -> Path: ...
    @typing.overload
    def dash_array(self) -> str: ...
    @typing.overload
    def dash_array(self, arg0: str) -> Path: ...
    @typing.overload
    def fill(self) -> Color: ...
    @typing.overload
    def fill(self, arg0: Color) -> Path: ...
    def line_to(self, x: typing.SupportsFloat, y: typing.SupportsFloat) -> Path:
        """
        Add L (line to) command
        """
    def move_to(self, x: typing.SupportsFloat, y: typing.SupportsFloat) -> Path:
        """
        Add M (move to) command
        """
    def quadratic(
        self,
        cx: typing.SupportsFloat,
        cy: typing.SupportsFloat,
        x: typing.SupportsFloat,
        y: typing.SupportsFloat,
    ) -> Path:
        """
        Add Q (quadratic bezier) command
        """
    @typing.overload
    def stroke(self) -> Color: ...
    @typing.overload
    def stroke(self, arg0: Color) -> Path: ...
    @typing.overload
    def stroke_linecap(self) -> str: ...
    @typing.overload
    def stroke_linecap(self, arg0: str) -> Path: ...
    @typing.overload
    def stroke_linejoin(self) -> str: ...
    @typing.overload
    def stroke_linejoin(self, arg0: str) -> Path: ...
    @typing.overload
    def stroke_width(self) -> float: ...
    @typing.overload
    def stroke_width(self, arg0: typing.SupportsFloat) -> Path: ...
    def to_string(self) -> str:
        """
        Convert Path to SVG string representation
        """
    @typing.overload
    def transform(self) -> str: ...
    @typing.overload
    def transform(self, arg0: str) -> Path: ...

class Polygon:
    def __copy__(self, arg0: dict) -> Polygon:
        """
        Create a shallow copy of the Polygon object
        """
    def __deepcopy__(self, memo: dict) -> Polygon:
        """
        Create a deep copy of the Polygon object
        """
    def __init__(
        self,
        points: typing.Annotated[
            numpy.typing.NDArray[numpy.float64], "[m, 2]", "flags.c_contiguous"
        ],
    ) -> None:
        """
        Initialize Polygon with a set of points
        """
    @typing.overload
    def attrs(self) -> str: ...
    @typing.overload
    def attrs(self, arg0: str) -> Polygon: ...
    def clone(self) -> Polygon:
        """
        Create a deep copy of the Polygon object
        """
    @typing.overload
    def dash_array(self) -> str: ...
    @typing.overload
    def dash_array(self, arg0: str) -> Polygon: ...
    @typing.overload
    def fill(self) -> Color: ...
    @typing.overload
    def fill(self, arg0: Color) -> Polygon: ...
    def from_numpy(
        self,
        arg0: typing.Annotated[
            numpy.typing.NDArray[numpy.float64], "[m, 2]", "flags.c_contiguous"
        ],
    ) -> Polygon:
        """
        Set Polygon points from NumPy array
        """
    @typing.overload
    def stroke(self) -> Color: ...
    @typing.overload
    def stroke(self, arg0: Color) -> Polygon: ...
    @typing.overload
    def stroke_linecap(self) -> str: ...
    @typing.overload
    def stroke_linecap(self, arg0: str) -> Polygon: ...
    @typing.overload
    def stroke_linejoin(self) -> str: ...
    @typing.overload
    def stroke_linejoin(self, arg0: str) -> Polygon: ...
    @typing.overload
    def stroke_width(self) -> float: ...
    @typing.overload
    def stroke_width(self, arg0: typing.SupportsFloat) -> Polygon: ...
    def to_numpy(
        self,
    ) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 2]"]:
        """
        Convert Polygon points to NumPy array
        """
    def to_string(self) -> str:
        """
        Convert Polygon to SVG string representation
        """
    @typing.overload
    def transform(self) -> str: ...
    @typing.overload
    def transform(self, arg0: str) -> Polygon: ...

class Polyline:
    def __copy__(self, arg0: dict) -> Polyline:
        """
        Create a shallow copy of the Polyline object
        """
    def __deepcopy__(self, memo: dict) -> Polyline:
        """
        Create a deep copy of the Polyline object
        """
    def __init__(
        self,
        points: typing.Annotated[
            numpy.typing.NDArray[numpy.float64], "[m, 2]", "flags.c_contiguous"
        ],
    ) -> None:
        """
        Initialize Polyline with a set of points
        """
    @typing.overload
    def attrs(self) -> str: ...
    @typing.overload
    def attrs(self, arg0: str) -> Polyline: ...
    def clone(self) -> Polyline:
        """
        Create a deep copy of the Polyline object
        """
    @typing.overload
    def dash_array(self) -> str: ...
    @typing.overload
    def dash_array(self, arg0: str) -> Polyline: ...
    @typing.overload
    def fill(self) -> Color: ...
    @typing.overload
    def fill(self, arg0: Color) -> Polyline: ...
    def from_numpy(
        self,
        arg0: typing.Annotated[
            numpy.typing.NDArray[numpy.float64], "[m, 2]", "flags.c_contiguous"
        ],
    ) -> Polyline:
        """
        Set Polyline points from NumPy array
        """
    @typing.overload
    def stroke(self) -> Color: ...
    @typing.overload
    def stroke(self, arg0: Color) -> Polyline: ...
    @typing.overload
    def stroke_linecap(self) -> str: ...
    @typing.overload
    def stroke_linecap(self, arg0: str) -> Polyline: ...
    @typing.overload
    def stroke_linejoin(self) -> str: ...
    @typing.overload
    def stroke_linejoin(self, arg0: str) -> Polyline: ...
    @typing.overload
    def stroke_width(self) -> float: ...
    @typing.overload
    def stroke_width(self, arg0: typing.SupportsFloat) -> Polyline: ...
    def to_numpy(
        self,
    ) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 2]"]:
        """
        Convert Polyline points to NumPy array
        """
    def to_string(self) -> str:
        """
        Convert Polyline to SVG string representation
        """
    @typing.overload
    def transform(self) -> str: ...
    @typing.overload
    def transform(self, arg0: str) -> Polyline: ...

class Rect:
    def __copy__(self, arg0: dict) -> Rect:
        """
        Create a shallow copy of the Rect object
        """
    def __deepcopy__(self, memo: dict) -> Rect:
        """
        Create a deep copy of the Rect object
        """
    def __init__(
        self,
        x: typing.SupportsFloat = 0,
        y: typing.SupportsFloat = 0,
        width: typing.SupportsFloat = 0,
        height: typing.SupportsFloat = 0,
    ) -> None:
        """
        Initialize Rect with x, y, width, height
        """
    @typing.overload
    def attrs(self) -> str: ...
    @typing.overload
    def attrs(self, arg0: str) -> Rect: ...
    def clone(self) -> Rect:
        """
        Create a deep copy of the Rect object
        """
    @typing.overload
    def dash_array(self) -> str: ...
    @typing.overload
    def dash_array(self, arg0: str) -> Rect: ...
    @typing.overload
    def fill(self) -> Color: ...
    @typing.overload
    def fill(self, arg0: Color) -> Rect: ...
    @typing.overload
    def height(self) -> float: ...
    @typing.overload
    def height(self, arg0: typing.SupportsFloat) -> Rect: ...
    @typing.overload
    def rx(self) -> float: ...
    @typing.overload
    def rx(self, arg0: typing.SupportsFloat) -> Rect: ...
    @typing.overload
    def ry(self) -> float: ...
    @typing.overload
    def ry(self, arg0: typing.SupportsFloat) -> Rect: ...
    @typing.overload
    def stroke(self) -> Color: ...
    @typing.overload
    def stroke(self, arg0: Color) -> Rect: ...
    @typing.overload
    def stroke_linecap(self) -> str: ...
    @typing.overload
    def stroke_linecap(self, arg0: str) -> Rect: ...
    @typing.overload
    def stroke_linejoin(self) -> str: ...
    @typing.overload
    def stroke_linejoin(self, arg0: str) -> Rect: ...
    @typing.overload
    def stroke_width(self) -> float: ...
    @typing.overload
    def stroke_width(self, arg0: typing.SupportsFloat) -> Rect: ...
    def to_string(self) -> str:
        """
        Convert Rect to SVG string representation
        """
    @typing.overload
    def transform(self) -> str: ...
    @typing.overload
    def transform(self, arg0: str) -> Rect: ...
    @typing.overload
    def width(self) -> float: ...
    @typing.overload
    def width(self, arg0: typing.SupportsFloat) -> Rect: ...
    @typing.overload
    def x(self) -> float: ...
    @typing.overload
    def x(self, arg0: typing.SupportsFloat) -> Rect: ...
    @typing.overload
    def y(self) -> float: ...
    @typing.overload
    def y(self, arg0: typing.SupportsFloat) -> Rect: ...

class SVG:
    def __copy__(self, arg0: dict) -> SVG:
        """
        Create a shallow copy of the SVG object
        """
    def __deepcopy__(self, memo: dict) -> SVG:
        """
        Create a deep copy of the SVG object
        """
    def __init__(
        self, width: typing.SupportsFloat, height: typing.SupportsFloat
    ) -> None:
        """
        Initialize SVG with width and height
        """
    @typing.overload
    def add(self, polyline: Polyline) -> Polyline:
        """
        Add a Polyline to the SVG
        """
    @typing.overload
    def add(self, polygon: Polygon) -> Polygon:
        """
        Add a Polygon to the SVG
        """
    @typing.overload
    def add(self, circle: Circle) -> Circle:
        """
        Add a Circle to the SVG
        """
    @typing.overload
    def add(self, text: Text) -> Text:
        """
        Add a Text to the SVG
        """
    @typing.overload
    def add(self, path: Path) -> Path:
        """
        Add a Path to the SVG
        """
    @typing.overload
    def add(self, rect: Rect) -> Rect:
        """
        Add a Rect to the SVG
        """
    def add_circle(
        self,
        center: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"],
        *,
        r: typing.SupportsFloat = 1.0,
    ) -> Circle:
        """
        Add a Circle to the SVG
        """
    def add_path(self, d: str = "") -> Path:
        """
        Add a Path to the SVG
        """
    def add_polygon(
        self,
        points: typing.Annotated[
            numpy.typing.NDArray[numpy.float64], "[m, 2]", "flags.c_contiguous"
        ],
    ) -> Polygon:
        """
        Add a Polygon to the SVG using NumPy array of points
        """
    def add_polyline(
        self,
        points: typing.Annotated[
            numpy.typing.NDArray[numpy.float64], "[m, 2]", "flags.c_contiguous"
        ],
    ) -> Polyline:
        """
        Add a Polyline to the SVG using NumPy array of points
        """
    def add_rect(
        self,
        x: typing.SupportsFloat,
        y: typing.SupportsFloat,
        width: typing.SupportsFloat,
        height: typing.SupportsFloat,
    ) -> Rect:
        """
        Add a Rect to the SVG
        """
    def add_text(
        self,
        position: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"],
        *,
        text: str,
        fontsize: typing.SupportsFloat = 10.0,
    ) -> Text:
        """
        Add a Text to the SVG
        """
    def as_circle(self, index: typing.SupportsInt) -> Circle:
        """
        Get the element at the given index as a Circle
        """
    def as_path(self, index: typing.SupportsInt) -> Path:
        """
        Get the element at the given index as a Path
        """
    def as_polygon(self, index: typing.SupportsInt) -> Polygon:
        """
        Get the element at the given index as a Polygon
        """
    def as_polyline(self, index: typing.SupportsInt) -> Polyline:
        """
        Get the element at the given index as a Polyline
        """
    def as_rect(self, index: typing.SupportsInt) -> Rect:
        """
        Get the element at the given index as a Rect
        """
    def as_text(self, index: typing.SupportsInt) -> Text:
        """
        Get the element at the given index as a Text
        """
    @typing.overload
    def attrs(self) -> str: ...
    @typing.overload
    def attrs(self, arg0: str) -> SVG: ...
    @typing.overload
    def background(self) -> Color: ...
    @typing.overload
    def background(self, arg0: Color) -> SVG: ...
    def clone(self) -> SVG:
        """
        Create a deep copy of the SVG object
        """
    def dump(self, path: str) -> None:
        """
        Save the SVG to a file
        """
    def empty(self) -> bool:
        """
        Check if the SVG is empty
        """
    @typing.overload
    def grid_color(self) -> Color: ...
    @typing.overload
    def grid_color(self, arg0: Color) -> SVG: ...
    @typing.overload
    def grid_step(self) -> float: ...
    @typing.overload
    def grid_step(self, arg0: typing.SupportsFloat) -> SVG: ...
    @typing.overload
    def grid_x(self) -> list[float]: ...
    @typing.overload
    def grid_x(self, arg0: collections.abc.Sequence[typing.SupportsFloat]) -> SVG: ...
    @typing.overload
    def grid_y(self) -> list[float]: ...
    @typing.overload
    def grid_y(self, arg0: collections.abc.Sequence[typing.SupportsFloat]) -> SVG: ...
    @typing.overload
    def height(self) -> float: ...
    @typing.overload
    def height(self, arg0: typing.SupportsFloat) -> SVG: ...
    def is_circle(self, arg0: typing.SupportsInt) -> bool:
        """
        Check if the element at the given index is a Circle
        """
    def is_path(self, arg0: typing.SupportsInt) -> bool:
        """
        Check if the element at the given index is a Path
        """
    def is_polygon(self, arg0: typing.SupportsInt) -> bool:
        """
        Check if the element at the given index is a Polygon
        """
    def is_polyline(self, arg0: typing.SupportsInt) -> bool:
        """
        Check if the element at the given index is a Polyline
        """
    def is_rect(self, arg0: typing.SupportsInt) -> bool:
        """
        Check if the element at the given index is a Rect
        """
    def is_text(self, arg0: typing.SupportsInt) -> bool:
        """
        Check if the element at the given index is a Text
        """
    def num_elements(self) -> int:
        """
        Get the number of elements in the SVG
        """
    def pop(self) -> None:
        """
        Remove the last added element from the SVG
        """
    def to_string(self) -> str:
        """
        Convert the SVG to a string representation
        """
    @typing.overload
    def view_box(self) -> list[float]: ...
    @typing.overload
    def view_box(self, arg0: collections.abc.Sequence[typing.SupportsFloat]) -> SVG: ...
    @typing.overload
    def width(self) -> float: ...
    @typing.overload
    def width(self, arg0: typing.SupportsFloat) -> SVG: ...

class Text:
    @staticmethod
    def html_escape(text: str) -> str:
        """
        Escape special characters in the text for HTML
        """
    def __copy__(self, arg0: dict) -> Text:
        """
        Create a shallow copy of the Text object
        """
    def __deepcopy__(self, memo: dict) -> Text:
        """
        Create a deep copy of the Text object
        """
    def __init__(
        self,
        position: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"],
        text: str,
        fontsize: typing.SupportsFloat = 10.0,
    ) -> None:
        """
        Initialize Text with position, content, and font size
        """
    @typing.overload
    def attrs(self) -> str: ...
    @typing.overload
    def attrs(self, arg0: str) -> Text: ...
    def clone(self) -> Text:
        """
        Create a deep copy of the Text object
        """
    @typing.overload
    def dash_array(self) -> str: ...
    @typing.overload
    def dash_array(self, arg0: str) -> Text: ...
    @typing.overload
    def fill(self) -> Color: ...
    @typing.overload
    def fill(self, arg0: Color) -> Text: ...
    @typing.overload
    def fontsize(self) -> float: ...
    @typing.overload
    def fontsize(self, arg0: typing.SupportsFloat) -> Text: ...
    @typing.overload
    def lines(self) -> list[str]: ...
    @typing.overload
    def lines(self, arg0: collections.abc.Sequence[str]) -> Text: ...
    @typing.overload
    def position(
        self,
    ) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 1]"]:
        """
        Get the position of the Text
        """
    @typing.overload
    def position(
        self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]
    ) -> Text:
        """
        Set the position of the Text
        """
    @typing.overload
    def stroke(self) -> Color: ...
    @typing.overload
    def stroke(self, arg0: Color) -> Text: ...
    @typing.overload
    def stroke_linecap(self) -> str: ...
    @typing.overload
    def stroke_linecap(self, arg0: str) -> Text: ...
    @typing.overload
    def stroke_linejoin(self) -> str: ...
    @typing.overload
    def stroke_linejoin(self, arg0: str) -> Text: ...
    @typing.overload
    def stroke_width(self) -> float: ...
    @typing.overload
    def stroke_width(self, arg0: typing.SupportsFloat) -> Text: ...
    @typing.overload
    def text(self) -> str: ...
    @typing.overload
    def text(self, arg0: str) -> Text: ...
    def to_string(self) -> str:
        """
        Convert Text to SVG string representation
        """
    @typing.overload
    def transform(self) -> str: ...
    @typing.overload
    def transform(self, arg0: str) -> Text: ...

def add(arg0: typing.SupportsInt, arg1: typing.SupportsInt) -> int:
    """
    Add two numbers

    Some other explanation about the add function.
    """

__version__: str = "0.1.0"
