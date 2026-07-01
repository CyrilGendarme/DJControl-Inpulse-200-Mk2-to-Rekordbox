import mido
from .controller_notes import *
from helpers.midi_device_name import get_midi_device_name_matching_regex

INST_BASS_PARTS_MERGED = True


def set_sync_light(channel, note, on_true, out):
    out.send(
        mido.Message(
            "note_on", note=note, velocity=127 if on_true else 0, channel=channel
        )
    )
    # Ensure the light state is preserved when "shift" touch is pressed
    out.send(
        mido.Message(
            "note_on", note=note, velocity=127 if on_true else 0, channel=channel + 3
        )
    )


class StateMachine:
    def __init__(self):
        midi_out_light_playback_name = get_midi_device_name_matching_regex(
            is_output=True,
            regex="DJControl Inpulse 200 Mk2",
        )
        self.outport_lights = mido.open_output(midi_out_light_playback_name)

        self.deck13 = False
        self.deck24 = False
        self.channel_1 = ChannelState(1, self.outport_lights)
        self.channel_2 = ChannelState(2, self.outport_lights)
        self.channel_3 = ChannelState(3, self.outport_lights)
        self.channel_4 = ChannelState(4, self.outport_lights)

        self.vocal_fx_active = True
        self.inst_fx_active = True
        self.bass_fx_active = True
        self.drums_fx_active = True
        self.inst_bass_parts_merged = INST_BASS_PARTS_MERGED
        self.assist_prep_pressed = False
        self.master_pressed = False

        set_sync_light(1, SYNC_NOTE, self.deck13, self.outport_lights)
        set_sync_light(2, SYNC_NOTE, self.deck24, self.outport_lights)
        self.set_fx_part_light_playback(FX_VOCAL_NOTE, True)
        self.set_fx_part_light_playback(FX_INST_NOTE, True)
        self.set_fx_part_light_playback(FX_BASS_NOTE, True)
        self.set_fx_part_light_playback(FX_DRUMS_NOTE, True)

    def close(self):
        if self.outport_lights and not self.outport_lights.closed:
            self.outport_lights.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def switch_deck13(self):
        self.deck13 = not self.deck13
        set_sync_light(1, SYNC_NOTE, self.deck13, self.outport_lights)
        if self.deck13:
            self.channel_3.set_all_lights_playback()
            self.channel_3.set_all_knobs_and_faders_desactivated()
        else:
            self.channel_1.set_all_lights_playback()
            self.channel_1.set_all_knobs_and_faders_desactivated()

    def switch_deck24(self):
        self.deck24 = not self.deck24
        set_sync_light(2, SYNC_NOTE, self.deck24, self.outport_lights)
        if self.deck24:
            self.channel_4.set_all_lights_playback()
            self.channel_4.set_all_knobs_and_faders_desactivated()
        else:
            self.channel_2.set_all_lights_playback()
            self.channel_2.set_all_knobs_and_faders_desactivated()

    def _get_channel_state(self, channel):
        if channel in [1, 4, 6]:
            return self.channel_3 if self.deck13 else self.channel_1
        elif channel in [2, 5, 7]:
            return self.channel_4 if self.deck24 else self.channel_2
        elif channel == 11:
            return self.channel_3
        elif channel == 12:
            return self.channel_4
        return None

    def _is_channel_main(self, ims):
        return ims.channel in [1, 2, 11, 12]

    def set_fx_part_light_playback(self, fx_note, active):
        set_sync_light(6, fx_note, active, self.outport_lights)
        set_sync_light(7, fx_note, active, self.outport_lights)

    def set_assist_prep_pressed_state(self, pressed):
        self.assist_prep_pressed = pressed
        # set_sync_light(0, ASSIST_PREP_NOTE, pressed, self.outport_lights)
        set_sync_light(0, ASSIST_PREP_NOTE, False, self.outport_lights)

    def set_master_pressed_state(self, pressed):
        self.master_pressed = pressed
        # set_sync_light(0, MASTER_NOTE, pressed, self.outport_lights)
        set_sync_light(0, MASTER_NOTE, False, self.outport_lights)
        
    def is_knobs_and_faders_desactivated(self, channel, control):
        channel_state = self._get_channel_state(channel)
        if channel_state is None:
            return False
        return channel_state.knobs_and_faders_desactivated.get(control)

    def ims_to_lights_playback(self, ims):

        if ims.type == "control_change":
            if ims.note in [
                EQ_HIGH_NOTE,
                EQ_MID_NOTE,
                EQ_LOW_NOTE,
                CHANNEL_FADER_NOTE,
                CFX_NOTE,
            ]:
                channel_state = self._get_channel_state(ims.channel)
                channel_state.set_knobs_and_faders_value(ims.note, ims.value)

        elif ims.type == "note_on":
            channel_state = self._get_channel_state(ims.channel)

            if channel_state is None:
                if ims.note == ASSIST_PREP_NOTE:
                    self.set_assist_prep_pressed_state(ims.velocity > 0)
                if ims.note == MASTER_NOTE:
                    self.set_master_pressed_state(ims.velocity > 0)
                return

            pressed = ims.velocity > 0

            if ims.note == LOAD_NOTE and pressed:
                channel_state.reset_lights_playback_after_track_load()
            elif (
                ims.note == HOT_CUE_MODE_NOTE and pressed and self._is_channel_main(ims)
            ):
                channel_state.switch_mode_to_hot_cue()
            elif ims.note == STEMS_MODE_NOTE and pressed and self._is_channel_main(ims):
                channel_state.switch_mode_to_stems()
            elif ims.note == PLAYPAUSE_NOTE and pressed:
                channel_state.set_play_active(not channel_state.play_active)
            elif ims.note == HEADPHONE_CUE_NOTE and pressed:
                channel_state.set_headphone_cue_active(
                    not channel_state.headphone_cue_active
                )
            elif ims.note == LOOP_NOTE and pressed and self._is_channel_main(ims):
                channel_state.set_loop_active(True)
            elif ims.note == LOOP_NOTE and pressed and not self._is_channel_main(ims):
                channel_state.set_loop_active(False)

            elif ims.note == FX_VOCAL_NOTE and pressed:
                self.vocal_fx_active = not self.vocal_fx_active
                self.set_fx_part_light_playback(FX_VOCAL_NOTE, self.vocal_fx_active)
            elif ims.note == FX_INST_NOTE and pressed:
                self.inst_fx_active = not self.inst_fx_active
                self.set_fx_part_light_playback(FX_INST_NOTE, self.inst_fx_active)
                if self.inst_bass_parts_merged:
                    self.bass_fx_active = self.inst_fx_active
                    self.set_fx_part_light_playback(FX_BASS_NOTE, self.bass_fx_active)
            elif ims.note == FX_BASS_NOTE and pressed:
                self.bass_fx_active = not self.bass_fx_active
                self.set_fx_part_light_playback(FX_BASS_NOTE, self.bass_fx_active)
                if self.inst_bass_parts_merged:
                    self.inst_fx_active = self.bass_fx_active
                    self.set_fx_part_light_playback(FX_INST_NOTE, self.bass_fx_active)
            elif ims.note == FX_DRUMS_NOTE and pressed:
                self.drums_fx_active = not self.drums_fx_active
                self.set_fx_part_light_playback(FX_DRUMS_NOTE, self.drums_fx_active)

            if not self.assist_prep_pressed:
                if ims.note == VOCAL_PART_NOTE and pressed:
                    channel_state.set_music_part_active(
                        "vocal", not channel_state.vocal_active
                    )
                elif ims.note == INST_PART_NOTE and pressed:
                    channel_state.set_music_part_active(
                        "inst", not channel_state.inst_active
                    )
                elif ims.note == BASS_PART_NOTE and pressed:
                    channel_state.set_music_part_active(
                        "bass", not channel_state.bass_active
                    )
                elif ims.note == DRUMS_PART_NOTE and pressed:
                    channel_state.set_music_part_active(
                        "drums", not channel_state.drums_active
                    )


