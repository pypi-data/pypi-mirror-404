"""
Module for handling aff files, the chart file format
used by the music game *Arcaea*.
"""

from collections.abc import Callable
from typing import ClassVar, TextIO
import math

_PRECISION: int = 2

class Event:
    """Represents a single control statement in an aff file."""
    start_time: int

    def __str__(self) -> str:
        """
        Converts a event to its string representation in an aff file.

        E.g., `Tap(1000, 1)` -> `(1000,1);`, `Hold(1000, 2000, 2)` -> `hold(1000,2000,2);`

        For an abstract Event, this is a dummy implementation and
        the resulting string is not valid in an aff file.
        """
        return f"event({self.start_time});"
    
    def __repr__(self) -> str:
        """
        Converts a event to its detailed string representation.

        E.g., `Tap(1000, 1)` -> `Tap(start_time=1000, lane=1)`, `Hold(1000, 2000, 2)` -> `Hold(start_time=1000, end_time=2000, lane=2)`

        For an abstract Event, this method returns the default representation `<Event object at 0x...>`.
        """
        return super().__repr__()
    
    def get_type(self) -> str:
        """
        Gets the type name of this event.
        """
        return "event"


class Note(Event):
    """
    Represents a note.
    
    This class is for type hierarchy purposes only.
    """
    pass


class Tap(Note):
    """
    Represents a tap note (or floor note) in an aff file / chart.
    """
    lane: int

    def __init__(self, start_time: int, lane: int):
        """
        Constructs a tap note by time and lane.
        """
        self.start_time = start_time
        self.lane = lane
    
    def __str__(self) -> str:
        return f"({self.start_time},{self.lane});"
    
    def __repr__(self) -> str:
        return f"Tap(start_time={self.start_time}, lane={self.lane})"
    
    def get_type(self) -> str:
        return "tap"


class Hold(Note):
    """
    Represents a hold note in an aff file / chart.
    """
    lane: int
    end_time: int

    def __init__(self, start_time: int, end_time: int, lane: int):
        """
        Constructs a hold note by time, end time and lane.
        """
        self.start_time = start_time
        self.end_time = end_time
        self.lane = lane
    
    def __str__(self) -> str:
        return f"hold({self.start_time},{self.end_time},{self.lane});"
    
    def __repr__(self) -> str:
        return f"Hold(start_time={self.start_time}, end_time={self.end_time}, lane={self.lane})"
    
    def get_type(self) -> str:
        return "hold"


def easing_linear(x: float) -> float:
    """
    The linear easing function. The position moves at a constant speed.
    
    This maps the ratio of time to the ratio of position.
    """
    return x

def easing_sine_in(x: float) -> float:
    """
    The sine-in easing function. The position moves fast at the beginning and slows down towards the end.
    Note that this is different from the common definition of "sine-in" easing, but the version used in Arcaea.
    
    This maps the ratio of time to the ratio of position.
    """
    return math.sin(x * math.pi / 2)

def easing_sine_out(x: float) -> float:
    """
    The sine-out easing function. The position moves slowly at the beginning and accelerates towards the end.
    Note that this is different from the common definition of "sine-out" easing, but the version used in Arcaea.

    This maps the ratio of time to the ratio of position.
    """
    return 1 - math.cos(x * math.pi / 2)

def easing_bezier(x: float) -> float:
    """
    The cubic Bezier easing function with control points 0, 1/3, 2/3, 1.
    The position moves slowly at the beginning and end, and faster in the middle.
    
    This maps the ratio of time to the ratio of position.
    """
    return x * x * (3 - 2 * x)

def easing_linear_derivative(x: float) -> float:
    """
    The derivative (speed) of `easing_linear`.
    This is more used in mathematical computation, but not in actual gameplay.
    """
    return 1

def easing_sine_in_derivative(x: float) -> float:
    """
    The derivative (speed) of `easing_sine_in`.
    This is more used in mathematical computation, but not in actual gameplay.
    """
    return (math.pi / 2) * math.cos(x * math.pi / 2)

def easing_sine_out_derivative(x: float) -> float:
    """
    The derivative (speed) of `easing_sine_out`.
    This is more used in mathematical computation, but not in actual gameplay.
    """
    return (math.pi / 2) * math.sin(x * math.pi / 2)

def easing_bezier_derivative(x: float) -> float:
    """
    The derivative (speed) of `easing_bezier`.
    This is more used in mathematical computation, but not in actual gameplay.
    """
    return 6 * x * (1 - x)

def ratio(start: float, value: float, end: float) -> float:
    """
    Returns the ratio between start and end for a given value.
    """
    return (value - start) / (end - start)

