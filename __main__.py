import mido
from math import ceil
from wheel import Wheel, GrooveForm
from itertools import cycle, islice, compress
import shutil
import os

SMALLEST_FRACTION = 1 / 16
FORM = GrooveForm.ELLIPSE
REST = 1 / 100
RADIUS = 50
AXIS_SIDE = 7.375
FALL = 10

my_mapping = {
    36: "Kick",
    38: "Snare",
    42: "Hi Hat",
    46: "Bell 1",
    44: "Bell 2",
}


class Loop:
    def __init__(self, notes, title, bpm, num_bars, time_signature) -> None:
        self.title = title
        self.time_signature = time_signature
        self.bpm = bpm
        self.num_bars = num_bars
        # timing information in [0, 1)
        self.notes = {
            note: [x / (num_bars * time_signature[0]) for x in timings]
            for note, timings in notes.items()
        }

    def __str__(self) -> str:
        return f"""\
Loop (
    {self.title}
    {self.time_signature[0]}/{self.time_signature[1]}
    {self.bpm} BPM
    {self.num_bars} bars
    {len(self.notes.keys())} different notes
    {self.notes.keys()}
)"""

    def as_wheels(self) -> list[Wheel]:
        info = f"""\
{self.num_bars} bars
{self.bpm} BPM
{self.time_signature[0]}/{self.time_signature[1]}
{self.bpm / (self.time_signature[0]*self.num_bars)} rpm"""
        wheels = []
        for key, timings in self.notes.items():
            title = f"{self.title}"
            subtitle = f"{my_mapping[key]}"
            double_wheel = False
            for i in range(len(timings)):
                if (timings[i] - timings[i - 1]) % 1 < SMALLEST_FRACTION:
                    double_wheel = True
                    break
            if double_wheel:
                try:
                    timings1, timings2 = disentangle(timings)
                    wheels.append(
                        make_wheel(timings1, title, f"{subtitle}\nWheel 1", info)
                    )
                    wheels.append(
                        make_wheel(timings2, title, f"{subtitle}\nWheel 2", info)
                    )
                except ValueError:
                    print(title.replace("\n", " "), "is packed to thightly")
                    exit(1)
            else:
                wheels.append(
                    make_wheel(timings, title, f"{subtitle}\nsingle wheel", info)
                )
        return wheels


def disentangle(timings: list[float]) -> tuple[float, float]:
    initial = list(islice(cycle([True, False]), len(timings)))
    for i in range(len(timings)):
        if (timings[i] - timings[i - 2]) % 1 < SMALLEST_FRACTION:
            raise ValueError
    for i in range(2 ** len(timings)):
        flipper = bool_list_from_int(i, len(timings))
        to_list_1 = list(map(lambda x, y: x ^ y, initial.copy(), flipper))
        timings1 = list(compress(timings.copy(), to_list_1.copy()))
        to_list_2 = map(lambda x: not x, to_list_1)
        timings2 = list(compress(timings.copy(), to_list_2))
        if is_ok(timings1) and is_ok(timings2):
            assert len(timings1) + len(timings2) == len(timings)
            return (timings1, timings2)
    raise ValueError


def bool_list_from_int(n: int, len: int) -> list[bool]:
    return list(reversed([(1 << i) & n == 0 for i in range(len)]))


def is_ok(timings):
    for i in range(len(timings)):
        if (timings[i] - timings[i - 1]) % 1 < SMALLEST_FRACTION:
            return False
    return True


def make_wheel(timing: list, title: str, subtitle: str, info: str) -> Wheel:
    wheel = Wheel(title, RADIUS, AXIS_SIDE, subtitle, info)
    for i in range(len(timing)):
        wheel.add_trigger(
            timing[i], FORM, min((timing[i] - timing[i - 1] - REST) % 1, 0.2), FALL
        )
    return wheel


def load_midi(name) -> Loop:
    file = mido.MidiFile(f"midi/{name}.mid")
    if file.type != 0:
        assert False, "this is not a single track file"

    current_time = 0
    time_msg = None
    tempo = None
    notes = {}
    for msg in file.tracks[0]:
        current_time += msg.time
        match msg.type:
            case "note_on":
                time_list = notes.get(msg.note)
                if time_list:
                    time_list.append(current_time)
                else:
                    notes[msg.note] = [current_time]
            case "time_signature":
                time_msg = msg
            case "set_tempo":
                tempo = msg.tempo
    notes = {
        key: [t * time_msg.denominator / file.ticks_per_beat / 4 for t in timings]
        for key, timings in notes.items()
    }

    maximum = max([max(x) for x in notes.values()])
    num_bars = ceil(maximum / time_msg.numerator)
    return Loop(
        notes,
        name,
        mido.tempo2bpm(tempo),
        num_bars,
        (time_msg.numerator, time_msg.denominator),
    )


def make_out_folder(subfolder_name):
    path = f"./out/{subfolder_name}"
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


if __name__ == "__main__":
    name = "rheel"
    loop = load_midi(name)
    make_out_folder(name)
    for wheel in loop.as_wheels():
        subt = wheel.subtitle.replace("\n", " ")
        wheel.get_svg().save_svg(f"out/{name}/{subt}.svg")
