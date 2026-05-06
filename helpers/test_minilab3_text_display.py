#!/usr/bin/env python

import mido
import re


def get_midi_device_name_matching_regex(is_output: bool, regex: str) -> str:
    device_names = mido.get_output_names()  if is_output else mido.get_input_names()
    # print(f"{'Output' if is_output else 'Input'} MIDI devices found: {device_names}")
    pattern = re.compile(regex, re.IGNORECASE)
    for name in device_names:
        if pattern.search(name):
            return name
    return None


def sysex(*bytes):
    # This automatically adds the 0xF0 prefix and 0xF7 suffix.
    # There is also an Arturia-specific prefix (00 20 6B 7F 42) but we keep that explicit in the messages below.
    return mido.Message(
        'sysex',
        data=list(bytes)
    )

def init(port):
    # Initialization: needed for display changes. Not needed for pad color changes
    # TODO: what exactly does this do?
    port.send(sysex(
        0x00,0x20,0x6B,0x7F,0x42, 
        0x02,0x02,0x40,0x6A,0x21, # sometimes suggested to be 0x20. Is this Arturia vs DAW?
    ))


def show_text(port,line1, line2):
    str1 = list(bytearray(line1, 'ascii'))
    str2 = list(bytearray(line2, 'ascii'))
    port.send(sysex(
        0x00, 0x20, 0x6B, 0x7F, 0x42,
        0x04, 0x01, 0x60,
        0x01, *str2, 0x00,
        0x02, *str1,
    ))
    
    
    
controls = {
    'knob':   0x03,
    'fader':  0x04,
    'pad':    0x05,
}


def show_info(port, line1, line2, value, control, autohide=True):
    assert value >= 0 and value <= 127, "value must be 0..127"
    assert type(autohide) == bool, "autohide must be bool"
    assert control in controls

    str1 = list(bytearray(line1, 'ascii'))
    str2 = list(bytearray(line2, 'ascii'))
    autohide_byte = 0x02 if autohide else 0x00
    control_byte = controls[control]

    port.send(sysex(
        0x00, 0x20, 0x6B, 0x7F, 0x42,
        0x04, 0x01, 0x60,
        0x1F, control_byte, autohide_byte, value, 0x00, 0x00,
        0x01, *str1, 0x00,
        0x02, *str2,
    ))




midi_out_name = get_midi_device_name_matching_regex(
    is_output=True, regex="Minilab3 ALV"
)

try:
    with  mido.open_output(
        midi_out_name
    ) as outport:

        init(outport)           
        # show_text(outport, 'IIIIIIIIIIIIIIIIIIIIIIIIII   127', 'SOMETHING')
        # show_text(outport, '________   127', 'SOMETHING')
        # show_text(outport, '-------------   127', 'SOMETHING')
        
        import time
        time.sleep(2)
        show_text(outport, "___      ___", '[ ][ ][ ][ ]  [ ][ ][ ][ ]')
        time.sleep(2)
        show_text(outport, "E R F      E R F", '[ ][ ][ ][ ]  [ ][ ][ ][ ]')

        
        
        
    
except KeyboardInterrupt:
        print("\nClosing RekordJog, bye.")
except Exception as e:
    print("\n[ERROR] Something went wrong:")