def value_at_ratio(start: float, end: float, ratio: float) -> float:
    """
    Returns the value between start and end at a given ratio.
    """
    return start + (end - start) * ratio

class Easing:
    """
    Enum-like class for 1D-easing types.
    
    This class represents an 1D-easing, providing some useful functions.
    For 2D-easing or easing used by arcs, see `ArcEasing`.
    | Easing type       | Abbreviation |
    | ----------------- | ------------ |
    | `Easing.BEZIER`   | `Easing.B`   |
    | `Easing.LINEAR`   | `Easing.S`   |
    | `Easing.SINE_IN`  | `Easing.SI`  |
    | `Easing.SINE_OUT` | `Easing.SO`  |

    You can create your own easing by providing the easing function,
    but they are not supported in the actual game.

    Note that the sine in and sine out easing are defined differently
    from common easing definitions, instead, they use the definitions
    in Arcaea.
    """

    BEZIER: ClassVar["Easing"]
    LINEAR: ClassVar["Easing"]
    SINE_IN: ClassVar["Easing"]
    SINE_OUT: ClassVar["Easing"]
    B: ClassVar["Easing"]
    S: ClassVar["Easing"]
    SI: ClassVar["Easing"]
    SO: ClassVar["Easing"]

    def __init__(self, easing: Callable[[float], float],
                 derivative: Callable[[float], float | None]):
        """
        Constructs an easing type by its easing function and derivative function.

        easing: A function that maps the ratio of time to the ratio of position.

        derivative: A function that gives the derivative of the easing function.

        The easing function should map 0.0 to 0.0, 1.0 to 1.0, and is defined on
        [0.0, 1.0]. If the easing function is not continuous or not differentiable,
        the derivative function at such point should return `None` and avoid raising
        exceptions or returning NaN value.
        """
        self.easing = easing
        self.derivative = derivative

    def get_position(self,
                     start_time: float | int, end_time: float | int,
                     start_pos: float, end_pos: float, current_time: float | int) -> float:
        """
        Gets the position at a given time using this easing.
        """
        if start_time == end_time:
            return start_pos
        time_ratio = ratio(start_time, current_time, end_time)
        return value_at_ratio(start_pos, end_pos, self.easing(time_ratio))
    
    def get_speed(self,
                  start_time: float | int, end_time: float | int,
                  start_pos: float, end_pos: float, current_time: float | int) -> float | None:
        """
        Gets the speed at a given time using this easing.
        """
        if start_time == end_time:
            return None
        time_ratio = ratio(start_time, current_time, end_time)
        pos_ratio_derivative = self.derivative(time_ratio)
        if pos_ratio_derivative is None:
            return None
        time_span = end_time - start_time
        pos_span = end_pos - start_pos
        return (pos_span / time_span) * pos_ratio_derivative


Easing.BEZIER = Easing(easing_bezier, easing_bezier_derivative)
Easing.LINEAR = Easing(easing_linear, easing_linear_derivative)
Easing.SINE_IN = Easing(easing_sine_in, easing_sine_in_derivative)
Easing.SINE_OUT = Easing(easing_sine_out, easing_sine_out_derivative)
Easing.B = Easing.BEZIER
Easing.S = Easing.LINEAR
Easing.SI = Easing.SINE_IN
Easing.SO = Easing.SINE_OUT


class ArcEasing:
    """
    Enum-like class for 2D-easing types used by arcs.

    This class represents an 2D-easing, providing some useful functions.
    For 1D-easing, see `Easing`.
    | Easing type       | Abbreviation |
    | ----------------- | ------------ |
    | `Easing.BEZIER`   | `Easing.B`   |
    | `Easing.LINEAR`   | `Easing.S`   |
    | `Easing.SINE_IN`  | `Easing.SI`  |
    | `Easing.SINE_OUT` | `Easing.SO`  |

    You can create your own easing by providing the easing function,
    but they are not supported in the actual game.

    Note that the sine in and sine out easing are defined differently
    from common easing definitions, instead, they use the definitions
    in Arcaea.
    """

    BEZIER: ClassVar["ArcEasing"]
    LINEAR: ClassVar["ArcEasing"]
    SINE_IN: ClassVar["ArcEasing"]
    SINE_OUT: ClassVar["ArcEasing"]
    B: ClassVar["ArcEasing"]
    S: ClassVar["ArcEasing"]
    SI: ClassVar["ArcEasing"]
    SO: ClassVar["ArcEasing"]
    SISI: ClassVar["ArcEasing"]
    SISO: ClassVar["ArcEasing"]
    SOSI: ClassVar["ArcEasing"]
    SOSO: ClassVar["ArcEasing"]
    values: ClassVar[dict[str, "ArcEasing"]]

    def __init__(self, name: str, easing_x: Easing, easing_y: Easing):
        self.name = name
        self.easing_x = easing_x
        self.easing_y = easing_y
    
    def get_position(self,
                     start_time: float | int, end_time: float | int,
                     start_x: float, start_y: float, end_x: float, end_y: float,
                     current_time: float | int) -> tuple[float, float]:
        """
        Gets the position at a given time using this easing.
        """
        return (
            self.easing_x.get_position(start_time, end_time, start_x, end_x, current_time),
            self.easing_y.get_position(start_time, end_time, start_y, end_y, current_time)
        )
    
    def get_speed(self,
                  start_time: float | int, end_time: float | int,
                  start_x: float, start_y: float, end_x: float, end_y: float,
                  current_time: float | int) -> tuple[float | None, float | None]:
        """
        Gets the speed at a given time using this easing.
        """
        return (
            self.easing_x.get_speed(start_time, end_time, start_x, end_x, current_time),
            self.easing_y.get_speed(start_time, end_time, start_y, end_y, current_time)
        )


