import pretty_errors
import drawSvg as draw
from math import sin, cos, tau

MM_IN_PX = 3.543307  # px

MAX_FALL = 20

FONT = "monospace"
TITLE = 6 * MM_IN_PX
SUB_TITLE = 4 * MM_IN_PX
INFO = 3 * MM_IN_PX


class GrooveForm:
    FALL = -1
    STAY = 0
    LINEAR = 1
    ELLIPSE = 2
    CUBIC = 3
    O_CUBIC = 4


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

    def add_trigger(self, pos, form, len, fall) -> None:
        self.triggers.append((pos * tau, form, len * tau, fall * MM_IN_PX))

    def add_triggers(self, arr) -> None:
        for args in arr:
            self.add_trigger(*args)

    def get_svg(self, cut_color, draw_color) -> draw.Drawing:
        size = (self.radius + MAX_FALL) * 2
        img = draw.Drawing(size, size, origin="center")
        axis = draw.Rectangle(
            -self.axis_side / 2,
            -self.axis_side / 2,
            self.axis_side,
            self.axis_side,
            fill="none",
            stroke=cut_color,
        )
        img.append(axis)
        img.append(self._get_path(cut_color))
        [img.append(x) for x in self._get_text_elements(draw_color)]
        img.setPixelScale(1)
        return img

    def _get_path(self, cut_color) -> draw.Path:
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
        path = draw.Path(stroke_width=2, stroke=cut_color, fill="none")
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
                        includeM=False,
                    )
                case GrooveForm.LINEAR:
                    path.L(*to_cartesian(self.radius + piece["fall"], piece["stop"]))
                case GrooveForm.ELLIPSE:
                    path.A(
                        self.radius + piece["fall"],
                        self.radius,
                        (piece["start"] + piece["stop"]) / 2,
                        False,
                        False,
                        *to_cartesian(self.radius + piece["fall"], piece["stop"]),
                    )
                case GrooveForm.CUBIC:
                    path.C(
                        *to_cartesian(
                            (self.radius) / cos((piece["stop"] - piece["start"]) / 2),
                            (piece["start"] + piece["stop"]) / 2,
                        ),
                        *to_cartesian(
                            (self.radius + piece["fall"])
                            / cos((piece["stop"] - piece["start"]) / 2),
                            (piece["start"] + piece["stop"]) / 2,
                        ),
                        *to_cartesian(self.radius + piece["fall"], piece["stop"]),
                    )
                case GrooveForm.O_CUBIC:
                    delta = piece["stop"] - piece["start"]
                    path.C(
                        *to_cartesian(
                            (self.radius) / cos(2 * delta / 3),
                            piece["start"] + delta / 3,
                        ),
                        *to_cartesian(
                            (self.radius + piece["fall"]) / cos(delta / 4),
                            piece["start"] + delta / 4,
                        ),
                        *to_cartesian(self.radius + piece["fall"], piece["stop"]),
                    )
        path.Z()
        return path

    def _get_text_elements(self, draw_color) -> list[draw.Text]:
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
                    fill=draw_color,
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
                    fill=draw_color,
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
                    fill=draw_color,
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
                    fill=draw_color,
                    text_anchor="end",
                    font_family=FONT,
                )
            )
        return text_fields


if __name__ == "__main__":
    wheel = Wheel("Test", 50, 4)
    wheel.add_triggers(
        [
            (0.0, GrooveForm.ELLIPSE, 1 / 16, 7),
            (0.25, GrooveForm.ELLIPSE, 1 / 16, 10),
            (0.5, GrooveForm.ELLIPSE, 1 / 16, 14),
            (0.75, GrooveForm.ELLIPSE, 1 / 16, 18),
        ]
    )
    wheel.get_svg("#ff0000", "#000000").saveSvg("out/test.svg")


# if __name__ == "__main__":
#     falls = [8, 10, 14]
#     distances = [12, 16, 24]
#     rests = [400, 100, 50]

#     for fall in falls:
#         wheel = Wheel("Test Wheel", 50, 4, fall, f"fall = {fall}")

#         current_pos = 0
#         for d in distances:
#             wheel.add_trigger(current_pos, GrooveForm.ELLIPSE, 1 / 16)
#             for r in rests:
#                 current_pos += 1 / d
#                 wheel.add_trigger(current_pos, GrooveForm.ELLIPSE, 1 / d - 1 / r)
#             current_pos += 1 / 8
#         wheel.get_svg(cut_color="#ff0000", draw_color="#000000").saveSvg(
#             f"out/test{fall}.svg"
#         )
