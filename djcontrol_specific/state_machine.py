# sysex commands based on https://gist.github.com/Janiczek/04a87c2534b9d1435a1d8159c742d260 @Janiczek

import mido
import threading
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


def set_button_color(port, button, r=0x00, g=0x00, b=0x00):
    button += 3
    assert button >= 0 and button <= 11, "pad must be 0..11"
    assert r >= 0 and r <= 0x7F, "red must be 0x00..0x7F"
    assert g >= 0 and g <= 0x7F, "green must be 0x00..0x7F"
    assert b >= 0 and b <= 0x7F, "blue must be 0x00..0x7F"

    # for Arturia: 0x02, 0x01 - for DAW : 0x02, 0x02 - for User mode : 0x02, 0x00
    port.send(sysex(0x00, 0x20, 0x6B, 0x7F, 0x42, 0x02, 0x01, 0x16, button, r, g, b))


def show_text(port, line1, line2):
    str1 = list(bytearray(line1, "ascii"))
    str2 = list(bytearray(line2, "ascii"))
    port.send(
        sysex(
            0x00,
            0x20,
            0x6B,
            0x7F,
            0x42,
            0x04,
            0x01,
            0x60,
            0x01,
            *str2,
            0x00,
            0x02,
            *str1,
        )
    )


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
        self.fx1_effects = [False, False, False]
        self.fx2_effects = [False, False, False]

        self._base_screen_timer = None

        init(self.outport_lights)

        self.set_pads_colored_lights()
        self.set_base_screen()

    def switch_pad_state(self, pad_index):
        if pad_index < 0 or pad_index >= len(self.pads_state):
            raise ValueError(f"Invalid pad index: {pad_index}")

        self.pads_state[pad_index] = not self.pads_state[pad_index]

        self.set_pads_colored_lights()

    def switch_fx_effect_state(self, fx_index, effect_index):
        if fx_index == 1:
            self.fx1_effects[effect_index] = not self.fx1_effects[effect_index]
        elif fx_index == 2:
            self.fx2_effects[effect_index] = not self.fx2_effects[effect_index]
        else:
            raise ValueError(f"Invalid fx index: {fx_index}")

        self.set_pads_colored_lights()
        self.set_base_screen()

    def set_pads_colored_lights(self):

        fx1_effects_nb = self.fx1_effects.count(True)
        fx2_effects_nb = self.fx2_effects.count(True)

        for pad_index, pad_state in enumerate(self.pads_state):
            if not pad_state:
                color = DARK
            else:
                if pad_index in [0, 1, 2, 3]:
                    if fx1_effects_nb == 0:
                        color = WHITE
                    elif fx1_effects_nb == 1:
                        color = YELLOW
                    elif fx1_effects_nb == 2:
                        color = ORANGE
                    elif fx1_effects_nb == 3:
                        color = RED
                else:
                    if fx2_effects_nb == 0:
                        color = WHITE
                    elif fx2_effects_nb == 1:
                        color = GREEN
                    elif fx2_effects_nb == 2:
                        color = BLUE
                    elif fx2_effects_nb == 3:
                        color = VIOLET

            set_button_color(self.outport_lights, pad_index + 1, *color)

    def set_base_screen(self):
        show_text(
            self.outport_lights,
            "echo - rvrb - fltr",
            f"[{'X' if self.fx1_effects[0] else ' '}][{'X' if self.fx1_effects[1] else ' '}][{'X' if self.fx1_effects[2] else ' '}] [{'X' if self.fx2_effects[0] else ' '}][{'X' if self.fx2_effects[1] else ' '}][{'X' if self.fx2_effects[2] else ' '}]",
        )

    def set_other_screen_then_base_screen(self, line1, line2):
        show_text(self.outport_lights, line1, line2)
        if self._base_screen_timer is not None:
            self._base_screen_timer.cancel()
        self._base_screen_timer = threading.Timer(1.0, self.set_base_screen)
        self._base_screen_timer.start()

    def _get_str_from_knob_value(self, value):
        value_percent = int((value / 127) * 100)
        number_of_bars = int((value_percent / 100) * 13)
        return f"{'I' * number_of_bars*2}{'-' * (13 - number_of_bars)}   {value_percent:03d}"

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

    def ims_to_playback(self, ims):
        if ims.type == "note_off" and ims.note in PADS_NOTES:
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

        elif ims.type == "note_on" and ims.note in FX_ACTIVATE_NOTES:
            if ims.note == FX1_1_ACTIVATE_NOTE_INT:
                self.switch_fx_effect_state(1, 0)
            elif ims.note == FX1_2_ACTIVATE_NOTE_INT:
                self.switch_fx_effect_state(1, 1)
            elif ims.note == FX1_3_ACTIVATE_NOTE_INT:
                self.switch_fx_effect_state(1, 2)
            elif ims.note == FX2_1_ACTIVATE_NOTE_INT:
                self.switch_fx_effect_state(2, 0)
            elif ims.note == FX2_2_ACTIVATE_NOTE_INT:
                self.switch_fx_effect_state(2, 1)
            elif ims.note == FX2_3_ACTIVATE_NOTE_INT:
                self.switch_fx_effect_state(2, 2)

        elif ims.type == "control_change" and ims.control in KNOBS_CONTROLS:
            if ims.control == KNOB_1_1_CONTROL_INT:
                self.set_other_screen_then_base_screen(
                    f"{self._get_str_from_knob_value(ims.value)}", f"FX1 ECHO (1/2)"
                )
            elif ims.control == KNOB_1_2_CONTROL_INT:
                self.set_other_screen_then_base_screen(
                    f"{self._get_str_from_knob_value(ims.value)}", f"FX1 REVERB (25%)"
                )
            elif ims.control == KNOB_1_3_CONTROL_INT:
                self.set_other_screen_then_base_screen(
                    f"{self._get_str_from_knob_value(ims.value)}", f"FX1 FILTER (1)"
                )
            elif ims.control == KNOB_2_1_CONTROL_INT:
                self.set_other_screen_then_base_screen(
                    f"{self._get_str_from_knob_value(ims.value)}", f"FX2 ECHO (1/2)"
                )
            elif ims.control == KNOB_2_2_CONTROL_INT:
                self.set_other_screen_then_base_screen(
                    f"{self._get_str_from_knob_value(ims.value)}", f"FX2 REVERB (25%)"
                )
            elif ims.control == KNOB_2_3_CONTROL_INT:
                self.set_other_screen_then_base_screen(
                    f"{self._get_str_from_knob_value(ims.value)}", f"FX2 FILTER (1)"
                )

        elif ims.type == "note_on" and ims.note in SAMPLES_NOTES:
            self.set_other_screen_then_base_screen(f"SAMPLE {ims.note - 52}", "")

    # Used to send multi semitone variations
    def get_active_fx1_channel(self):
        return self.pads_state[:4]