ArcEasing.BEZIER = ArcEasing("b", Easing.BEZIER, Easing.BEZIER)
ArcEasing.LINEAR = ArcEasing("s", Easing.LINEAR, Easing.LINEAR)
ArcEasing.SINE_IN = ArcEasing("si", Easing.SINE_IN, Easing.LINEAR)
ArcEasing.SINE_OUT = ArcEasing("so", Easing.SINE_OUT, Easing.LINEAR)
ArcEasing.B = ArcEasing.BEZIER
ArcEasing.S = ArcEasing.LINEAR
ArcEasing.SI = ArcEasing.SINE_IN
ArcEasing.SO = ArcEasing.SINE_OUT
ArcEasing.SISI = ArcEasing("sisi", Easing.SINE_IN, Easing.SINE_IN)
ArcEasing.SISO = ArcEasing("siso", Easing.SINE_IN, Easing.SINE_OUT)
ArcEasing.SOSI = ArcEasing("sosi", Easing.SINE_OUT, Easing.SINE_IN)
ArcEasing.SOSO = ArcEasing("soso", Easing.SINE_OUT, Easing.SINE_OUT)

ArcEasing.values = {
    "b": ArcEasing.BEZIER,
    "s": ArcEasing.LINEAR,
    "si": ArcEasing.SINE_IN,
    "so": ArcEasing.SINE_OUT,
    "sisi": ArcEasing.SISI,
    "siso": ArcEasing.SISO,
    "sosi": ArcEasing.SOSI,
    "soso": ArcEasing.SOSO
}


