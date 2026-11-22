import wave
from pathlib import Path

import i18n

SOUNDS = Path(__file__).resolve().parent.parent / "sounds"


def test_every_event_kind_has_a_short_sound():
    kinds = [key[2:] for key in i18n.STRINGS["en"] if key.startswith("n_") and not key.startswith("n_body")]
    assert kinds
    for kind in kinds:
        with wave.open(str(SOUNDS / f"{kind}.wav")) as wav:
            assert 0 < wav.getnframes() / wav.getframerate() < 1.5, kind
