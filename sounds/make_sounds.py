"""Gera os sons das notificações (um por tipo de evento) por síntese, só com a biblioteca padrão.

Uso: python sounds/make_sounds.py  →  sounds/<evento>.wav
"""

import math
import struct
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
RATE = 44100


def sweep(f0, f1, dur, vol=0.5, harmonics=(1.0,), decay=0.0, vibrato=0.0):
    """Tom que desliza de f0 a f1 Hz, com ataque/soltura curtos e decaimento exponencial opcional."""
    n = int(RATE * dur)
    out, phase = [], 0.0
    attack, release = int(RATE * 0.005), int(RATE * 0.02)
    for i in range(n):
        t = i / RATE
        freq = f0 + (f1 - f0) * (i / n)
        if vibrato:
            freq *= 1 + 0.03 * math.sin(2 * math.pi * vibrato * t)
        phase += 2 * math.pi * freq / RATE
        sample = sum(a * math.sin(phase * (k + 1)) for k, a in enumerate(harmonics)) / sum(harmonics)
        env = min(1.0, i / attack if attack else 1.0, (n - i) / release if release else 1.0)
        env *= math.exp(-decay * t)
        out.append(vol * env * sample)
    return out


def silence(dur):
    return [0.0] * int(RATE * dur)


def mix(*tracks):
    """Soma faixas (sobreposição), com a duração da maior."""
    length = max(len(tr) for tr in tracks)
    return [sum(tr[i] for tr in tracks if i < len(tr)) for i in range(length)]


SOUNDS = {
    # Chamado do suricato: dois "chirps" agudos subindo.
    "review_requested": lambda: (
        sweep(1700, 2600, 0.07, 0.45, (1, 0.3), vibrato=40) + silence(0.05)
        + sweep(1800, 2900, 0.09, 0.45, (1, 0.3), vibrato=40)
    ),
    # "Uh-oh": dois tons graves descendo, timbre mais áspero.
    "ci_failed": lambda: (
        sweep(523, 494, 0.15, 0.5, (1, 0, 0.35)) + silence(0.04) + sweep(415, 370, 0.28, 0.5, (1, 0, 0.35), decay=3)
    ),
    # Arpejo de sininho subindo (dó, mi, sol).
    "approved": lambda: mix(
        sweep(1047, 1047, 0.45, 0.35, (1, 0.25), decay=7),
        silence(0.08) + sweep(1319, 1319, 0.4, 0.35, (1, 0.25), decay=7),
        silence(0.16) + sweep(1568, 1568, 0.5, 0.4, (1, 0.25), decay=6),
    ),
    # "Hmm-hmm": dois tons médios caindo.
    "changes_requested": lambda: (
        sweep(740, 620, 0.13, 0.45, (1, 0.2)) + silence(0.07) + sweep(740, 620, 0.13, 0.45, (1, 0.2))
    ),
    # Blip curto e suave.
    "commented": lambda: sweep(1250, 1350, 0.09, 0.4, (1, 0.15), decay=18),
    # "Whoosh" subindo e um blip: hora do rebase.
    "parent_merged": lambda: (
        sweep(350, 1300, 0.25, 0.35, (1, 0.4, 0.2)) + silence(0.03) + sweep(1568, 1568, 0.18, 0.4, (1, 0.25), decay=12)
    ),
}


def write(path, samples):
    peak = max(abs(s) for s in samples) or 1.0
    scale = 0.85 / peak  # normaliza sem distorcer
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(b"".join(struct.pack("<h", int(s * scale * 32767)) for s in samples))


def main():
    for name, make in SOUNDS.items():
        write(HERE / f"{name}.wav", make())


if __name__ == "__main__":
    main()