class Arc(Note):
    """
    Represents an arc note in an aff file / chart.

    This class corresponds to an arc statement in aff files,
    which means arctaps are considered as an attribute of this class,
    and there are no separate ArcTap class representing these.
    """

    start_time: int
    end_time: int
    start_x: float
    end_x: float
    easing: ArcEasing
    start_y: float
    end_y: float
    color: int
    hitsound: str
    is_skyline: bool
    smoothness: float
    arctaps: list[int]

    def __init__(self, start_time: int, end_time: int, start_x: float,
                 end_x: float, easing: ArcEasing, start_y: float,
                 end_y: float, color: int, hitsound: str | None = "none",
                 is_skyline: bool = False, smoothness: float | None = 1.0,
                 arctaps: list[int] = []):
        """
        Constructs an arc note by all its attributes.
        hitsound defaults to `none` if not specified, and smoothness defaults to `1.0`.

        The arguments are ordered as in the aff file format.
        """
        self.start_time = start_time
        self.end_time = end_time
        self.start_x = start_x
        self.end_x = end_x
        self.easing = easing
        self.start_y = start_y
        self.end_y = end_y
        self.color = color
        if hitsound is None:
            hitsound = "none"
        self.hitsound = hitsound
        self.is_skyline = is_skyline
        if smoothness is None:
            smoothness = 1.0
        self.smoothness = smoothness
        self.arctaps = arctaps

    def __str__(self) -> str:
        smoothness_formatted = f"{self.smoothness:.{_PRECISION}f}"

        if float(smoothness_formatted) == 1:
            part_before_arctap = (f"arc({self.start_time},{self.end_time},"
                                  f"{self.start_x:.{_PRECISION}f},"
                                  f"{self.end_x:.{_PRECISION}f},"
                                  f"{self.easing.name},"
                                  f"{self.start_y:.{_PRECISION}f},"
                                  f"{self.end_y:.{_PRECISION}f},"
                                  f"{self.color},{self.hitsound},"
                                  f"{"true" if self.is_skyline else "false"})")
        else:
            part_before_arctap = (f"arc({self.start_time},{self.end_time},"
                                  f"{self.start_x:.{_PRECISION}f},"
                                  f"{self.end_x:.{_PRECISION}f},"
                                  f"{self.easing.name},"
                                  f"{self.start_y:.{_PRECISION}f},"
                                  f"{self.end_y:.{_PRECISION}f},"
                                  f"{self.color},{self.hitsound},"
                                  f"{"true" if self.is_skyline else "false"},"
                                  f"{smoothness_formatted})")
        
        part_arctap = ""
        if self.arctaps:
            part_arctap = "[" + ",".join(map(lambda t: f"arctap({t})", self.arctaps)) + "]"
        
        return part_before_arctap + part_arctap + ";"
    
    def __repr__(self) -> str:
        return (f"Arc(start_time={self.start_time}, end_time={self.end_time}, "
                f"start_x={self.start_x}, end_x={self.end_x}, easing={self.easing.name}, "
                f"start_y={self.start_y}, end_y={self.end_y}, color={self.color}, "
                f"hitsound='{self.hitsound}', is_skyline={self.is_skyline}, "
                f"smoothness={self.smoothness}, arctaps={self.arctaps})")
    
    def get_position(self, current_time: float) -> tuple[float, float]:
        """
        Gets the (x, y) position at a given time using this arc's easing.
        """
        return self.easing.get_position(
            self.start_time, self.end_time,
            self.start_x, self.start_y,
            self.end_x, self.end_y,
            current_time
        )
    
    def separate_arctaps(self) -> list["Arc"]:
        """
        Separates the arctaps into individual arc objects.

        Each arctap will be represented as an `Arc` object with 1ms length,
        start at the same time as the original arc, and with both the start and end
        positions equal to the position of corresponding arctap.

        If there are no arctaps, an empty list is returned.
        This method does not modify the original `Arc` object.
        """
        arcs = []
        for t in self.arctaps:
            x, y = self.get_position(t)
            arc = Arc(
                start_time=t,
                end_time=t+1,
                start_x=x,
                end_x=x,
                easing=ArcEasing.S,
                start_y=y,
                end_y=y,
                color=self.color,
                hitsound=self.hitsound,
                is_skyline=True,
                arctaps=[t]
            )
            arcs.append(arc)
        return arcs

class Timing(Event):
    """
    Represents a timing event in an aff file / chart.
    """

    bpm: float
    beats: float

    def __init__(self, start_time: int, bpm: float, beats: float):
        """
        Constructs a timing event by time, bpm and beats.
        """
        self.start_time = start_time
        self.bpm = bpm
        self.beats = beats
    
    def __str__(self) -> str:
        return f"timing({self.start_time},{self.bpm:.{_PRECISION}f},{self.beats:.{_PRECISION}f});"
    
    def __repr__(self) -> str:
        return f"Timing(start_time={self.start_time}, bpm={self.bpm}, beats={self.beats})"


class SceneControl(Event):
    """
    Represents a scenecontrol event with parameters
    in an aff file / chart.

    Possible effect types are:
    trackdisplay, redline, arcahvdistort, arcahvdebris,
    hidegroup, enwidencamera, enwidenlanes
    """

    effect: str
    param1: float | None
    param2: int | None
    has_param: bool

    TRACKHIDE = "trackhide"
    TRACKSHOW = "trackshow"
    TRACKDISPLAY = "trackdisplay"
    REDLINE = "redline"
    ARCAHVDISTORT = "arcahvdistort"
    ARCAHVDEBRIS = "arcahvdebris"
    HIDEGROUP = "hidegroup"
    ENWIDENCAMERA = "enwidencamera"
    ENWIDENLANES = "enwidenlanes"

    def __init__(self, start_time: int, effect: str, param1: float | None = None, param2: int | None = None):
        self.start_time = start_time
        self.effect = effect
        self.param1 = param1
        self.param2 = param2
        self.has_param = param1 is not None and param2 is not None

    def __str__(self) -> str:
        if self.has_param:
            return f"scenecontrol({self.start_time},{self.effect},{self.param1:.{_PRECISION}f},{self.param2});"
        else:
            return f"scenecontrol({self.start_time},{self.effect});"

    def __repr__(self) -> str:
        if self.has_param:
            return f"SceneControl(start_time={self.start_time}, name='{self.effect}', param1={self.param1}, param2={self.param2})"
        else:
            return f"SceneControl(start_time={self.start_time}, name='{self.effect}')"


