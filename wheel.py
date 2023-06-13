import drawsvg as draw
from math import sin, cos, tau

MM_IN_PX = 3.7795275591  # px

CUT_STROKE_WIDTH = 0.01 * MM_IN_PX
CUT_STROKE_COLOR = "#000000"
DRAW_COLOR = "#ff0000"

MAX_FALL = 20 * MM_IN_PX

MIN_RISE_LEN_FRAC_OVER_1 = 16

FONT = "monospace"
TITLE = 3 * MM_IN_PX
SUB_TITLE = TITLE * 0.75
INFO = TITLE * 0.5


class GrooveForm:
    FALL = -1
    STAY = 0
    ELLIPSE = 2


to_cartesian = lambda r, theta: (r * cos(theta), r * sin(theta))


class Wheel:
    def __init__(
        self,
        title: str,
        radius: float,
        axis_side: float,
        subtitle: str = "",
        info: str = "",
    ) -> None:
        self.title = title
        self.subtitle = subtitle
        self.info = info
        self.radius = radius * MM_IN_PX
        self.axis_side = axis_side * MM_IN_PX
        self.triggers = []

    # receives the timing informations in [0,1) and saves them as [0, tau)
    def add_trigger(self, pos, form, len, fall) -> None:
        self.triggers.append((pos * tau, form, len * tau, fall * MM_IN_PX))

    def add_triggers(self, arr) -> None:
        for args in arr:
            self.add_trigger(*args)

    def get_svg(self) -> draw.Drawing:
        size = (self.radius + MAX_FALL) * 2
        img = draw.Drawing(size, size, origin="center", context=draw.Context(True))
        axis = draw.Rectangle(
            -self.axis_side / 2,
            -self.axis_side / 2,
            self.axis_side,
            self.axis_side,
            fill="none",
            stroke=CUT_STROKE_COLOR,
            stroke_width=CUT_STROKE_WIDTH,
        )
        img.append(axis)
        img.append(self._get_path())
        [img.append(x) for x in self._get_text_elements()]
        img.set_pixel_scale(1)
        return img

    def _get_path(self) -> draw.Path:
        self.triggers.sort(key=lambda x: x[0])
        pieces = []
        for i, (pos, form, len, fall) in enumerate(self.triggers):
            pieces.append(
                {
                    "start": self.triggers[i - 1][0],
                    "stop": pos - len,
                    "form": GrooveForm.STAY,
                }
            )
            pieces.append({"start": pos - len, "stop": pos, "form": form, "fall": fall})
            pieces.append({"start": pos, "stop": pos, "form": GrooveForm.FALL})
        path = draw.Path(
            stroke_width=CUT_STROKE_WIDTH, stroke=CUT_STROKE_COLOR, fill="none"
        )
        path.M(*to_cartesian(self.radius, pieces[0]["start"]))
        for piece in pieces:
            match piece["form"]:
                case GrooveForm.FALL:
                    path.L(*to_cartesian(self.radius, piece["stop"]))
                case GrooveForm.STAY:
                    path.arc(
                        0,
                        0,
                        self.radius,
                        piece["start"] * 360 / tau,
                        piece["stop"] * 360 / tau,
                        include_m=False,
                    )
                case GrooveForm.ELLIPSE:
                    if (piece["stop"] - piece["start"]) % tau > (tau / MIN_RISE_LEN_FRAC_OVER_1):
                        path.A(
                            self.radius + piece["fall"],
                            self.radius,
                            (piece["start"] + piece["start"] + tau / MIN_RISE_LEN_FRAC_OVER_1) / 2,
                            False,
                            True,
                            *to_cartesian(
                                self.radius + piece["fall"],
                                piece["start"] + tau / MIN_RISE_LEN_FRAC_OVER_1,
                            ),
                        )
                        path.arc(
                            0,
                            0,
                            self.radius + piece["fall"],
                            (piece["start"] + tau / MIN_RISE_LEN_FRAC_OVER_1) * 360 / tau,
                            piece["stop"] * 360 / tau,
                            include_m=False,
                        )
                    else:
                        path.A(
                            self.radius + piece["fall"],
                            self.radius,
                            (piece["start"] + piece["stop"]) / 2,
                            False,
                            True,
                            *to_cartesian(self.radius + piece["fall"], piece["stop"]),
                        )
        path.Z()
        return path

    def _get_text_elements(self) -> list[draw.Text]:
        text_fields = []
        if self.subtitle:
            lines = self.subtitle.splitlines()
            height = TITLE * 4 / 3 + (len(lines) - 1) * SUB_TITLE * 4 / 3 + SUB_TITLE
            text_fields.append(
                draw.Text(
                    self.title,
                    TITLE,
                    self.axis_side,
                    height / 2,
                    valign="top",
                    fill=DRAW_COLOR,
                    font_family=FONT,
                )
            )
            text_fields.append(
                draw.Text(
                    lines,
                    SUB_TITLE,
                    self.axis_side,
                    height / 2 - TITLE * 4 / 3,
                    valign="top",
                    fill=DRAW_COLOR,
                    font_style="italic",
                    font_family=FONT,
                )
            )
        else:
            text_fields.append(
                draw.Text(
                    self.title,
                    TITLE,
                    self.axis_side,
                    0,
                    valign="middle",
                    fill=DRAW_COLOR,
                    font_family=FONT,
                )
            )
        if self.info:
            text_fields.append(
                draw.Text(
                    self.info,
                    INFO,
                    -self.axis_side,
                    0,
                    valign="middle",
                    fill=DRAW_COLOR,
                    text_anchor="end",
                    font_family=FONT,
                )
            )
        return text_fields


