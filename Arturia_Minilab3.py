from djcontrol_specific.state_machine import StateMachine
import mido
import traceback

from functions.tempo_reverse import tempo_reverse
from helpers.midi_device_name import get_midi_device_name_matching_regex
from djcontrol_specific.controller_notes import SHIFT_NOTE_INT


def main():
    midi_inp_name = get_midi_device_name_matching_regex(
        is_output=False, regex="Minilab3"
    )
    midi_out_name = get_midi_device_name_matching_regex(
        is_output=True, regex="Minilab3"
    )

    try:
        with mido.open_input(midi_inp_name) as inport, mido.open_output(
            midi_out_name
        ) as outport, StateMachine() as state_machine:
            while True:
                
                ims = inport.receive()
                
                if getattr(ims, "type", None) == "sysex":
                    continue
                
                msg = ims.copy()
                
                print(f"Received MIDI message: {ims}")
                                
                if ims.type == "control_change":
                    outport.send(msg)

                elif ims.type in ["note_on"]: # Only forward note_on
                    outport.send(msg)
                    
                
                state_machine.ims_to_lights_playback(ims)


    except KeyboardInterrupt:
        print("\nClosing RekordJog, bye.")

    except Exception as e:
        print("\n[ERROR] Something went wrong:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