class Camera(Event):
    """
    Represents a camera event in an aff file / chart.
    """

    x: float
    y: float
    z: float
    xOy_angle: float
    yOz_angle: float
    zOx_angle: float
    easing: str
    duration: int

    def __init__(self, start_time: int, x: float, y: float, z: float,
                 xOy_angle: float, yOz_angle: float, zOx_angle: float,
                 easing: str, duration: int):
        self.start_time = start_time
        self.x = x
        self.y = y
        self.z = z
        self.xOy_angle = xOy_angle
        self.yOz_angle = yOz_angle
        self.zOx_angle = zOx_angle
        self.easing = easing
        self.duration = duration

    def __str__(self) -> str:
        return f"camera({self.start_time},{self.x:.{_PRECISION}f},{self.y:.{_PRECISION}f},{self.z:.{_PRECISION}f},{self.xOy_angle:.{_PRECISION}f},{self.yOz_angle:.{_PRECISION}f},{self.zOx_angle:.{_PRECISION}f},{self.easing},{self.duration});"

    def __repr__(self) -> str:
        return f"Camera(start_time={self.start_time}, x={self.x}, y={self.y}, z={self.z}, xOy_angle={self.xOy_angle}, yOz_angle={self.yOz_angle}, zOx_angle={self.zOx_angle}, easing='{self.easing}', duration={self.duration})"


class TimingGroup(list[Event]):
    """
    Represents a timing group in an aff file / chart.
    A timing group is a list of events.

    The notes / events outside timing groups are considered as a
    separate timinggroup.
    """

    anglex: int
    angley: int
    fadingholds: bool
    noinput: bool

    def __init__(self, noinput: bool = False, fadingholds: bool = False,
                 anglex: int | None = 0, angley: int | None = 0,
                 attr_str: str | None = None):
        """
        Constructs a timing group with optional attributes.

        If attr_str is given, other attribute parameters are ignored,
        and actual attributes are parsed from attr_str. If parsing fails,
        a ValueError is raised.

        If attr_str is not given, attributes are set according to
        the parameters.
        """
        super().__init__()
        if attr_str is not None:
            self.parse_attributes(attr_str)
            return
        self.noinput = noinput
        if anglex is None:
            anglex = 0
        if angley is None:
            angley = 0
        self.anglex = anglex
        self.angley = angley
        self.fadingholds = fadingholds
    
    def parse_attributes(self, attr_str: str):
        """
        Parses timing group attributes from a string and store them in this object.
        """
        self.noinput = False
        self.fadingholds = False
        self.anglex = 0
        self.angley = 0
        attributes = attr_str.split("_")
        for attribute in attributes:
            if attribute == "noinput":
                self.noinput = True
            elif attribute == "fadingholds":
                self.fadingholds = True
            elif attribute.startswith("anglex"):
                try:
                    self.anglex = int(attribute[6:])
                except ValueError:
                    raise ValueError(f"Invalid anglex attribute: {attribute}")
            elif attribute.startswith("angley"):
                try:
                    self.angley = int(attribute[6:])
                except ValueError:
                    raise ValueError(f"Invalid angley attribute: {attribute}")
            else:
                raise ValueError(f"Unknown attribute: {attribute}")
    
    def gen_attribute_string(self) -> str:
        """
        Generates the attribute string for this timing group.
        """
        attributes = []
        if self.noinput:
            attributes.append("noinput")
        if self.fadingholds:
            attributes.append("fadingholds")
        if self.anglex != 0:
            attributes.append(f"anglex{self.anglex}")
        if self.angley != 0:
            attributes.append(f"angley{self.angley}")
        return "_".join(attributes)
    
    def __str__(self, default_group = False) -> str:
        """
        Converts a timing group to its representation in an aff file.
        If `default_group is True`, the `timinggroup(){};` wrapping is omitted,
        and events are formatted without indent at the beginning of each line.
        """
        if default_group:
            events_str = "\n".join(str(event) for event in self)
            return events_str
        else:
            attr_str = self.gen_attribute_string()
            events_str = "\n".join("  " + str(event) for event in self)
            return f"timinggroup({attr_str}){{\n{events_str}\n}};"


