import pyautogui
import mido

pyautogui.FAILSAFE = False
from helpers.midi_device_name import get_midi_device_name_matching_regex
from minilab_specific.fx_presets import (
    available_fx,
    available_beat_periods_per_fx,
    get_nb_of_steps_until_next_available_effect,
)
from .user_config import (
    LAYOUT_4_DECKS_HORIZONTAL,
)
from helpers.rekordbox_process import focus_rekordbox_window
from helpers.screenshot_and_show import screenshot_and_show

TOP_MENU_FEATURE_1 = (200, 54)
TOP_MENU_FEATURE_2 = (237, 54)
TOP_MENU_FEATURE_3 = (274, 54)
TOP_MENU_FEATURE_4 = (311, 54)
TOP_MENU_FEATURE_5 = (348, 54)

FX1_SLOT_1_DROPDOWN_ARROW = (450, 85)
FX1_SLOT_2_DROPDOWN_ARROW = (590, 85)
FX1_SLOT_3_DROPDOWN_ARROW = (730, 85)
FX2_SLOT_1_DROPDOWN_ARROW = (1284, 85)
FX2_SLOT_2_DROPDOWN_ARROW = (1424, 85)
FX2_SLOT_3_DROPDOWN_ARROW = (1564, 85)

FX_SLOT_COUNT = 6
FX_SELECT_NOTE_BASE = 31
FX_BEAT_DOWN_NOTE_BASE = 81


def send_key_to_rekordbox(
    key, delay_after: float = 0, hold_time: float = 0, shall_refocus_on_rekordbox=False
):
    if shall_refocus_on_rekordbox:
        focus_rekordbox_window()

    if hold_time > 0:
        pyautogui.keyDown(key)
        pyautogui.sleep(hold_time)

        pyautogui.keyUp(key)
    else:
        pyautogui.press(key)

    pyautogui.sleep(delay_after)


def click_on_rekordbox(x, y, delay_after: float = 0.2):
    focus_rekordbox_window()
    pyautogui.click(x=x, y=y)
    pyautogui.sleep(delay_after)


def click_top_menu_feature(feature_number: int):
    if feature_number == 1:
        click_on_rekordbox(TOP_MENU_FEATURE_1[0], TOP_MENU_FEATURE_1[1])
    elif feature_number == 2:
        click_on_rekordbox(TOP_MENU_FEATURE_2[0], TOP_MENU_FEATURE_2[1])
    elif feature_number == 3:
        click_on_rekordbox(TOP_MENU_FEATURE_3[0], TOP_MENU_FEATURE_3[1])
    elif feature_number == 4:
        click_on_rekordbox(TOP_MENU_FEATURE_4[0], TOP_MENU_FEATURE_4[1])
    elif feature_number == 5:
        click_on_rekordbox(TOP_MENU_FEATURE_5[0], TOP_MENU_FEATURE_5[1])


def ensure_delay_on_all_fx_slots():
    click_on_rekordbox(FX1_SLOT_1_DROPDOWN_ARROW[0], FX1_SLOT_1_DROPDOWN_ARROW[1])
    click_on_rekordbox(FX1_SLOT_1_DROPDOWN_ARROW[0], FX1_SLOT_1_DROPDOWN_ARROW[1] + 15)
    click_on_rekordbox(FX1_SLOT_2_DROPDOWN_ARROW[0], FX1_SLOT_2_DROPDOWN_ARROW[1])
    click_on_rekordbox(FX1_SLOT_2_DROPDOWN_ARROW[0], FX1_SLOT_2_DROPDOWN_ARROW[1] + 15)
    click_on_rekordbox(FX1_SLOT_3_DROPDOWN_ARROW[0], FX1_SLOT_3_DROPDOWN_ARROW[1])
    click_on_rekordbox(FX1_SLOT_3_DROPDOWN_ARROW[0], FX1_SLOT_3_DROPDOWN_ARROW[1] + 15)
    click_on_rekordbox(FX2_SLOT_1_DROPDOWN_ARROW[0], FX2_SLOT_1_DROPDOWN_ARROW[1])
    click_on_rekordbox(FX2_SLOT_1_DROPDOWN_ARROW[0], FX2_SLOT_1_DROPDOWN_ARROW[1] + 15)
    click_on_rekordbox(FX2_SLOT_2_DROPDOWN_ARROW[0], FX2_SLOT_2_DROPDOWN_ARROW[1])
    click_on_rekordbox(FX2_SLOT_2_DROPDOWN_ARROW[0], FX2_SLOT_2_DROPDOWN_ARROW[1] + 15)
    click_on_rekordbox(FX2_SLOT_3_DROPDOWN_ARROW[0], FX2_SLOT_3_DROPDOWN_ARROW[1])
    click_on_rekordbox(FX2_SLOT_3_DROPDOWN_ARROW[0], FX2_SLOT_3_DROPDOWN_ARROW[1] + 15)


def _send_note_on(outport, note: int, repeat_count: int = 1):
    for _ in range(max(repeat_count, 0)):
        outport.send(mido.Message(type="note_on", note=note))


def _set_beat_periods_to_minimum_for_slot(outport, slot_index: int):
    select_note = FX_SELECT_NOTE_BASE + slot_index
    beat_down_note = FX_BEAT_DOWN_NOTE_BASE + slot_index

    current_effect = available_fx[0]
    for target_effect in available_fx:
        if target_effect != current_effect:
            steps = get_nb_of_steps_until_next_available_effect(current_effect)
            _send_note_on(outport, select_note, repeat_count=steps)
            current_effect = target_effect

        beat_count = len(available_beat_periods_per_fx.get(target_effect, []))
        _send_note_on(outport, beat_down_note, repeat_count=beat_count)


def initialize_fx_beat_periods_minimums():
    virtual_out_name = get_midi_device_name_matching_regex(
        is_output=True, regex="Virtual Minilab3"
    )
    with mido.open_output(virtual_out_name) as outport:
        for slot_index in range(FX_SLOT_COUNT):
            _set_beat_periods_to_minimum_for_slot(outport, slot_index)
