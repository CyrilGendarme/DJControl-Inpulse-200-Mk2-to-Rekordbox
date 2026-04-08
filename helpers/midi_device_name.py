import mido
import re


def get_midi_device_name_matching_regex(is_output: bool, regex: str) -> str:
    device_names = mido.get_output_names()  if is_output else mido.get_input_names()
    pattern = re.compile(regex, re.IGNORECASE)
    for name in device_names:
        if pattern.search(name):
            return name
    return None