class Chart:
    """
    Represents an aff file / chart.
    """
    timing_groups: list[TimingGroup]
    attributes: dict[str, str]

    ATTRIBUTE_KEY_AUDIO_OFFSET = "AudioOffset"
    ATTRIBUTE_KEY_DENSITY_FACTOR = "TimingPointDensityFactor"

    def __init__(self):
        self.timing_groups = [TimingGroup()]
        self.attributes = {Chart.ATTRIBUTE_KEY_AUDIO_OFFSET : "0"}

    def get_timing_groups(self) -> list[TimingGroup]:
        """
        Gets the list of all timing groups in this chart.
        The default timing group is at index 0, others
        are listed by the same order as they appears in
        the file.
        """
        return self.timing_groups
    
    def get_default_timing_group(self) -> TimingGroup:
        """
        Gets the default timing group. Equivalent to
        `get_timing_groups()[0]`.
        """
        if not self.timing_groups:
            self.timing_groups = [TimingGroup()]
        return self.timing_groups[0]

    def get_audio_offset(self) -> int:
        """
        Gets the audio offset of this chart, in `int`.

        By default, offset is 0, this means the chart
        starts at the same time when the audio starts
        to play.

        If offset is `x`, then the chart starts `x`
        milliseconds after the audio starts to play.
        `x` can be negative, which means the chart
        starts earlier than the audio starts.

        If the corresponding attribute key is not a
        number, raises a ValueError.
        """
        off_str = self.attributes.get(Chart.ATTRIBUTE_KEY_AUDIO_OFFSET, "0")
        try:
            return int(off_str)
        except ValueError:
            raise ValueError(f"Invalid audio offset attribute: {off_str}")
    
    def set_audio_offset(self, offset: int):
        """
        Sets the audio offset attribute. For the
        meaning of audio offset, see `get_audio_offset`.
        """
        self.attributes[Chart.ATTRIBUTE_KEY_AUDIO_OFFSET] = str(offset)

    def get_density_factor(self) -> float:
        """
        Gets the density factor of this chart, in `float`.

        By default, density factor is `1`. If this value
        is set to `y`, the density of judgement points
        of hold and arc notes becomes `y` times the
        default density.

        This value should be positive.
        """
        den_str = self.attributes.get(Chart.ATTRIBUTE_KEY_DENSITY_FACTOR, "1")
        try:
            return float(den_str)
        except ValueError:
            raise ValueError(f"Invalid density factor attribute: {den_str}")
    
    def set_density_factor(self, factor: float):
        """
        Sets the density factor attribute. For the
        meaning of density factor, see `get_density_factor`.
        """
        self.attributes[Chart.ATTRIBUTE_KEY_DENSITY_FACTOR] = str(factor)

    def __str__(self):
        """
        Gets the representation of this chart as an
        aff file.
        """
        attributes_copy = self.attributes.copy()
        audio_offset = attributes_copy.pop(Chart.ATTRIBUTE_KEY_AUDIO_OFFSET, "0")
        density_factor = attributes_copy.pop(Chart.ATTRIBUTE_KEY_DENSITY_FACTOR, "1")
        attributes_str_list = [f"{Chart.ATTRIBUTE_KEY_AUDIO_OFFSET}:{audio_offset}"]
        if float(density_factor) != 1:
            attributes_str_list.append(f"{Chart.ATTRIBUTE_KEY_DENSITY_FACTOR}:{density_factor}")
        for k, v in attributes_copy.items():
            attributes_str_list.append(f"{k}, {v}")
        attributes_str = "\n".join(attributes_str_list)

        default_group_str = self.get_default_timing_group().__str__(default_group=True)
        additional_group_str = "\n".join(tg.__str__() for tg in self.timing_groups[1:])
        return f"{attributes_str}\n-\n{default_group_str}\n{additional_group_str}"


