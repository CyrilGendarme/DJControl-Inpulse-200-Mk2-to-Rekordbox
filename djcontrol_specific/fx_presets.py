from enum import Enum


class FxName(str, Enum):
    DELAY = "DELAY"
    ECHO = "ECHO"
    SPIRAL = "SPIRAL"
    REVERB = "REVERB"
    REV_DELAY = "REV DELAY"
    MT_DELAY = "MT DELAY"
    UP_ECHO = "UP ECHO"
    DOWN_ECHO = "DOWN ECHO"
    TRANS = "TRANS"
    PAN = "PAN"
    FILTER = "FILTER"
    FLANGER = "FLANGER"
    PHASER = "PHASER"
    SLIP_ROLL = "SLIP ROLL"
    ROLL = "ROLL"
    REV_ROLL = "REV ROLL"
    ROBOT = "ROBOT"
    PITCH = "PITCH"
    ENIGMA_JET = "ENIGMA JET"
    MOBIUS_SAW = "MOBIUS SAW"
    MOBIUS_TRU = "MOBIUS TRU"
    LOW_CUTE_ECHO = "LOW CUTE ECHO"
    PING_PONG = "PING PONG"
    HELIX = "HELIX"
    VINYL_BRAKE = "VINYL BRAKE"
    STRETCH = "STRETCH"
    BPF_ECHO = "BPF ECHO"
    NOISE = "NOISE"
    SPIRAL_UP = "SPIRAL UP"
    REVERB_UP = "REVERB UP"
    HPF_ECHO = "HPF ECHO"
    LPF_ECHO = "LPF ECHO"
    CRUSH_ECHO = "CRUSH ECHO"
    SPIRAL_DOWN = "SPIRAL DOWN"
    REVERB_DOWN = "REVERB DOWN"

available_fx = [
    FxName.DELAY,
    FxName.ECHO,
    FxName.REVERB,
    FxName.TRANS,
    FxName.ROLL,
]


def get_nb_of_steps_until_next_avaailalbe_effect(current_effect: FxName) -> int:
    all_fx = list(FxName)

    if current_effect not in all_fx:
        raise ValueError(f"Unknown FX value: {current_effect!r}")

    current_index = all_fx.index(current_effect)

    for step in range(1, len(all_fx) + 1):
        next_effect = all_fx[(current_index + step) % len(all_fx)]
        if next_effect in available_fx:
            return step

    raise ValueError("No available FX configured in available_fx.")


class FxBeatPeriod(str, Enum):
    ONE_EIGHTH = "1/8"
    ONE_QUARTER = "1/4"
    ONE_HALF = "1/2"
    THREE_QUARTERS = "3/4"
    ONE = "1"
    TWO = "2"
    FOUR = "4"
    EIGHT = "8"
    SIXTEEN = "16"


FxPresetEntry = tuple[FxName, FxBeatPeriod]
FxPreset = tuple[FxPresetEntry, FxPresetEntry, FxPresetEntry]


fx_presets: dict[str, FxPreset] = {
    "preset_1": (
        (FxName.DELAY, FxBeatPeriod.ONE),
        (FxName.ECHO, FxBeatPeriod.ONE_HALF),
        (FxName.REVERB, FxBeatPeriod.ONE_QUARTER),
    ),
}
