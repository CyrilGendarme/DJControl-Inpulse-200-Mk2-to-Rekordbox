import time
import mido
from helpers import rekordbox_process
from helpers.midi_device_name import get_midi_device_name_matching_regex
from ocr_and_clicks import detection
from ocr_and_clicks import actions
from minilab_specific.fx_presets import (
    available_fx,
    available_beat_periods_per_fx,
    fx_presets,
    get_nb_of_steps_until_next_available_effect,
)

FX_SELECT_FORWARD_NOTE_OFFSET = 30
FX_SELECT_BACK_NOTE_OFFSET = 0
FX_BEAT_UP_NOTE_OFFSET = 90


def _apply_fx_presets_to_software():
    # initialize_fx_beat_periods_minimums() leaves each slot at ROLL + minimum beat.
    baseline_effect = available_fx[-1]
    all_preset_entries = list(fx_presets["preset_1"]) + list(fx_presets["preset_2"])

    virtual_out_name = get_midi_device_name_matching_regex(
        is_output=True, regex="Virtual Minilab3"
    )

    with mido.open_output(virtual_out_name) as virtual_outport:
        for idx, (target_fx_name, target_beat_period) in enumerate(all_preset_entries):
            if target_fx_name not in available_fx:
                continue

            current_index = available_fx.index(baseline_effect)
            target_index = available_fx.index(target_fx_name)
            steps_forward = (target_index - current_index) % len(available_fx)
            steps_backward = (current_index - target_index) % len(available_fx)

            if steps_forward <= steps_backward:
                select_note = idx + 1 + FX_SELECT_FORWARD_NOTE_OFFSET
                transition_count = steps_forward
                backward = False
            else:
                select_note = idx + 1 + FX_SELECT_BACK_NOTE_OFFSET
                transition_count = steps_backward
                backward = True

            current_effect = baseline_effect
            for _ in range(transition_count):
                step_count = get_nb_of_steps_until_next_available_effect(
                    current_effect,
                    backward=backward,
                )
                for _ in range(step_count):
                    virtual_outport.send(mido.Message(type="note_on", note=select_note))
                current_available_index = available_fx.index(current_effect)
                next_available_index = (
                    (current_available_index - 1)
                    if backward
                    else (current_available_index + 1)
                ) % len(available_fx)
                current_effect = available_fx[next_available_index]

            beat_periods = available_beat_periods_per_fx.get(target_fx_name, [])
            if target_beat_period in beat_periods:
                beat_up_steps = beat_periods.index(target_beat_period)
                beat_up_note = idx + 1 + FX_BEAT_UP_NOTE_OFFSET
                for _ in range(beat_up_steps):
                    virtual_outport.send(
                        mido.Message(type="note_on", note=beat_up_note)
                    )

def start_up_sequence():
    '''
    We want:
        4 DECKS
        FX ON
        MIX POINT LINK OFF
        SAMPLER ON
        MIXER ON
    '''
    
    
    if not rekordbox_process.is_rekordbox_running():
        rekordbox_process.launch_rekordbox()
        if not rekordbox_process.wait_for_rekordbox_ready(timeout=90):
            raise RuntimeError("Failed to launch or initialize Rekordbox window.")


    rekordbox_process.focus_rekordbox_window()
    
    time.sleep(5)
    

    if not detection.is_fx_active():
        actions.click_top_menu_feature(1)
    if detection.is_mix_point_link_active():
        actions.click_top_menu_feature(2)
    if not detection.is_sampler_active():
        actions.click_top_menu_feature(3)
    if not detection.is_mixer_active():
        actions.click_top_menu_feature(4)
        
    time.sleep(1)
        
    actions.ensure_delay_on_all_fx_slots()
    actions.initialize_fx_beat_periods_minimums()
    _apply_fx_presets_to_software()