def load(stream: TextIO, strict: bool = False) -> Chart:
    """
    Parse a chart from a readable text stream.

    If `strict` is set to `True`, it will raise a ValueError
    if a line could not be parsed. Otherwise, it will ignore
    that line.
    """

    def check_prefix(text: str, prefix: str) -> bool:
        if not strict:
            return text[:len(prefix)].lower() == prefix.lower()
        else:
            return text.startswith(prefix)
    chart = Chart()

    _PART_METADATA = 0
    _PART_MAIN = 1

    current_part = _PART_METADATA
    current_timing_group = chart.get_default_timing_group()
    line_num = 0
    while True:
        line_num += 1
        line = stream.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue

        if current_part == _PART_METADATA:
            if line == "-":
                current_part = _PART_MAIN
                continue
            key, _, val = line.partition(":")
            if not _:
                if strict:
                    raise ValueError(f"{line_num}: Invalid line '{line}'")
                current_part = _PART_MAIN
            else:
                chart.attributes[key] = val

        if current_part == _PART_MAIN:
            if check_prefix(line, "timinggroup("):
                if current_timing_group == chart.get_default_timing_group():
                    right_bracket_index = line.find(")", 12)
                    if strict and line[right_bracket_index:] != "){":
                        raise ValueError(f"{line_num}: Found invalid timing group start")
                    attr_str = line[12:right_bracket_index]
                    try:
                        current_timing_group = TimingGroup(attr_str=attr_str)
                    except ValueError:
                        if strict:
                            raise ValueError(f"{line_num}: Invalid timing group attribute: '{attr_str}'")
                        else:
                            current_timing_group = TimingGroup()
                    chart.timing_groups.append(current_timing_group)
                elif strict:
                    raise ValueError(f"{line_num}: Found timing group inside another timing group")
                continue
            elif "}" in line:
                if strict and line != "};":
                    raise ValueError(f"{line_num}: Found invalid timing group end")
                if strict and current_timing_group == chart.get_default_timing_group():
                    raise ValueError(f"{line_num}: Found timing group ending out of a timing group")
                current_timing_group = chart.get_default_timing_group()
                continue
            
            if check_prefix(line, "("):
                right_bracket_index = line.find(")", 1)
                if right_bracket_index == -1:
                    right_bracket_index = len(line)
                if strict and line[right_bracket_index:] != ");":
                    raise ValueError(f"{line_num}: Found extra string after a tap: '{line}'")
                param = line[1:right_bracket_index].split(",")
                if len(param) == 2:
                    try:
                        time = int(param[0])
                        lane = int(param[1])
                        current_timing_group.append(Tap(time, lane))
                        continue
                    except ValueError:
                        pass
                if strict:
                    raise ValueError(f"{line_num}: Cannot parse tap: '{line}', should be (int,int)")
            elif check_prefix(line, "hold("):
                right_bracket_index = line.find(")", 5)
                if right_bracket_index == -1:
                    right_bracket_index = len(line)
                if strict and line[right_bracket_index:] != ");":
                    raise ValueError(f"{line_num}: Found extra string after a hold: '{line}'")
                param = line[5:right_bracket_index].split(",")
                if len(param) == 3:
                    try:
                        start_time = int(param[0])
                        end_time = int(param[1])
                        lane = int(param[2])
                        current_timing_group.append(Hold(start_time, end_time, lane))
                        continue
                    except ValueError:
                        pass
                if strict:
                    raise ValueError(f"{line_num}: Cannot parse hold: '{line}', should be hold(int,int,int)")
            elif check_prefix(line, "scenecontrol("):
                right_bracket_index = line.find(")", 13)
                if right_bracket_index == -1:
                    right_bracket_index = len(line)
                if strict and line[right_bracket_index:] != ");":
                    raise ValueError(f"{line_num}: Found extra string after a scenecontrol: '{line}'")
                param = line[13:right_bracket_index].split(",")
                if len(param) == 2:
                    try:
                        time = int(param[0])
                        name = param[1]
                        current_timing_group.append(SceneControl(time, name))
                        continue
                    except ValueError:
                        pass
                elif len(param) == 4:
                    try:
                        time = int(param[0])
                        name = param[1]
                        param1 = float(param[2])
                        param2 = int(param[3])
                        current_timing_group.append(SceneControl(time, name, param1, param2))
                        continue
                    except ValueError:
                        pass
                if strict:
                    raise ValueError(f"{line_num}: Cannot parse scenecontrol: '{line}', should be scenecontrol(int,str) or scenecontrol(int,str,float,int)")
            elif check_prefix(line, "timing("):
                right_bracket_index = line.find(")", 7)
                if right_bracket_index == -1:
                    right_bracket_index = len(line)
                if strict and line[right_bracket_index:] != ");":
                    raise ValueError(f"{line_num}: Found extra string after a timing: '{line}'")
                param = line[7:right_bracket_index].split(",")
                if len(param) == 3:
                    try:
                        time = int(param[0])
                        bpm = float(param[1])
                        beats = float(param[2])
                        current_timing_group.append(Timing(time, bpm, beats))
                        continue
                    except ValueError:
                        pass
                if strict:
                    raise ValueError(f"{line_num}: Cannot parse timing: '{line}', should be timing(int,float,float)")
            elif check_prefix(line, "camera("):
                right_bracket_index = line.find(")", 7)
                if right_bracket_index == -1:
                    right_bracket_index = len(line)
                if strict and line[right_bracket_index:] != ");":
                    raise ValueError(f"{line_num}: Found extra string after a camera: '{line}'")
                param = line[7:right_bracket_index].split(",")
                if len(param) == 9:
                    try:
                        start_time = int(param[0])
                        x, y, z = float(param[1]), float(param[2]), float(param[3])
                        xOy, yOz, zOx = float(param[4]), float(param[5]), float(param[6])
                        easing = param[7]
                        duration = int(param[8])
                        current_timing_group.append(Camera(start_time, x, y, z, xOy, yOz, zOx, easing, duration))
                        continue
                    except ValueError:
                        pass
                if strict:
                    raise ValueError(f"{line_num}: Cannot parse camera: '{line}', should be camera(int,float,float,float,float,float,float,str,int)")
            elif check_prefix(line, "arc("):
                right_bracket_index = line.find(")", 4)
                if right_bracket_index == -1:
                    right_bracket_index = len(line)
                param = line[4:right_bracket_index].split(",")
                if len(param) == 10 or 11:
                    try:
                        start_time, end_time = int(param[0]), int(param[1])
                        start_x, end_x = float(param[2]), float(param[3])
                        easing = param[4]
                        if strict and (easing not in ArcEasing.values.keys()):
                            raise ValueError
                        easing = ArcEasing.values.get(easing.lower(), ArcEasing.LINEAR)
                        start_y, end_y = float(param[5]), float(param[6])
                        color = int(param[7])
                        hitsound = param[8]
                        if strict:
                            if param[9] == "false":
                                is_skyline = False
                            elif param[9] == "true":
                                is_skyline = True
                            else:
                                raise ValueError
                        else:
                            if param[9].lower() in ["true", "yes", "1"]:
                                is_skyline = True
                            else:
                                is_skyline = False
                        if len(param) == 11:
                            smoothness = float(param[10])
                        else:
                            smoothness = 1.0
                        arctaps: list[int] = []
                        current_timing_group.append(Arc(start_time, end_time, start_x, end_x,
                                                        easing, start_y, end_y, color,
                                                        hitsound, is_skyline, smoothness,
                                                        arctaps))
                        if line[right_bracket_index + 1] == "[":
                            arctap_end_index = line.find("]", right_bracket_index)
                            if arctap_end_index == -1:
                                arctap_end_index = len(line)
                            if strict and line[arctap_end_index:] != "];":
                                raise ValueError
                            arctap_strs = line[right_bracket_index+2:arctap_end_index].split(",")
                            for arctap_str in arctap_strs:
                                if check_prefix(arctap_str, "arctap("):
                                    right_bracket_index = arctap_str.find(")")
                                    if strict and arctap_str[right_bracket_index:] != ")":
                                        raise ValueError
                                    time = int(arctap_str[7:right_bracket_index])
                                    arctaps.append(time)
                                    continue
                                raise ValueError
                        else:
                            if strict and line[right_bracket_index:] != ");":
                                raise ValueError
                        continue
                    except ValueError:
                        pass
                if strict:
                    raise ValueError(f"{line_num}: Cannot parse arc: '{line}'")
    
    return chart

