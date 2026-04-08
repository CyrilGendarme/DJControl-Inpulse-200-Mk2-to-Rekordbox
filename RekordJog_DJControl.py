from djcontrol_specific.state_machine import StateMachine
import mido
import traceback

from functions.jog_incremental import jog_incremental
from functions.rekordjog_start_sequence import rekordjog_start_sequence
from functions.tempo_reverse import tempo_reverse
from helpers.midi_device_name import get_midi_device_name_matching_regex
from djcontrol_specific.controller_notes import (
    JOG_SIDE_CODE,
    JOG_TOP_CODE,
    SYNC_NOTE_INT,
)


def main():
    midi_inp_name = get_midi_device_name_matching_regex(
        is_output=False, regex="DJControl Inpulse 200 Mk2"
    )
    midi_out_name = get_midi_device_name_matching_regex(
        is_output=True, regex="PIONEER DDJ-SX"
    )

    try:
        with mido.open_input(midi_inp_name) as inport, mido.open_output(
            midi_out_name
        ) as outport, StateMachine() as state_machine:
            rekordjog_start_sequence()
            wheel_messages_counter = 3

            while True:
                ims = inport.receive()

                # --- Deck Emulation Logic ---
                if (
                    ims.type == "note_on"
                    and ims.velocity > 0
                    and ims.note == SYNC_NOTE_INT
                ):
                    if ims.channel == 1:  # Deck 1 toggle
                        state_machine.switch_deck13()
                    elif ims.channel == 2:  # Deck 2 toggle
                        state_machine.switch_deck24()
                    else:
                        raise ValueError(f"Unexpected channel for toggle: {ims}")

                # Dynamic MIDI mapping: remap deck 1/2 controls to deck 3/4 if toggled
                msg = ims.copy()
                if ims.type in ["note_on", "note_off", "control_change"]:
                    if state_machine.deck13:
                        if ims.channel in [1, 4]:
                            msg.channel += 10  # Deck 3
                        elif ims.channel == 6:
                            msg.channel = 8  # Deck 3
                    if state_machine.deck24:
                        if ims.channel in [2, 5]:
                            msg.channel += 10  # Deck 4
                        elif ims.channel == 7:
                            msg.channel = 9

                state_machine.ims_to_lights_playback(ims)

                if ims.type == "control_change":
                    if ims.control == JOG_SIDE_CODE or ims.control == JOG_TOP_CODE:
                        wheel_messages_counter = jog_incremental(
                            msg,
                            outport,
                            wheel_messages_counter,
                            JOG_SIDE_CODE,
                            JOG_TOP_CODE,
                        )
                    else:
                        outport.send(msg)

                    tempo_reverse(msg, outport)

                elif ims.type in ["note_on", "note_off"]:
                    outport.send(msg)

    except KeyboardInterrupt:
        print("\nClosing RekordJog, bye.")

    except Exception as e:
        print("\n[ERROR] Something went wrong:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
