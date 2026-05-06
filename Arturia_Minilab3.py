from djcontrol_specific.state_machine import StateMachine
import mido
import traceback

from functions.tempo_reverse import tempo_reverse
from helpers.midi_device_name import get_midi_device_name_matching_regex
from djcontrol_specific.controller_notes import (
    SHIFT_NOTE_INT,
    SEMITONE_DOWN_NOTE_INT,
    SEMITONE_UP_NOTE_INT,
    FADERS_ISO_VOLUME_INT,
    STEPPED_KNOB_TURN_CONTROL_INT,
    STEPPED_KNOB_TURN_RIGHT_CONTROL_VALUE_INT_1,
    STEPPED_KNOB_TURN_RIGHT_CONTROL_VALUE_INT_2,
    STEPPED_KNOB_TURN_LEFT_CONTROL_VALUE_INT_1,
    STEPPED_KNOB_TURN_LEFT_CONTROL_VALUE_INT_2,
)

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
                        active_fx_effects = state_machine.get_active_fx_effects()

                        if ims.value in [
                            STEPPED_KNOB_TURN_RIGHT_CONTROL_VALUE_INT_1,
                            STEPPED_KNOB_TURN_RIGHT_CONTROL_VALUE_INT_2,
                        ]:
                            state_machine.stepped_knob_turn_right()

                            for idx, state in enumerate(active_fx_effects):
                                if state:
                                    msg = mido.Message(
                                        type="note_on",
                                        # control=ims.control + 5 * idx,
                                        note=idx + 1,
                                    )
                                    print(
                                        f"Stepped knob turn right, sending note_on with note={msg.note} for effect {idx + 1}"
                                    )
                                    virtual_outport.send(msg)

                        elif ims.value in [
                            STEPPED_KNOB_TURN_LEFT_CONTROL_VALUE_INT_1,
                            STEPPED_KNOB_TURN_LEFT_CONTROL_VALUE_INT_2,
                        ]:
                            state_machine.stepped_knob_turn_left()

                            for idx, state in enumerate(active_fx_effects):
                                if state:
                                    msg = mido.Message(
                                        "note_on",
                                        note=30 + idx + 1,
                                        channel=ims.channel,
                                    )
                                    print(
                                        f"Stepped knob turn left, sending note_on with note={msg.note} for effect {idx + 1}"
                                    )
                                    virtual_outport.send(msg)

                    else:
                        virtual_outport.send(ims)

                elif ims.type in ["note_on"]:  # Only forward note_on

                    print(f"Received note_on: {ims.note}")

                    if ims.note in [
                        SEMITONE_DOWN_NOTE_INT,
                        SEMITONE_UP_NOTE_INT,
                    ]:

                        if state_machine.shift_state:
                            for idx, state in enumerate(
                                state_machine.get_active_fx_effects()
                            ):
                                if state:
                                    msg = ims.copy(
                                        note=(
                                            80
                                            if ims.note == SEMITONE_DOWN_NOTE_INT
                                            else 90
                                        )
                                        + idx
                                        + 1
                                    )  # Map to a different note for each effect, matching midi_mappings/Minilab3.csv
                                    virtual_outport.send(msg)
                        else:
                            for idx, state in enumerate(
                                state_machine.get_active_fx1_channels()
                            ):
                                if state:
                                    msg = ims.copy(
                                        note=(
                                            10
                                            if ims.note == SEMITONE_DOWN_NOTE_INT
                                            else 20
                                        )
                                        + idx
                                        + 1
                                    )  # Map to a different note for each channel, matching midi_mappings/Minilab3.csv
                                    virtual_outport.send(msg)
                    else:
                        virtual_outport.send(ims)

                state_machine.ims_to_playback(ims)

    except KeyboardInterrupt:
        print("\nClosing RekordJog, bye.")

    except Exception as e:
        print("\n[ERROR] Something went wrong:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
