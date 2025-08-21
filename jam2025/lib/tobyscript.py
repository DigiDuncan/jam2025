import collections.abc
import json
import re
from types import NoneType
from typing import Any, ClassVar, Literal, TypedDict, cast

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

def flatten(x: Any) -> list:
    if isinstance(x, collections.abc.Iterable):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


class Settings(TypedDict):
    """
    * `char_name`: replaces `\\[C]`
    * `g`: replaces `\\[G]`
    * `item`: replaces `\\[I]`
    * `one`: replaces `\\[1]`
    * `two`: replaces `\\[2]`
    * `fix_black`: replaces all black text with white`
    """
    char_name: str
    g: str
    item: str
    one: str
    two: str
    fix_black: bool


# SETTINGS
settings: Settings = {
    "char_name": "Player",
    "g": "0",
    "item": "Monster Candy",  # item ID 1
    "one": "0",
    "two": "0",
    "fix_black": True
}

replacements = [
    ("\\z4", "∞"),
    ("&", "\n"),
    ("\\*Z", "[Z]"),
    ("\\*X", "[X]"),
    ("\\*C", "[C]"),
    ("\\*A", "[A]"),
    ("\\*D", "[D]")
]


class Event:
    def __init__(self, data: str | int | None = None):
        self.data = data

    def __str__(self) -> str:
        data = repr(self.data) if self.data is not None else ''
        data = data.replace("\n", "\\n")
        return f"<{self.__class__.__name__} {data}".strip() + ">"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def tobyscript(self) -> str:
        raise NotImplementedError

class TextEvent(Event):
    def __init__(self, data: str):
        """Represents text to display on the screen."""
        super().__init__(data)
        self.data = cast(str, self.data)

    @property
    def tobyscript(self) -> str:
        s = self.data
        for old, new in replacements:
            s = s.replace(new, old)
        return s

class PauseEvent(Event):
    def __init__(self, data: int):
        """Delays an amount of time before continuing."""
        super().__init__(data)
        self.data = cast(int, self.data)

    @property
    def tobyscript(self) -> str:
        return f"^{self.data}"

class ColorEvent(Event):
    NAME_MAP: ClassVar[dict[str, str]] = {
                "R": "red",
                "G": "green",
                "W": "white",
                "Y": "yellow",
                "B": "blue",
                "O": "orange",
                "L": "azure",
                "P": "magenta",
                "p": "pink"
            }

    COLOR_MAP: ClassVar[dict[str, tuple[int, int, int, int]]] = {
                "R": (0xFF, 0x00, 0x00, 0xFF),
                 "G": (0x00, 0xFF, 0x00, 0xFF),
                 "W": (0xFF, 0xFF, 0xFF, 0xFF),
                 "Y": (0xFF, 0xFF, 0x00, 0xFF),
                 "B": (0x00, 0x00, 0xFF, 0xFF),
                 "O": (0xFF, 0xA0, 0x40, 0xFF),
                 "L": (0x0E, 0xC0, 0xFD, 0xFF),
                 "P": (0xFF, 0x00, 0xFF, 0xFF),
                 "p": (0xFF, 0xBB, 0xD4, 0xFF)
            }

    def __init__(self, data: str):
        """Changes the color of upcoming text.

        * `self.name`: `str` - the name of the color.
        * `self.rgba`: `tuple` - the color as an RGBA tuple (as rendered in Undertale).
        * `self.rgb`: `tuple` - the color as an RGB tuple (as rendered in Undertale).
        """
        super().__init__(data)
        self.data = cast(str, self.data)

    @property
    def name(self) -> str | None:
        if self.data == "X":
            return "white" if settings["fix_black"] else "black"
        else:
            return self.NAME_MAP.get(self.data)

    @property
    def rgba(self) -> RGBA | None:
        if self.data == "X":
            return (0xFF, 0xFF, 0xFF, 0xFF) if settings["fix_black"] else (0x00, 0x00, 0x00, 0xFF)
        else:
            return self.COLOR_MAP.get(self.data)

    @property
    def rgb(self) -> RGB | None:
        return self.rgba[0:3] if self.rgba else None

    @property
    def tobyscript(self) -> str:
        return f"\\{self.data}"