class ChannelState:
    def __init__(self, channel, outport_lights):
        self.channel = channel
        self.deck = 1 if channel in [1, 3] else 2
        self.outport_lights = outport_lights
        self.play_active = False
        self.headphone_cue_active = False
        self.loop_active = False
        self.hot_cue_mode = True
        self.stems_mode = False
        self.loop_in_pressed = False
        self.vocal_active = True
        self.inst_active = True
        self.bass_active = True
        self.drums_active = True
        self.inst_bass_parts_merged = INST_BASS_PARTS_MERGED
        self.set_all_lights_playback()
        self.knobs_and_faders_value = {
            EQ_HIGH_NOTE: 127,
            EQ_MID_NOTE: 127,
            EQ_LOW_NOTE: 127,
            CHANNEL_FADER_NOTE: 127,
            CFX_NOTE: 127,
        }
        self.knobs_and_faders_desactivated = {
            EQ_HIGH_NOTE: True,
            EQ_MID_NOTE: True,
            EQ_LOW_NOTE: True,
            CHANNEL_FADER_NOTE: True,
            CFX_NOTE: True,
        }

    def switch_mode_to_hot_cue(self):
        self.hot_cue_mode = True
        self.stems_mode = False
        set_sync_light(
            self.deck, HOT_CUE_MODE_NOTE, self.hot_cue_mode, self.outport_lights
        )
        set_sync_light(self.deck, STEMS_MODE_NOTE, self.stems_mode, self.outport_lights)

    def switch_mode_to_stems(self):
        self.hot_cue_mode = False
        self.stems_mode = True
        set_sync_light(
            self.deck, HOT_CUE_MODE_NOTE, self.hot_cue_mode, self.outport_lights
        )
        set_sync_light(self.deck, STEMS_MODE_NOTE, self.stems_mode, self.outport_lights)

    def set_play_active(self, active):
        self.play_active = active
        set_sync_light(self.deck, PLAYPAUSE_NOTE, self.play_active, self.outport_lights)

    def set_headphone_cue_active(self, active):
        self.headphone_cue_active = active
        set_sync_light(
            self.deck,
            HEADPHONE_CUE_NOTE,
            self.headphone_cue_active,
            self.outport_lights,
        )

    def set_loop_active(self, active):
        self.loop_active = active
        set_sync_light(self.deck, LOOP_NOTE, self.loop_active, self.outport_lights)

    def set_music_part_active(self, part, active):
        if part == "vocal":
            self.vocal_active = active
            set_sync_light(
                self.deck + 5, VOCAL_PART_NOTE, self.vocal_active, self.outport_lights
            )
        elif part == "inst":
            self.inst_active = active
            set_sync_light(
                self.deck + 5, INST_PART_NOTE, self.inst_active, self.outport_lights
            )
            if self.inst_bass_parts_merged:
                self.bass_active = self.inst_active
                set_sync_light(
                    self.deck + 5, BASS_PART_NOTE, self.bass_active, self.outport_lights
                )
        elif part == "bass":
            self.bass_active = active
            set_sync_light(
                self.deck + 5, BASS_PART_NOTE, self.bass_active, self.outport_lights
            )
            if self.inst_bass_parts_merged:
                self.inst_active = self.bass_active
                set_sync_light(
                    self.deck + 5, INST_PART_NOTE, self.inst_active, self.outport_lights
                )
        elif part == "drums":
            self.drums_active = active
            set_sync_light(
                self.deck + 5, DRUMS_PART_NOTE, self.drums_active, self.outport_lights
            )

    def set_all_lights_playback(self):
        set_sync_light(
            self.deck, HOT_CUE_MODE_NOTE, self.hot_cue_mode, self.outport_lights
        )
        set_sync_light(self.deck, STEMS_MODE_NOTE, self.stems_mode, self.outport_lights)
        set_sync_light(self.deck, PLAYPAUSE_NOTE, self.play_active, self.outport_lights)
        set_sync_light(
            self.deck,
            HEADPHONE_CUE_NOTE,
            self.headphone_cue_active,
            self.outport_lights,
        )
        set_sync_light(self.deck, LOOP_NOTE, self.loop_active, self.outport_lights)
        set_sync_light(
            self.deck + 5, VOCAL_PART_NOTE, self.vocal_active, self.outport_lights
        )
        set_sync_light(
            self.deck + 5, INST_PART_NOTE, self.inst_active, self.outport_lights
        )
        set_sync_light(
            self.deck + 5, BASS_PART_NOTE, self.bass_active, self.outport_lights
        )
        set_sync_light(
            self.deck + 5, DRUMS_PART_NOTE, self.drums_active, self.outport_lights
        )

    def reset_lights_playback_after_track_load(self):
        self.set_play_active(False)
        self.set_loop_active(False)
        self.set_music_part_active("vocal", True)
        self.set_music_part_active("inst", True)
        self.set_music_part_active("bass", True)
        self.set_music_part_active("drums", True)

    def set_knobs_and_faders_value(self, control, value) -> None:
        # If channel not desactivated, update the value and return
        if not self.knobs_and_faders_desactivated.get(control):
            self.knobs_and_faders_value[control] = value
            return

        # Otherwise, drop the value if not close to the previous one, otherwise update the value and desactivated state
        if self.is_knobs_and_faders_value_close_from_previous_one(control, value):
            self.knobs_and_faders_desactivated[control] = False
            self.knobs_and_faders_value[control] = value

    def set_all_knobs_and_faders_desactivated(self) -> None:
        for control in self.knobs_and_faders_desactivated.keys():
            self.knobs_and_faders_desactivated[control] = True

    def is_knobs_and_faders_value_close_from_previous_one(
        self, control, value, threshold=5
    ) -> bool:
        previous_value = self.knobs_and_faders_value.get(control)
        if previous_value is None:
            return False
        return abs(previous_value - value) <= threshold
