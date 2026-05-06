#!/usr/bin/env python

import mido

print(mido.get_output_names())
port = mido.open_output('Minilab3 MIDI 2')

def sysex(*bytes):
    # This automatically adds the 0xF0 prefix and 0xF7 suffix.
    # There is also an Arturia-specific prefix (00 20 6B 7F 42) but we keep that explicit in the messages below.
    return mido.Message(
        'sysex',
        data=list(bytes)
    )

def init():
    # Initialization: needed for display changes. Not needed for pad color changes
    # TODO: what exactly does this do?
    port.send(sysex(
        0x00,0x20,0x6B,0x7F,0x42,
        0x02,0x02,0x40,0x6A,0x21, # sometimes suggested to be 0x20. Is this Arturia vs DAW?
    ))
    #port.send(sysex(0x00,0x20,0x6B,0x7F,0x42, 0x01,0x00,0x40,0x03))
    #port.send(sysex(0x00,0x20,0x6B,0x7F,0x42, 0x01,0x00,0x40,0x01))
    #port.send(sysex(0x00,0x20,0x6b,0x7f,0x42, 0x04,0x01,0x60,0x0a,0x0a,0x5f,0x51,0x00))

def set_button_color(button, r=0x00, g=0x00, b=0x00):
    
    button+= 3
    
    assert button >= 0 and button <= 11, "pad must be 0..11"
    assert r >= 0 and r <= 0x7F, "red must be 0x00..0x7F"
    assert g >= 0 and g <= 0x7F, "green must be 0x00..0x7F"
    assert b >= 0 and b <= 0x7F, "blue must be 0x00..0x7F"
    port.send(sysex(
        0x00, 0x20, 0x6B, 0x7F, 0x42,
        0x02, 0x01, 0x16, button, r, g, b
    ))

# pictures = {
#     'none':  0x00,
#     'heart': 0x01,
#     'play':  0x02,
#     'rec':   0x03,
#     'armed': 0x04,
#     'shift': 0x05,
# }

# def show_text(line1, line2, picture1='none', picture2='none'):
#     assert picture1 in pictures, "unknown picture1"
#     assert picture1 in pictures, "unknown picture2"
#     pict1 = pictures[picture1]
#     pict2 = pictures[picture2]
#     str1 = list(bytearray(line1, 'ascii'))
#     str2 = list(bytearray(line2, 'ascii'))
#     port.send(sysex(
#         0x00, 0x20, 0x6B, 0x7F, 0x42,
#         0x04, 0x02, 0x60,
#         0x1F, 0x07, 0x01, pict1, pict2, 0x01, 0x00,
#         #              ^
#         # The Bitwig script also allows putting 0x02 here but I haven't seen a difference ¯\_(ツ)_/¯
#         0x01, *str1, 0x00,
#         0x02, *str2, 0x00,
#     ))

# def clear_text():
#     show_text('','')

# def show_text_left(line1, line2):
#     str1 = list(bytearray(line1, 'ascii'))
#     str2 = list(bytearray(line2, 'ascii'))
#     port.send(sysex(
#         0x00, 0x20, 0x6B, 0x7F, 0x42,
#         0x04, 0x02, 0x60,
#         0x01, *str1, 0x00,
#         0x02, *str2,
#     ))

# controls = {
#     'knob':   0x03,
#     'fader':  0x04,
#     'pad':    0x05,
# }

# def show_info(line1, line2, value, control, autohide=True):
#     assert value >= 0 and value <= 127, "value must be 0..127"
#     assert type(autohide) == bool, "autohide must be bool"
#     assert control in controls

#     str1 = list(bytearray(line1, 'ascii'))
#     str2 = list(bytearray(line2, 'ascii'))
#     autohide_byte = 0x02 if autohide else 0x00
#     control_byte = controls[control]

#     port.send(sysex(
#         0x00, 0x20, 0x6B, 0x7F, 0x42,
#         0x04, 0x02, 0x60,
#         0x1F, control_byte, autohide_byte, value, 0x00, 0x00,
#         0x01, *str1, 0x00,
#         0x02, *str2,
#     ))

# def show_scroll_text(line1, line2, pos, length, autohide=True):
#     # Note that after autohide, the text from this invocation stays there
#     assert pos < length, "pos must < length"
#     assert pos >= 0, "pos must be positive"
#     assert length >= 0, "length must be positive"
#     assert type(autohide) == bool, "autohide must be bool"

#     control_byte = 0x06
#     autohide_byte = 0x02 if autohide else 0x00
#     str1 = list(bytearray(line1, 'ascii'))
#     str2 = list(bytearray(line2, 'ascii'))

#     port.send(sysex(
#         0x00, 0x20, 0x6B, 0x7F, 0x42,
#         0x04, 0x02, 0x60,
#         0x1F, control_byte, autohide_byte, pos, 0x00, length, 0x00, 0x00,
#         0x01, *str1, 0x00,
#         0x02, *str2, 0x00,
#     ))

init()
      

set_button_color( 1,0x7F,0x00,0x00)
set_button_color( 2,0x30,0x00,0x00)
set_button_color( 3,0x7F,0x7F,0x7F)
set_button_color( 4,0x30,0x30,0x30)
set_button_color( 5,0x00,0x7F,0x00)
set_button_color( 6,0x00,0x30,0x00)
set_button_color( 7,0x00,0x00,0x7F)
set_button_color( 8,0x00,0x00,0x00)
set_button_color( 8,0x00,0x00,0x30)

# clear_text()

# show_text('Hello', 'World!', 'heart', 'play')
# show_text('Hello', 'World!', picture1='heart', picture2='heart')
# show_text_left('Hello', 'World')

# show_info('Pad', 'Info',   0, control='pad')
# show_info('Pad', 'Info',  50, control='knob')
# show_info('Pad', 'Info', 127, control='fader')

# show_scroll_text('What', 'Whattt', 1, 5)