class EmotionEvent(Event):
    def __init__(self, data: int):
        """Denotes an emotion for the character on screen (if any) to display."""
        super().__init__(data)

    @property
    def tobyscript(self) -> str:
        return f"\\E{self.data}"

class FaceEvent(Event):
    FACE_MAP: ClassVar[dict[int, str | None]] = {
        0: None,
        1: "Toriel",
        2: "Flowey",
        3: "Sans",
        4: "Papyrus",
        5: "Undyne",
        6: "Alphys",
        7: "Asgore",
        8: "Mettaton",
        9: "Asriel"
    }

    def __init__(self, data: int):
        """Denotes a character's face to display on screen."""
        super().__init__(data)
        self.data = cast(int, self.data)

    @property
    def character(self) -> str | None:
        return self.FACE_MAP.get(self.data, "Unknown")

    @property
    def tobyscript(self) -> str:
        return f"\\F{self.data}"

class AnimationEvent(Event):
    def __init__(self, data: int):
        """Denotes an animation. Hard to know what this means in context of the game."""
        super().__init__(data)
        self.data = cast(int, self.data)

    @property
    def tobyscript(self) -> str:
        return f"\\M{self.data}"

class SoundEvent(Event):
    def __init__(self, data: str):
        """Manipulate the current sound in some way.

        * `self.type`: `str` - The type of event this is:
            - `on`: text beeps on
            - `off`: text beeps off
            - `phone`: play phone sfx
        """
        super().__init__(data)
        self.data = cast(Literal["-", "+", "p"], self.data)

    @property
    def type(self) -> str:
        match self.data:
            case "-":
                return "off"
            case "+":
                return "on"
            case "p":
                return "phone"
            case _:
                raise ValueError

    @property
    def tobyscript(self) -> str:
        return f"\\S{self.data}"

class TextSizeEvent(Event):
    def __init__(self, data: str):
        """Change the upcoming text size.

        `self.small`: `bool` - whether or not we're changing the text size to small (or normal, if False.)"""
        super().__init__(data)
        self.data = cast(str, self.data)

    @property
    def small(self) -> bool:
        return True if self.data == "-" else False

    @property
    def tobyscript(self) -> str:
        return f"\\T{self.data}"

class SpeakerEvent(Event):
    SPEAKER_MAP: ClassVar[dict[str, str]] = {
        "T": "Toriel",
        "t": "Toriel (Sans)",
        "0": "Default",
        "S": "Default (no sound)",
        "F": "Flowey (evil)",
        "s": "Sans",
        "P": "Papryus",
        "M": "Mettaton",
        "U": "Undyne",
        "A": "Alphys",
        "a": "Asgore",
        "R": "Asriel"
    }

    def __init__(self, data: str):
        """Change the current speaker. Used to change text beep sound, typically.

        * `self.speaker`: the name of the speaker (as listed in Undertale Dialog Simulator.)
        """
        super().__init__(data)
        self.data = cast(str, self.data)

    @property
    def speaker(self) -> str:
        return self.SPEAKER_MAP.get(self.data, "Unknown")

    @property
    def tobyscript(self) -> str:
        return f"\\T{self.data}"

class WaitEvent(Event):
    def __init__(self):
        """Wait for user input."""
        super().__init__()
        self.data = cast(NoneType, self.data)

    @property
    def tobyscript(self) -> str:
        return "/"

class SkipEvent(Event):
    def __init__(self):
        """Continue to the next text box (or rather, clear the current box contents.)"""
        super().__init__()
        self.data = cast(NoneType, self.data)

    @property
    def tobyscript(self) -> str:
        return "%"

class CloseEvent(Event):
    def __init__(self):
        """Close the current text box. (Usually denotes the end of an interaction, but not always!)"""
        super().__init__()
        self.data = cast(NoneType, self.data)

    @property
    def tobyscript(self) -> str:
        return "%%"


