from minilab_specific.state_machine import StateMachine
import mido
import traceback

from minilab_specific.start_up_sequence import start_up_sequence
from helpers.midi_device_name import get_midi_device_name_matching_regex
from minilab_specific.controller_notes import (
    SEMITONE_DOWN_NOTE_INT,
    SEMITONE_UP_NOTE_INT,
    FADERS_ISO_VOLUME_INT,
    STEPPED_KNOB_TURN_CONTROL_INT,
    STEPPED_KNOB_TURN_CONTROL_INT_SHIFT,
    STEPPED_KNOB_TURN_RIGHT_CONTROL_VALUE_INT_1,
    STEPPED_KNOB_TURN_RIGHT_CONTROL_VALUE_INT_2,
    STEPPED_KNOB_TURN_LEFT_CONTROL_VALUE_INT_1,
    STEPPED_KNOB_TURN_LEFT_CONTROL_VALUE_INT_2,
    SAMPLER_VOLUME_SWITCH,
)
from minilab_specific.fx_presets import (
    get_nb_of_steps_until_next_available_effect,
)

RIGHT_TURN_VALUES = {
    STEPPED_KNOB_TURN_RIGHT_CONTROL_VALUE_INT_1,
    STEPPED_KNOB_TURN_RIGHT_CONTROL_VALUE_INT_2,
}

LEFT_TURN_VALUES = {
    STEPPED_KNOB_TURN_LEFT_CONTROL_VALUE_INT_1,
    STEPPED_KNOB_TURN_LEFT_CONTROL_VALUE_INT_2,
}

FX_SELECT_FORWARD_NOTE_OFFSET = 30
FX_SELECT_BACK_NOTE_OFFSET = 0
FX_BEAT_UP_NOTE_OFFSET = 90


def _send_fx_note_on(
    virtual_outport, idx: int, note_offset: int, repeat_count: int = 1
):
    for _ in range(repeat_count):
        msg = mido.Message(type="note_on", note=idx + 1 + note_offset)
        virtual_outport.send(msg)


def _handle_stepped_knob_turn(
    ims, state_machine: StateMachine, virtual_outport, shift_mode: bool
) -> bool:
    active_fx_effects = state_machine.get_active_fx_effects()
    all_fx_slots = state_machine.fx1_effects + state_machine.fx2_effects

    if ims.value in RIGHT_TURN_VALUES:
        turn_fn = state_machine.stepped_knob_turn_right
        direction_name = "right"
    elif ims.value in LEFT_TURN_VALUES:
        turn_fn = state_machine.stepped_knob_turn_left
        direction_name = "left"
    else:
        return False

    backward = direction_name == "left"

    # Snapshot effect names before mutating state; repeat_count must represent
    # how many software steps are needed from the current effect to next allowed one.
    fx_names_before_turn = [slot.fx_name for slot in all_fx_slots]
    turn_fn(shift_mode=shift_mode)

    note_offset = (
        (80 if backward else 90)
        if shift_mode
        else (FX_SELECT_BACK_NOTE_OFFSET if backward else FX_SELECT_FORWARD_NOTE_OFFSET)
    )

    for idx, state in enumerate(active_fx_effects):
        if not state:
            continue

        if shift_mode:
            repeat_count = 1
        else:
            repeat_count = get_nb_of_steps_until_next_available_effect(
                fx_names_before_turn[idx],
                backward=backward,
            )
            print(
                f"Stepped knob turn {direction_name}, effect {idx + 1} is active, sending {repeat_count} note_on messages for it"
            )

        _send_fx_note_on(virtual_outport, idx, note_offset, repeat_count)

    return True


def _forward_semitone_note_on(ims, state_machine: StateMachine, virtual_outport):
    base_note = 10 if ims.note == SEMITONE_DOWN_NOTE_INT else 20
    for idx, state in enumerate(state_machine.get_active_fx1_channels()):
        if state:
            msg = ims.copy(
                note=base_note + idx + 1
            )  # Map to a different note for each channel, matching midi_mappings/Minilab3.csv
            virtual_outport.send(msg)


def main():
    midi_inp_name = get_midi_device_name_matching_regex(
        is_output=False, regex="Minilab3 MIDI"
    )
    virtual_out_name = get_midi_device_name_matching_regex(
        is_output=True, regex="Virtual Minilab3"
    )

    try:
        with mido.open_input(midi_inp_name) as inport, mido.open_output(
            virtual_out_name
        ) as virtual_outport, StateMachine() as state_machine:
            while True:

                ims = inport.receive()

                if getattr(ims, "type", None) == "sysex":
                    continue

                if ims.type == "control_change":

                    print(
                        f"Received control_change: {ims.control} (value: {ims.value})"
                    )

                    if ims.control in FADERS_ISO_VOLUME_INT:
                        for idx, state in enumerate(
                            state_machine.get_active_fx1_channels()
                        ):
                            if state:
                                msg = ims.copy(
                                    control=ims.control
                                    - 80
                                    + 20
                                    + 5
                                    * idx  # i.e. values in [22, 23, 25] with a max increment of 15
                                )  # Map to a different note for each channel, matching midi_mappings/Minilab3.csv
                                virtual_outport.send(msg)

                    elif ims.control == STEPPED_KNOB_TURN_CONTROL_INT:
                        _handle_stepped_knob_turn(
                            ims,
                            state_machine,
                            virtual_outport,
                            shift_mode=False,
                        )

                    elif ims.control == STEPPED_KNOB_TURN_CONTROL_INT_SHIFT:
                        _handle_stepped_knob_turn(
                            ims,
                            state_machine,
                            virtual_outport,
                            shift_mode=True,
                        )

                    else:
                        virtual_outport.send(ims)

                elif ims.type in ["note_on"]:  # Only forward note_on

                    print(f"Received note_on: {ims.note}")

                    if ims.note in [
                        SEMITONE_DOWN_NOTE_INT,
                        SEMITONE_UP_NOTE_INT,
                    ]:
                        _forward_semitone_note_on(ims, state_machine, virtual_outport)
                    elif ims.note == SAMPLER_VOLUME_SWITCH:
                        if state_machine.sampler_volume_on:
                            value = 127
                        else:
                            value = 0
                        msg = mido.Message(
                            type="control_change", value=value, control=20
                        )
                        virtual_outport.send(msg)
                        virtual_outport.send(ims)

                    else:
                        virtual_outport.send(ims)

                state_machine.ims_to_playback(ims)

    except KeyboardInterrupt:
        print("\nClosing RekordJog, bye.")

    except Exception as e:
        print("\n[ERROR] Something went wrong:")
        traceback.print_exc()


if __name__ == "__main__":
    start_up_sequence()
    main()
