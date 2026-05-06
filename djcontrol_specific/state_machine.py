# sysex commands based on https://gist.github.com/Janiczek/04a87c2534b9d1435a1d8159c742d260 @Janiczek

import mido
import threading
from .controller_notes import *
from .fx_presets import fx_presets, FxName, FxBeatPeriod, available_fx
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


class FxSlot:
    def __init__(
        self,
        fx_name: FxName | None = None,
        beat_period: FxBeatPeriod | None = None,
        set_other_screen_then_base_screen_callback=None,
    ):
        self.is_active = False
        self.fx_name = fx_name if fx_name is not None else available_fx[0]
        self.beat_period = (
            beat_period if beat_period is not None else list(FxBeatPeriod)[0]
        )
        self._set_other_screen_then_base_screen_callback = (
            set_other_screen_then_base_screen_callback
        )

    def set_other_screen_then_base_screen(self, line1, line2, clear_pile: bool = False):
        if self._set_other_screen_then_base_screen_callback is None:
            return
        self._set_other_screen_then_base_screen_callback(line1, line2, clear_pile)

    def set_is_active(self, active: bool):
        self.is_active = active
        return self.is_active

    def switch_is_active(self):
        self.is_active = not self.is_active
        return self.is_active

    def up_one_effect(self):
        if self.fx_name not in available_fx:
            self.fx_name = available_fx[0]
            return self.fx_name
        current_index = available_fx.index(self.fx_name)
        next_index = (current_index + 1) % len(available_fx)
        self.fx_name = available_fx[next_index]
        return self.fx_name

    def down_one_effect(self):
        if self.fx_name not in available_fx:
            self.fx_name = available_fx[-1]
            return self.fx_name
        current_index = available_fx.index(self.fx_name)
        previous_index = (current_index - 1) % len(available_fx)
        self.fx_name = available_fx[previous_index]
        return self.fx_name

    def up_one_beat_period(self):
        beat_periods = list(FxBeatPeriod)
        current_index = beat_periods.index(self.beat_period)
        next_index = (current_index + 1) % len(beat_periods)
        self.beat_period = beat_periods[next_index]
        return self.beat_period

    def down_one_beat_period(self):
        beat_periods = list(FxBeatPeriod)
        current_index = beat_periods.index(self.beat_period)
        previous_index = (current_index - 1) % len(beat_periods)
        self.beat_period = beat_periods[previous_index]
        return self.beat_period


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

        self.fx1_effects = self.build_fx_slots_from_preset(fx_presets["preset_1"])
        self.fx2_effects = self.build_fx_slots_from_preset(fx_presets["preset_1"])

        self._base_screen_timer = None
        self._screen_message_queue = []
        self._screen_message_lock = threading.Lock()

        self.shift_state = False

        init(self.outport_lights)

        self.set_pads_colored_lights()
        self.set_base_screen()

    def build_fx_slots_from_preset(self, preset_entries):
        return [
            FxSlot(
                fx_name,
                beat_period,
                set_other_screen_then_base_screen_callback=self.set_other_screen_then_base_screen,
            )
            for fx_name, beat_period in preset_entries
        ]

    def switch_shift_state(self):
        self.shift_state = not self.shift_state
        self.set_pads_colored_lights()

    def switch_pad_state(self, pad_index):
        if pad_index < 0 or pad_index >= len(self.pads_state):
            raise ValueError(f"Invalid pad index: {pad_index}")

        self.pads_state[pad_index] = not self.pads_state[pad_index]

        self.set_pads_colored_lights()
        self.set_base_screen()

    def switch_fx_effect_state(self, fx_index, effect_index):
        if fx_index == 1:
            self.fx1_effects[effect_index].switch_is_active()
        elif fx_index == 2:
            self.fx2_effects[effect_index].switch_is_active()
        else:
            raise ValueError(f"Invalid fx index: {fx_index}")

        self.set_pads_colored_lights()
        self.set_base_screen()

    def set_pads_colored_lights(self):

        fx1_effects_nb = sum(1 for fx_slot in self.fx1_effects if fx_slot.is_active)
        fx2_effects_nb = sum(1 for fx_slot in self.fx2_effects if fx_slot.is_active)

        for pad_index, pad_state in enumerate(self.pads_state):
            if not pad_state:
                color = DARK
            elif self.shift_state:
                color = GREEN
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
                        color = LIGHT_BLUE
                    elif fx2_effects_nb == 2:
                        color = BLUE
                    elif fx2_effects_nb == 3:
                        color = DARK_BLUE

            set_button_color(self.outport_lights, pad_index + 1, *color)

    def _get_fx_slot_letter(self, fx_slot: FxSlot) -> str:
        fx_value = fx_slot.fx_name.value if fx_slot.fx_name else ""
        return fx_value[:1] if fx_value else "_"

    def _get_fx_slot_by_position(self, fx_index: int, effect_index: int) -> FxSlot:
        if fx_index == 1:
            return self.fx1_effects[effect_index]
        if fx_index == 2:
            return self.fx2_effects[effect_index]
        raise ValueError(f"Invalid fx index: {fx_index}")

    def _format_fx_slot_description(self, fx_index: int, effect_index: int) -> str:
        fx_slot = self._get_fx_slot_by_position(fx_index, effect_index)
        return f"{fx_slot.fx_name.value} ({fx_slot.beat_period.value})"

    def set_base_screen(self):
        fx1_1_letter = self._get_fx_slot_letter(self.fx1_effects[0])
        fx1_2_letter = self._get_fx_slot_letter(self.fx1_effects[1])
        fx1_3_letter = self._get_fx_slot_letter(self.fx1_effects[2])
        fx2_1_letter = self._get_fx_slot_letter(self.fx2_effects[0])
        fx2_2_letter = self._get_fx_slot_letter(self.fx2_effects[1])
        fx2_3_letter = self._get_fx_slot_letter(self.fx2_effects[2])

        show_text(
            self.outport_lights,
            f"{f'{fx1_1_letter} ' if self.fx1_effects[0].is_active else '_'}{f'{fx1_2_letter} ' if self.fx1_effects[1].is_active else '_'}{f'{fx1_3_letter} ' if self.fx1_effects[2].is_active else '_'}    {f' {fx2_1_letter}' if self.fx2_effects[0].is_active else '_'}{f' {fx2_2_letter}' if self.fx2_effects[1].is_active else '_'}{f' {fx2_3_letter}' if self.fx2_effects[2].is_active else '_'}",
            f"[{'X' if self.pads_state[0] else ' '}][{'X' if self.pads_state[1] else ' '}][{'X' if self.pads_state[2] else ' '}][{'X' if self.pads_state[3] else ' '}] [{'X' if self.pads_state[4] else ' '}][{'X' if self.pads_state[5] else ' '}][{'X' if self.pads_state[6] else ' '}][{'X' if self.pads_state[7] else ' '}]",
        )

    def _show_next_screen_message_or_base(self):
        with self._screen_message_lock:
            if not self._screen_message_queue:
                self._base_screen_timer = None
                next_message = None
            else:
                next_message = self._screen_message_queue.pop(0)

        if next_message is None:
            self.set_base_screen()
            return

        line1, line2 = next_message
        show_text(self.outport_lights, line1, line2)

        with self._screen_message_lock:
            self._base_screen_timer = threading.Timer(
                1.0, self._show_next_screen_message_or_base
            )
            self._base_screen_timer.start()

    def set_other_screen_then_base_screen(
        self, line1, line2, clear_pile: bool = False
    ):
        with self._screen_message_lock:
            if clear_pile:
                self._screen_message_queue.clear()
                if self._base_screen_timer is not None:
                    self._base_screen_timer.cancel()
                    self._base_screen_timer = None

            self._screen_message_queue.append((line1, line2))
            should_start_display = self._base_screen_timer is None

        if should_start_display:
            self._show_next_screen_message_or_base()

    def _get_str_from_knob_value(self, value):
        value_percent = int((value / 127) * 100)
        number_of_bars = int((value_percent / 100) * 13)
        return f"{'I' * number_of_bars*2}{'-' * (13 - number_of_bars)}   {value_percent:03d}"

    def close(self):
        with self._screen_message_lock:
            if self._base_screen_timer is not None:
                self._base_screen_timer.cancel()
                self._base_screen_timer = None
            self._screen_message_queue.clear()

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
        if ims.type == "note_off" and ims.note == SHIFT_LIKE_NOTE_INT:
            self.switch_shift_state()

        elif ims.type == "note_off" and ims.note in PADS_NOTES:
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
            control_to_fx_slot = {
                KNOB_1_1_CONTROL_INT: (1, 0),
                KNOB_1_2_CONTROL_INT: (1, 1),
                KNOB_1_3_CONTROL_INT: (1, 2),
                KNOB_2_1_CONTROL_INT: (2, 0),
                KNOB_2_2_CONTROL_INT: (2, 1),
                KNOB_2_3_CONTROL_INT: (2, 2),
            }
            fx_position = control_to_fx_slot.get(ims.control)
            if fx_position is not None:
                fx_index, effect_index = fx_position
                self.set_other_screen_then_base_screen(
                    f"{self._get_str_from_knob_value(ims.value)}",
                    self._format_fx_slot_description(fx_index, effect_index),
                    clear_pile=True,
                )

        elif ims.type == "note_on" and ims.note in SAMPLES_NOTES:
            self.set_other_screen_then_base_screen(f"SAMPLE {ims.note - 52}", "")

    def stepped_knob_turn_right(self):
        self._stepped_knob_turn(FxSlot.up_one_effect)

    def stepped_knob_turn_left(self):
        self._stepped_knob_turn(FxSlot.down_one_effect)

    def _stepped_knob_turn(self, effect_change_method):
        for effect_index, fx_slot in enumerate(self.fx1_effects):
            if not fx_slot.is_active:
                continue

            effect_change_method(fx_slot)
            fx_slot.set_other_screen_then_base_screen(
                f"FX 1 - {effect_index + 1}",
                self._format_fx_slot_description(1, effect_index),
            )

        for effect_index, fx_slot in enumerate(self.fx2_effects):
            if not fx_slot.is_active:
                continue

            effect_change_method(fx_slot)
            fx_slot.set_other_screen_then_base_screen(
                f"FX 2 - {effect_index + 1}",
                self._format_fx_slot_description(2, effect_index),
            )

    # Used to send multi semitone variations
    def get_active_fx1_channels(self) -> list:
        return self.pads_state[:4]

    def get_active_fx_effects(self) -> list:
        return [fx_slot.is_active for fx_slot in self.fx1_effects + self.fx2_effects]