def parse(s: str) -> list[Event]:
    """Take a TobyScript string and return an ordered list of Events."""
    events: list[Event] = []
    current_string = ""

    one_way_replacements = [
        ("\\[C]", settings["char_name"]),
        ("\\[I]", settings["item"]),
        ("\\[G]", settings["g"]),
        ("\\[1]", settings["one"]),
        ("\\[2]", settings["two"]),
        ("\\>1", " "),
        ("\\C", "")
    ]

    for old, new in replacements:
        s = s.replace(old, new)
    for old, new in one_way_replacements:
        s = s.replace(old, new)

    s = s.rstrip()

    current_string = ""
    skip = False
    for i in range(len(s)):
        current_char = s[i]

        if skip:
            skip = False
            continue

        # You have to have that % check because both % and %% are flags.
        if current_char in "^\\/&%" and current_string != "%":
            if current_string:
                events.append(TextEvent(current_string))
            current_string = ""

        current_string += current_char

        if re.match(r"\^\d", current_string):
            # Handle the weird postfix thing
            if i != len(s) - 1 and events and isinstance(events[-1], TextEvent):
                events[-1].data += s[i + 1]
                skip = True
            events.append(PauseEvent(int(current_string[1])))
            current_string = ""
        elif re.match(r"\\[RGWYXBOLPp]", current_string):
            events.append(ColorEvent(current_string[1]))
            current_string = ""
        elif re.match(r"\\E\d", current_string):
            events.append(EmotionEvent(int(current_string[2])))
            current_string = ""
        elif re.match(r"\\F\d", current_string):
            events.append(FaceEvent(int(current_string[2])))
            current_string = ""
        elif re.match(r"\\M\d", current_string):
            events.append(AnimationEvent(int(current_string[2])))
            current_string = ""
        elif re.match(r"\\S[-+p]", current_string):
            events.append(SoundEvent(current_string[2]))
            current_string = ""
        elif re.match(r"\\T[-+]", current_string):
            events.append(TextSizeEvent(current_string[2]))
            current_string = ""
        elif re.match(r"\\T\w", current_string):
            events.append(SpeakerEvent(current_string[2]))
            current_string = ""
        elif current_string == "/":
            events.append(WaitEvent())
            current_string = ""
        elif re.match(r"%[^%]+", current_string) or (current_string == "%" and i == len(s) - 1):
            events.append(SkipEvent())
            current_string = ""
        elif current_string == "%%":
            events.append(CloseEvent())

    return events

def parse_lines(s: str, *, split_on: str | None = None, merge: Literal["none", "close", "all"] = "none") -> list[list[Event]]:
    """Parse multiple TobyScript strings into an ordered list of ordered lists of Events.

    * s: `str` - The lines to parse.
    * split_on: `str` - The sequence to `.split()` the string with to denote line breaks. If `None`, defaults to calling `.splitlines()`.
    * merge: `str` - One of either `'none'`, `'close'`, or `'all'`.
    `none` returns the lists split as they were by the split functions.
    `close` returns the lists delimited by `CloseEvent`s.
    `all` returns a sequence of length 1, where all events are combined into one list."""
    event_lists = []

    if split_on is None:
        lines = s.splitlines()
    else:
        lines = s.split(split_on)

    for line in lines:
        parsed_line = parse(line)
        event_lists.append(parsed_line)

    if merge == "none":
        return event_lists
    if merge == "all":
        return [flatten(event_lists)]
    elif merge == "close":
        return_lists = []
        flattened = flatten(event_lists)
        current_list = []
        for event in flattened:
            current_list.append(event)
            if isinstance(event, CloseEvent):
                return_lists.append(current_list)
                current_list = []
        return return_lists

def to_JSON(li: list[Event], **kwargs: bool | None) -> str:
    """Create a JSON-serializable version of a list of `Event`s."""
    out = []
    for e in li:
        d = {}
        d["type"] = e.__class__.__name__
        d["data"] = e.data
        out.append(d)
    return json.dumps(out, **kwargs)  # type: ignore -- ugh

def to_tobyscript(li: list[Event]) -> str:
    s = ""
    for e in li:
        if not isinstance(e, PauseEvent):
            s += e.tobyscript
        else:
            a = s[-1]
            s = s[:-1]
            s += e.tobyscript
            s += a
    return s

def test(s: str) -> None:
    e = parse(s)
    print(s)
    print(e)
    print(to_tobyscript(e))


if __name__ == "__main__":
    test(R"\W* Howdy^2!&* I'm\Y FLOWEY\W.^2 &* \YFLOWEY\W the \YFLOWER\W!/")
