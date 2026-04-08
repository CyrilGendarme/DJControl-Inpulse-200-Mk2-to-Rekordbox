import mido

from djcontrol_specific.controller_notes import JOG_SIDE_CODE, JOG_TOP_CODE

TURN_CLOCK_SPEED = 0x46
TURN_COUNTER_SPEED = 0x3A


def jog_incremental(ims, midi_out, wheel_messages_counter):
    if ims.control == JOG_SIDE_CODE or ims.control == JOG_TOP_CODE:
        wheel_messages_counter += 1
        if wheel_messages_counter % 4 == 0:
            if ims.value == 0x01:
                midi_out.send(mido.Message('control_change', channel=ims.channel, control=ims.control, value=TURN_CLOCK_SPEED))
            elif ims.value == 0x7F:
                midi_out.send(mido.Message('control_change', channel=ims.channel, control=ims.control, value=TURN_COUNTER_SPEED))
    return wheel_messages_counter
