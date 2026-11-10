# Implementation Plan: Splitter Player for OP-XY

This is the authoritative, current plan for the `splitter_player` machine in
`machines/splitter-player`. It says what we are building and how. How and why it
differs from the original specification is recorded in
[PLAN_HISTORY.md](PLAN_HISTORY.md), which also points at the original text
(git commit `44db806`). Entries there are referenced below as `H-nn`.

Each section separates three kinds of statement:

- **Requirement**: the intended behavior.
- **SDK constraint**: a limit of the Open-XY SDK or the OP-XY that shapes the design.
- **Implementation**: how the code meets the requirement today.

## 0. Status

| Area | Status |
| --- | --- |
| Note mapping (zones, transposition, pitch limits) | Implemented; host-tested; confirmed working on the device, live and sequenced |
| Screen (header values, zone shading) | Implemented; confirmed on the device, including the first zone 2 key on white and black keys |
| Encoder 4 hidden | Implemented through an SDK change merged to `staging` (PR #476); confirmed on the device |
| Player menu name | Shows `splitter_play` (truncated); accepted for now, to be revisited with the SDK maintainer (section 12) |
| Setting the split by pressing a key | Not implemented; deferred, see section 11 |
| README | Written |
| Release and catalog entry | Not started, see section 12 |

## 1. Objective

**Requirement.** Implement an OP-XY note player that divides the 24-key physical
keyboard into exactly two zones. Each zone applies its own octave transposition to
incoming notes.

A player is a non-destructive note-mapping mechanism. It works on notes from the
physical keyboard and from the sequencer on the instrument track it is assigned
to. It never routes to other tracks, triggers other instruments, or rewrites
recorded notes. It uses the SDK's existing note-processing path, as the stock
Arpeggio, Hold and Maestro players do, and the existing `chords` player does.

**Scope note.** A second, separate machine, `splitter-aux`, will route zones to
other tracks. It is not part of this plan, and this player has no destination
track state.

## 2. The OP-XY keyboard

**Requirement.** The keyboard is 24 chromatic keys, numbered 1 to 24 from the left.
At octave 0 they span F3 to E5. The `-` and `+` buttons shift the whole keyboard by
octaves, from F-1 to E9 at the extremes, and must keep working unchanged. A key's
zone depends on its physical position, never on the keyboard octave.

**SDK constraint (H-02).** The SDK delivers a note's pitch only. There is no
physical key identity. `Controls::lowest_key` is the pitch of the lowest key at
the track's current octave, so a key's position is `note - lowest_key`
(0 to 23 for keys 1 to 24). A live note already carries the keyboard octave.
A sequenced note keeps the pitch it was recorded with, so its position is computed
against the octave at playback. This is the intended behavior: a track played at a
different keyboard octave than it was recorded at may place some notes in the other zone.

**Implementation.** Position is `note - lowest_key`. The split is a line through all
pitches: a position below `splitAtKey` is in zone 1 and a position at or above it is
in zone 2, however far outside the 24 keys of the current octave it lies. Nothing is
clamped or moved; the note is only assigned to a zone, and then its zone's
transposition applies. This is the intended behavior.

## 3. Identity and activation

**Requirement.** The user selects the player on an instrument track and the split
behavior applies to that track.

**Implementation.** `definition.json` has `id` `splitter_player` and `name`
`Splitter Player`. The id is also the C++ namespace and the prefix of the artwork
IDs, and is limited to 15 characters. It was lengthened from `splitter` so a later
`splitter_aux` can sit beside it (H-14).

**SDK constraint (H-14).** The player menu lists the machine's `id`, not its
`name`, and shows about 13 characters. `splitter_player` appears as
`splitter_play`. There is no separate on-device label field. This is accepted for
now; a `menuName` field will be reconsidered with the SDK maintainer.

## 4. Zones and split point

**Requirement.** There are exactly two zones. Zone 1 is keys 1 to `splitAtKey - 1`
and zone 2 is keys `splitAtKey` to 24. `splitAtKey` ranges from 2 to 24 (23
boundaries, including black-to-white ones) and defaults to 13. Neither zone is ever
empty. Encoder 2 sets it.

**Implementation.** Encoder 2 is a 23-choice enum labelled `2` to `24`, default
choice 13. The split is stored as that choice, not as player state.

## 5. Zone transposition

**Requirement.** Each zone has an octave transposition from -4 to +4, default 0.
Encoder 1 sets zone 1's and encoder 3 sets zone 2's. They are independent, and the
keyboard octave buttons never change them.

The final pitch is `originalPitch + 12 * globalOctave + 12 * zoneOctaves`.

**SDK constraint (H-03).** A live note's pitch already includes the keyboard octave,
so the player computes `note + 12 * zoneOctaves`.

**Pitch limits (H-04).** MIDI covers 0 to 127. A transposed note outside it is not
played. It is never clamped or wrapped, which follows the `chords` player's
documented convention. This is confirmed as intended.

**Implementation.** Encoders 1 and 3 are 9-choice enums labelled `-4` to `+4`,
default `+0`.

## 6. User interface

### 6.1 Layout

**Requirement.** The screen shows the player header with four encoder slots, and
below it a picture of the 24 keys that resembles the real OP-XY keyboard rather than
a piano.

**SDK constraint (H-07).** The header is the stock header. Its captions come from
the parameter labels in `definition.json` (at most 8 characters, shown lowercase)
and its values from the strings the player returns (at most 7 characters). The
`param_bar` in the design file is not used. The page itself is retained artwork
(`panel.svg.fragment`) that the player can only drive through 24 show/hide "dots",
a caption line, and the header strings.

### 6.2 Encoder slots

| Encoder | Parameter id | Caption | Values |
| --- | --- | --- | --- |
| 1 | `zone1_transpose` | `transp1` | `-4` to `+4` |
| 2 | `split_point_position` | `pos` | the number of `splitAtKey`, `2` to `24` |
| 3 | `zone2_transpose` | `transp2` | `-4` to `+4` |
| 4 | `unused` | none | none |

**Requirement.** The three active parameters are primary controls, available without
Shift. Encoder 4 is unused and shows nothing: no caption, no value, and turning it
does nothing. The note name is not shown next to the split number (H-08). The
captions `transp1` and `transp2` and the parameter ids were chosen by the project owner (H-12); the
original specification used `tr1` and `tr2`.

**Implementation.** The fourth parameter is declared `"absent": true`. This needs the
SDK change merged as PR #476 (H-13).

### 6.3 Keyboard picture

**Requirement.** All 24 keys are shown in their physical order, taken from
`designs/splitter.svg` (key boxes `r1` to `r24`, key pads `k1` to `k24`). Zone 1 keys
are drawn dark (#323232) and zone 2 keys light (#969696). The picture updates
immediately when the split changes and does not move when the keyboard octave
changes. The cue works whether the first zone 2 key is white or black.

**SDK constraint (H-09).** A player cannot recolor shapes at run time. It can only
show or hide up to 24 pre-drawn shapes. A key box's fill therefore cannot be changed
from the player.

**Implementation (H-09, H-11).** `artwork.py` generates `panel.svg.fragment` from
`designs/splitter.svg` in layers, from bottom to top:

1. All 24 key boxes in zone 2's color.
2. 23 zone 1 overlays (dots 0 to 22). Dot `k` covers keys 1 to `k + 1`, the zone 1
   keys for a split at key `k + 2`, in zone 1's color. The player shows exactly one.
3. A 24th dot that is never shown, because the SDK requires all 24.
4. The key pads as filled discs, then the key outlines, over the overlays.
5. The SDK's output keyboard along the bottom (H-20): 128 keys and 128 activity
   dots, which the SDK lays out and lights for the notes the player sounds.
6. The caption line the SDK requires, left empty.

Strokes are #000000, 1 px wide. Pads are circles of radius 10, and key corners are
square. The design file is the source of the key geometry and is not changed.

**Changed requirement (H-10).** The original specification marked the first zone 2
key by recoloring its ellipse (#646464). That marker is dropped. The first zone 2
key is recognizable as the first key of the lighter zone.

### 6.4 Shift

**Requirement.** Holding Shift does not change the meaning of the three active
encoders, and no Shift parameters exist.

**SDK constraint.** The player's turn handler applies the encoder's detents without a
Shift-dependent meaning, and the player gets no Shift state. Confirmed on the device:
holding Shift changes nothing (H-17).

## 7. State and parameter model

**Requirement.** The logical state is `splitAtKey` (2 to 24, default 13),
`zone1Transpose` and `zone2Transpose` (-4 to +4, default 0). New player instances
start at those defaults, and the settings persist with the project.

**SDK constraint (H-06).** Player state is zeroed, holds no settings, and is not
saved. Encoder values are saved as stock player parameters.

**Implementation.** The three values are the choices of encoders 1, 2 and 3, with
defaults set in `definition.json`. The player's `State` is empty. Nothing needs
restoring on reset.

## 8. Note processing

**Requirement.** For every incoming note, live or sequenced:

1. Find its zone from its position.
2. Apply that zone's transposition.
3. Pass the resulting note through the SDK's player pipeline, keeping its velocity.

The result stays on the same track and the recorded note is never changed. Zone
and transposition are evaluated when the note plays, so changing a setting affects
the next notes, including sequenced ones, without re-recording. Polyphony works and
each note uses its own zone.

**Note-off (H-05).** Held notes must not stick when a setting changes. The SDK
releases the tones it played for a root note when that note is released, so the
player does not recalculate anything on release. `release` returns `false` so the
stock player does the release.

**SDK constraint.** A note callback cannot tell a live key from a sequenced note.

**Implementation.** `press` builds a one-tone plan: pitch `note + 12 * zoneOctaves`,
original velocity, delay 0. It returns `true` with an empty plan when the result is
outside 0 to 127.

## 9. Implementation details

| File | Purpose |
| --- | --- |
| `machine.json` | `kind: player`, `sdk: 1.8` |
| `definition.json` | The four parameters (section 6.2) |
| `player.cpp` | `splitter_player` namespace: empty `State`, `press`, `release`, `display` |
| `artwork.py` | Generates `panel.svg.fragment` (section 6.3) |
| `panel.svg.fragment` | Generated page artwork; commit it after regenerating |
| `tests/gestures.cpp` | Host tests (below) |
| `../../designs/splitter.svg`, `splitter.afdesign` | Key geometry source and its editable design |

**Artwork rules the SDK enforces.** Dot elements must be a `path` or `circle` with
explicit fill, stroke, stroke width and a `matrix(1 0 0 1 x y)` transform. There is
no `style` attribute. Numbers have at most four decimals. All 24 dots and a caption
text node must be present.

**Tests.** `tests/gestures.cpp` covers: zone assignment at all 23 splits, pitch
maths with the zone transposition, the keyboard octave moving pitch but not the
split, sequenced notes (a different keyboard octave, and keys beyond the keyboard),
pitch limits, note release after a setting changes, and the display strings and lit
overlay. Run:

```sh
../.venv/bin/python ../open-xy/sdk.py test --machine machines/splitter-player
```

**Build** (from this repository). The player builds on its own with an SDK that
includes PR #481 (H-19):

```sh
../.venv/bin/python ../open-xy/sdk.py build --overwrite --out "../firmware/dev/001" \
  --stock-os ../firmware/1.2.1/os.ldr \
  --machine machines/splitter-player
```

The build writes `layout.json`, which holds the machine numbers (the player's type
and page). Pass it as `--layout` to later builds. Building without `chords` removed
its entry from `layout.json` (it was there from earlier builds), so add `--machine
../open-xy-core-machines/machines/chords` if the device should keep that player.
Stock firmware loads a player it doesn't recognize as Arpeggio.

Device operations need your explicit instruction each time (see `AGENTS.md`).

## 10. Acceptance criteria

Status key: **host** = covered by `tests/gestures.cpp`; **device** = reported working on
the OP-XY; **open** = not yet verified.

### Registration

- [x] The `splitter_player` player is available and selectable. Device: it appears in the menu (name truncated).
- [x] Selecting it applies the split to the selected track. Device (sequenced playback and zone view reported working).

### Zones

- [x] Exactly two zones; default split between keys 12 and 13. Host.
- [x] All 23 boundaries available; neither zone can be empty. Host.
- [x] The split stays on physical keys when the keyboard octave changes. Host.
- [x] Encoder 2 moves the split live. Host (value) and device (confirmed).

### Transposition

- [x] Zone transpositions are independent, default 0, -4 to +4. Host.
- [x] Final pitch is the note plus the zone's octaves; keyboard octave handled as in section 5. Host.
- [x] Encoders 1 and 3 set the zone transpositions. Device (confirmed working).

### Note processing

- [x] Zone 1 and zone 2 notes get their own transposition; polyphony works. Host.
- [x] Sequenced notes are processed, and the recorded data is untouched. Host, and device (reported working).
- [x] Release uses the original note, so changing a setting does not strand it. Host (release returns `false`; the SDK's release handling is not re-tested here).
- [x] Disabling the player restores normal note behavior. Device (confirmed working).
- [x] Repeated and overlapping notes are handled. Device (confirmed working).

### User interface

- [x] Encoder 1, 2 and 3 captions and values as in section 6.2. Host (strings). Device: the `pos` value was too wide with the note name (H-08); no other device report.
- [x] Encoder 4 empty on the device. Device (confirmed hidden after PR #476).
- [x] Shift does not change the three controls. Device (confirmed).
- [x] The keyboard picture follows the design and shows both zones. Device.
- [x] The first zone 2 key is distinguishable on white and black keys. Changed: boundary of the shading only (H-10). Device (confirmed visually).

### Quality

- [x] Settings persist as encoder values (SDK stock player parameters). By design; not separately tested.
- [x] Tests exist for zone assignment, pitch, notes, lifecycle, sequenced notes. Host.
- [x] The SDK check passes (`sdk.py check`, 493 tests on macOS).
- [x] No stock behavior is modified.

## 11. Scope boundaries

Excluded, as in the original plan: more than two zones, semitone transposition,
routing to other tracks, layering tracks, directly triggering other engines,
per-zone velocity or expression, configurable keyboard layouts, and Shift-modified
parameters.

## 12. Open questions and decisions needing approval

### Open

- **Release.** Tagging, the catalog entry and any hardware measurement
requirements (see `AGENTS.md`) have not been started.

### Parked

- **Menu name.** `splitter_player` is shown as `splitter_play`. This is accepted for
  now. The `menuName` SDK idea (H-14) will be reconsidered later with the SDK
  maintainer, as will setting the split by pressing a key (H-15).

- **Deferred (H-15).** Setting the split by pressing a key (or a `learn`
setting on encoder 4 that makes the next key set the split) is not in scope.
Players cannot see encoder clicks or Shift, and cannot change a parameter, so it
needs an SDK change that the SDK maintainer has not reviewed. A working prototype
was built and discarded. The design is recorded in `PLAN_HISTORY.md`. Encoder 2 is
the only way to set the split for now.
