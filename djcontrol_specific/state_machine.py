# sysex commands based on https://gist.github.com/Janiczek/04a87c2534b9d1435a1d8159c742d260 @Janiczek

import mido
from .controller_notes import *
from helpers.midi_device_name import get_midi_device_name_matching_regex
from .controller_notes import (
    PAD_1_NOTE_INT,
    PAD_2_NOTE_INT,
    PAD_3_NOTE_INT,
    PAD_4_NOTE_INT,
    PAD_5_NOTE_INT,
    PAD_6_NOTE_INT,
    PAD_7_NOTE_INT,
    PAD_8_NOTE_INT,
)
from .rgb_colors import *


def sysex(*bytes):
    # This automatically adds the 0xF0 prefix and 0xF7 suffix.
    # There is also an Arturia-specific prefix (00 20 6B 7F 42) but we keep that explicit in the messages below.
    return mido.Message("sysex", data=list(bytes))


def init(port):
    # Initialization: needed for display changes. Not needed for pad color changes
    # TODO: what exactly does this do?
    port.send(
        sysex(
            0x00,
            0x20,
            0x6B,
            0x7F,
            0x42,
            0x02,
            0x02,
            0x40,
            0x6A,
            0x21,  # sometimes suggested to be 0x20. Is this Arturia vs DAW?
        )
    )
    # port.send(sysex(0x00,0x20,0x6B,0x7F,0x42, 0x01,0x00,0x40,0x03))
    # port.send(sysex(0x00,0x20,0x6B,0x7F,0x42, 0x01,0x00,0x40,0x01))
    # port.send(sysex(0x00,0x20,0x6b,0x7f,0x42, 0x04,0x01,0x60,0x0a,0x0a,0x5f,0x51,0x00))


def set_button_color(port, button, r=0x00, g=0x00, b=0x00):

    print(f"Setting button {button} color to R={r} G={g} B={b}")
    button += 3
    assert button >= 0 and button <= 11, "pad must be 0..11"
    assert r >= 0 and r <= 0x7F, "red must be 0x00..0x7F"
    assert g >= 0 and g <= 0x7F, "green must be 0x00..0x7F"
    assert b >= 0 and b <= 0x7F, "blue must be 0x00..0x7F"
    port.send(sysex(0x00, 0x20, 0x6B, 0x7F, 0x42, 0x02, 0x00, 0x16, button, r, g, b))


class StateMachine:

    def __init__(self, outport_lights=None):
        self._owns_outport_lights = outport_lights is None
        if self._owns_outport_lights:
            midi_out_light_playback_name = get_midi_device_name_matching_regex(
                is_output=True,
                regex="Minilab3 MIDI",
            )
            self.outport_lights = mido.open_output(midi_out_light_playback_name)
        else:
            self.outport_lights = outport_lights

        self.pads_state = [True, False, False, False, False, True, False, False]

        init(self.outport_lights)
        set_button_color(self.outport_lights, 1, *LIGHT_WHITE)
        set_button_color(self.outport_lights, 6, *LIGHT_BLUE)

    def switch_pad_state(self, pad_index):
        if pad_index < 0 or pad_index >= len(self.pads_state):
            raise ValueError(f"Invalid pad index: {pad_index}")
        self.pads_state[pad_index] = not self.pads_state[pad_index]

        if self.pads_state[pad_index]:
            if pad_index in [0, 1, 2, 3]:
                set_button_color(self.outport_lights, pad_index + 1, *LIGHT_WHITE)
            else:
                set_button_color(self.outport_lights, pad_index + 1, *LIGHT_BLUE)
        else:
            set_button_color(self.outport_lights, pad_index + 1, 0x00, 0x00, 0x00)

    def close(self):
        if (
            self._owns_outport_lights
            and self.outport_lights
            and not self.outport_lights.closed
        ):
            self.outport_lights.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def ims_to_lights_playback(self, ims):
        if ims.type == "note_off" and ims.note in [
            PAD_1_NOTE_INT,
            PAD_2_NOTE_INT,
            PAD_3_NOTE_INT,
            PAD_4_NOTE_INT,
            PAD_5_NOTE_INT,
            PAD_6_NOTE_INT,
            PAD_7_NOTE_INT,
            PAD_8_NOTE_INT,
        ]:
            if ims.note == PAD_1_NOTE_INT:
                self.switch_pad_state(0)
            elif ims.note == PAD_2_NOTE_INT:
                self.switch_pad_state(1)
            elif ims.note == PAD_3_NOTE_INT:
                self.switch_pad_state(2)
            elif ims.note == PAD_4_NOTE_INT:
                self.switch_pad_state(3)
            elif ims.note == PAD_5_NOTE_INT:
                self.switch_pad_state(4)
            elif ims.note == PAD_6_NOTE_INT:
                self.switch_pad_state(5)
            elif ims.note == PAD_7_NOTE_INT:
                self.switch_pad_state(6)
            elif ims.note == PAD_8_NOTE_INT:
                self.switch_pad_state(7)