def get_precision() -> int:
    """
    Gets the current precision for formatting decimal values when writing an aff file.

    Decimal values are always formmated in fixed notation,
    rounded to decimal places specified by this option.

    This option defaults to `2`, as in the official aff files.

    Generally, the default option is sufficient for gameplay.
    Use higher values only if you want to do precise controls
    or computations using other tools.
    
    This option controls:
    | Attributes                                  | Example                                                                          |
    | ------------------------------------------- | -------------------------------------------------------------------------------- |
    | Position and smoothness in arc notes        | arc(1000,2000,**0.00**,**1.00**,s,**0.50**,**0.50**,0,none,false,**3.00**);      |
    | BPM and beat in timing events               | timing(1000,**120.00**,**4.00**);                                                |
    | Position and angle in camera events         | camera(1000,**0.00**,**900.00**,**0.00**,**90.00**,**90.00**,**90.00**,qi,1000); |
    | The first parameter in scenecontrol events  | scenecontrol(1000,arcahvdebris,**1.00**,128);                                    |
    | Position and movement vector in flick notes | flick(1000,**0.00**,**1.00**,**0.50**,**-0.50**);                                |
    
    This option **does not** control:
    | Attributes                                  | Example                                                      |
    | ------------------------------------------- | ------------------------------------------------------------ |
    | Any time value                              | timing(**1000**,120.00,4.00);<br/>hold(**1000**,**2000**,2); |
    | Note lane                                   | (1000,**3**);<br/>hold(1000,2000,**2**);                     |
    | The second parameter in scenecontrol events | scenecontrol(1000,arcahvdebris,1.00,**128**);                |
    | Timing point density factor                 | TimingPointDensityFactor: **1.125**                          |
    """
    return _PRECISION

def set_precision(precision: int) -> None:
    """
    Sets the current precision for formatting decimal values when writing an aff file.

    See `get_precision` for details.
    """
    global _PRECISION
    _PRECISION = precision