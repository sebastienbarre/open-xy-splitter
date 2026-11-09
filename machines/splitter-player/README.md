# Splitter Player

A note player for the OP-XY that splits the 24-key keyboard into two zones, each
with its own octave transposition. Play bass with your left hand and a lead an
octave or two higher with your right, on a single instrument track.

The player works on the track it is assigned to. It does not route notes to other
tracks or trigger other instruments. For that, see the separate splitter aux machine.

## Using it

Select **Splitter Player** as the track's player (Shift + the player key). The
keyboard splits into:

| Zone | Keys | Screen |
| --- | --- | --- |
| Zone 1 | key 1 up to the key before the split | darker keys |
| Zone 2 | the split key up to key 24 | lighter keys |

Keys are numbered 1 to 24 from the left. At the default keyboard octave they are F3
to E5. By default the split is between keys 12 and 13: zone 1 is F3 to E4 and zone 2
is F4 to E5. The split can sit between any two keys, white or black.

## Encoders and screen

| Encoder | Caption | Control | Range | Default |
| --- | --- | --- | --- | --- |
| 1 | z1tr | Zone 1 transposition, in octaves | -4 to +4 | +0 |
| 2 | pos | Split point: the number of the first key of zone 2 | 2 to 24 | 13 |
| 3 | z2tr | Zone 2 transposition, in octaves | -4 to +4 | +0 |
| 4 | | Not used; shows nothing | | |

All three controls work directly, and Shift does not change their meaning. Each
encoder moves one step per click.

The screen shows the keyboard, with the zone 1 keys darker and the zone 2 keys
lighter. The picture follows the split as you turn encoder 2 and stays on the same
physical keys when you change the keyboard octave.

## How notes are played

- A key's zone depends on its physical position, so the **`-` and `+` octave
  buttons move the whole keyboard**, both zones together, without moving the split.
- A note sounds at its key's pitch plus its zone's transposition, in whole octaves.
  For example, with the keyboard at +1, zone 1 at +0 and zone 2 at -1, zone 1 plays
  F4 to E5 and zone 2 plays F3 to E4.
- The two zones are independent: changing one zone's transposition does not affect
  the other, and the keyboard octave never changes either transposition.
- Notes in both zones can sound together. Each note follows its own zone.
- Velocity is kept as played.
- A note whose transposed pitch falls outside the MIDI range, 0 to 127, is not played.
  Nothing is wrapped or clamped.
- If you change the split or a transposition while a key is held, that note still
  stops when you release the key.

### Sequencer

Recorded notes are not changed. Notes are recorded at the pitch you played, and the
split and transpositions apply when they play back. Change a setting and the next
notes follow it, with no need to record again.

A recorded note keeps its pitch, so its zone is worked out against the keyboard
octave in use during playback. If you play a track at a different keyboard octave
than it was recorded at, some notes may fall in the other zone.

### Saved settings

The three settings are saved with the project, like other player controls. A new
player starts at the defaults above.

## Limitations

- The split can be set only with encoder 2. Setting it by pressing a key needs
  SDK support that does not exist yet.
- The player's name in the player menu is cut off (it reads `splitter_play`).
  The menu shows the machine id, not its display name.

## Building and testing

Requires the Open-XY SDK with two changes that are in `staging` after SDK 1.10: one
that lets a player leave an encoder empty (open-xy pull request #476) and one that
lets a player build without any other machine (#481). From this repository:

```sh
../.venv/bin/python ../open-xy/sdk.py test --machine machines/splitter-player

../.venv/bin/python ../open-xy/sdk.py build --overwrite --out "../firmware/dev/001" \
  --stock-os ../firmware/1.2.1/os.ldr \
  --machine machines/splitter-player
```

Add a `--machine` for each other machine you want on the device. The build writes
`layout.json`; keep it and pass it as `--layout` to later builds, so the player
keeps its type number. Stock firmware loads a player it does not recognize as
Arpeggio.

[tests/gestures.cpp](tests/gestures.cpp) covers the zones at all 23 split positions,
the transposition maths, the keyboard octave, sequenced notes, the pitch limits,
releasing notes after a setting changes, and the strings and overlay on the screen.

## Files

| File | Contents |
| --- | --- |
| [player.cpp](player.cpp) | The player: zone lookup, transposition, screen values |
| [definition.json](definition.json) | The four encoders |
| [artwork.py](artwork.py) | Generates the screen artwork from [../../designs/splitter.svg](../../designs/splitter.svg) |
| [panel.svg.fragment](panel.svg.fragment) | The generated artwork; regenerate with `python artwork.py` |
| [PLAN.md](PLAN.md) | The current implementation plan and open questions |
| [PLAN_HISTORY.md](PLAN_HISTORY.md) | How and why the plan changed |
