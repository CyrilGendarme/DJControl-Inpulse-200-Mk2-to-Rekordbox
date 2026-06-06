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


def get_nb_of_steps_until_next_available_effect(
    current_effect: FxName, backward: bool = False
) -> int:
    all_fx = list(FxName)

    if current_effect not in all_fx:
        raise ValueError(f"Unknown FX value: {current_effect!r}")

    current_index = all_fx.index(current_effect)

    for step in range(1, len(all_fx) + 1):
        direction = -step if backward else step
        next_effect = all_fx[(current_index + direction) % len(all_fx)]
        if next_effect in available_fx:
            return step

    raise ValueError("No available FX configured in available_fx.")


class FxBeatPeriod(str, Enum):
    ONE_SIXTEENTH = "1/16"
    ONE_EIGHTH = "1/8"
    ONE_QUARTER = "1/4"
    ONE_HALF = "1/2"
    THREE_QUARTERS = "3/4"
    ONE = "1"
    TWO = "2"
    FOUR = "4"
    EIGHT = "8"
    SIXTEEN = "16"

    # Specific to reverb decay time, not related to beat period
    ONE_PERCENT = "1%"
    TEN_PERCENT = "10%"
    TWENTY_FIVE_PERCENT = "25%"
    FIFTY_PERCENT = "50%"
    SEVENTY_FIVE_PERCENT = "75%"
    NINETY_PERCENT = "90%"
    ONE_HUNDRED_PERCENT = "100%"


available_beat_periods_per_fx = {
    FxName.DELAY: [
        FxBeatPeriod.ONE_SIXTEENTH,
        FxBeatPeriod.ONE_EIGHTH,
        FxBeatPeriod.ONE_QUARTER,
        FxBeatPeriod.ONE_HALF,
        FxBeatPeriod.THREE_QUARTERS,
        FxBeatPeriod.ONE,
        FxBeatPeriod.TWO,
        FxBeatPeriod.FOUR,
        FxBeatPeriod.EIGHT,
    ],
    FxName.ECHO: [
        FxBeatPeriod.ONE_SIXTEENTH,
        FxBeatPeriod.ONE_EIGHTH,
        FxBeatPeriod.ONE_QUARTER,
        FxBeatPeriod.ONE_HALF,
        FxBeatPeriod.THREE_QUARTERS,
        FxBeatPeriod.ONE,
        FxBeatPeriod.TWO,
        FxBeatPeriod.FOUR,
        FxBeatPeriod.EIGHT,
    ],
    FxName.REVERB: [
        FxBeatPeriod.ONE_PERCENT,
        FxBeatPeriod.TEN_PERCENT,
        FxBeatPeriod.TWENTY_FIVE_PERCENT,
        FxBeatPeriod.FIFTY_PERCENT,
        FxBeatPeriod.SEVENTY_FIVE_PERCENT,
        FxBeatPeriod.NINETY_PERCENT,
        FxBeatPeriod.ONE_HUNDRED_PERCENT,
    ],
    FxName.TRANS: [
        FxBeatPeriod.ONE_SIXTEENTH,
        FxBeatPeriod.ONE_EIGHTH,
        FxBeatPeriod.ONE_QUARTER,
        FxBeatPeriod.ONE_HALF,
        FxBeatPeriod.ONE,
        FxBeatPeriod.TWO,
        FxBeatPeriod.FOUR,
        FxBeatPeriod.EIGHT,
        FxBeatPeriod.SIXTEEN,
    ],
    FxName.ROLL: [
        FxBeatPeriod.ONE_SIXTEENTH,
        FxBeatPeriod.ONE_EIGHTH,
        FxBeatPeriod.ONE_QUARTER,
        FxBeatPeriod.ONE_HALF,
        FxBeatPeriod.ONE,
        FxBeatPeriod.TWO,
        FxBeatPeriod.FOUR,
        FxBeatPeriod.EIGHT,
    ],
}


FxPresetEntry = tuple[FxName, FxBeatPeriod]
FxPreset = tuple[FxPresetEntry, FxPresetEntry, FxPresetEntry]


fx_presets: dict[str, FxPreset] = {
    "preset_1": (
        (FxName.TRANS, FxBeatPeriod.ONE),
        (FxName.REVERB, FxBeatPeriod.FIFTY_PERCENT),
        (FxName.ROLL, FxBeatPeriod.FOUR),
    ),
    "preset_2": (
        (FxName.TRANS, FxBeatPeriod.ONE_HALF),
        (FxName.ECHO, FxBeatPeriod.TWO),
        (FxName.ROLL, FxBeatPeriod.EIGHT),
    ),
}