def make_test_1():
    falls = [8, 10, 14]
    distances = [12, 16, 24]
    REST = 1 / 50

    wheel = Wheel("Test Wheel", 50, 7.345)
    current_pos = 0
    for fall in falls:
        wheel.add_trigger(current_pos, GrooveForm.ELLIPSE, 1 / 16, fall)
        for d in distances:
            current_pos += 1 / d
            if fall != 14:
                wheel.add_trigger(current_pos, GrooveForm.ELLIPSE, 1 / d - REST, fall)
            else:
                wheel.add_trigger(current_pos, GrooveForm.ELLIPSE, 1 / d, fall)
        current_pos += 1 / 8
    wheel.get_svg().save_svg("out/test.svg")


def make_test_2():
    falls = [10, 14]

    REST = 1 / 64

    wheel = Wheel("Test Wheel 2", 50, 7.375)
    current_pos = 0
    for fall in falls:
        wheel.add_trigger(current_pos, GrooveForm.ELLIPSE, 1 / 24, fall)
        for i in range(3):
            current_pos += 1 / 12
            wheel.add_trigger(current_pos, GrooveForm.ELLIPSE, 1 / 24 - REST, fall)
        current_pos += 1 / 4
    wheel.get_svg().save_svg("out/test.svg")


def make_test_3_and_4():
    beats = 16
    max_rest = 1 / 32
    get_length = lambda i: (1 - i * max_rest) / beats

    wheel = Wheel("Test Wheel 3", 55, 7.375, "Fall = 16 mm")
    for i in range(beats):
        wheel.add_trigger(i / beats, GrooveForm.ELLIPSE, get_length(i), 16)
    wheel.get_svg().save_svg("out/test_3.svg")

    wheel = Wheel("Test Wheel 4", 55, 7.375, "Fall = 13 mm")
    for i in range(beats):
        wheel.add_trigger(i / beats, GrooveForm.ELLIPSE, get_length(i), 13)
    wheel.get_svg().save_svg("out/test_4.svg")


def test():
    wheel = Wheel("bb", 50, 7.375)
    wheel.add_trigger(0, GrooveForm.ELLIPSE, 1 / 16, 12)
    wheel.add_trigger(1 / 4, GrooveForm.ELLIPSE, 1 / 16, 12)
    wheel.add_trigger(1 / 2, GrooveForm.ELLIPSE, 1 / 16, 12)
    wheel.add_trigger(3 / 4, GrooveForm.ELLIPSE, 1 / 16, 12)
    wheel.get_svg().save_svg("out/test.svg")


if __name__ == "__main__":
    make_test_3_and_4()
