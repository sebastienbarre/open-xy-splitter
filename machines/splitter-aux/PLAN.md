# Implementation Plan: Splitter Aux

Status: **postponed** until the SDK maintainer returns (owner decision, 2026-11-09).
Nothing is implemented. This file records the requirements, what the SDK
investigation found, and the proposed plan, so the work can resume without
repeating the investigation.

The machine is the sibling of the [Splitter Player](../splitter-player/PLAN.md)
(machine id `splitter_player`), and the machine id here is `splitter_aux`
(name `Splitter Aux`).

Each statement below is one of: a **requirement** (what the owner asked for), an
**SDK finding** (read from the SDK source, its docs or the pull requests named),
a **proposal** (my suggestion, not agreed), or **unverified** (needs a check).

## 1. Objective

**Requirement.** The Splitter Player splits the 24-key keyboard into two zones, each
with its own octave transposition. As a player it is a non-destructive note mapping:
it works on the notes of its own track and never routes to other tracks.

The Splitter Aux machine covers the more useful case: assign a different
instrument track to each zone, route the notes to those tracks so they can be
recorded in the sequencer, and keep the zone transposition.

The OP-XY community agreed that this is the job of an aux machine. An aux machine
lives on an aux track (the SDK supports only the CV track, track 12) and, while on
screen, may send notes to other tracks.

## 2. Requirements (as given by the owner)

- **Presentation.** Same as the Splitter Player: the same keyboard picture, and
  encoder 2 moves the split point in the same way.
- **Destinations.** Encoder 1 chooses the instrument track, 1 to 8, for zone 1.
  Encoder 3 does the same for zone 2.
- **Transposition.** The player's octave transposition moves to the Shift key, as on
  the stock synth engines. Shift + encoder 1 chooses zone 1's octaves and shift +
  encoder 3 zone 2's, with the same choices as the player (-4 to +4).
- **No second row.** Do not use the idiom of a second row of four label/value pairs
  switched by clicking an encoder. It is not idiomatic to the OP-XY.
- **Not recording.** While the machine is active and on screen, a key pressed on the
  keyboard is routed to the instrument track of its zone, with the zone's
  transposition applied.
- **Recording.** While recording, the note is recorded in the sequencer in that
  track, with the transposition applied.
- **Parameters.** `zone1_dest` (label `z1dest`), `zone2_dest` (label `z2dest`).
  Encoder 4 stays unused, with or without Shift.
- **Process.** Investigate feasibility before implementing. Follow existing SDK
  abstractions and conventions, invent no API names, event types, drawing methods
  or routing mechanisms, and document the limits found. Do not change stock aux
  behavior. Keep it small, focused and heavily commented, as the player is.
  Share common code with the player in a separate header or file in a separate
  directory.

## 3. Investigation: what the SDK provides

Sources: `docs/api.md` ("Track control", "Aux tracks"), `docs/abi-1.2.1.md`,
`docs/display.md`, `docs/extensions.md`, `sdk/include/opxy/track_control.hpp`, the
merged pull request #360, the open pull request #378, issue #345 and the Conductor
repository (`../OP-XY-Conductor`).

### 3.1 What an aux machine is

**SDK finding.** There is no `kind: aux`. An aux machine is a `kind: synth` machine
with `"sdk": "1.9"` (or later), `resources.trackControl` (`"unique": true`,
`"aux": [12]`, `stateBytes`) and a `control.cpp`. The existing
`machine.json` here says `"kind": "aux"`, which the SDK does not accept; it must become
`"kind": "synth"`.

It runs on track 12, chosen with Shift + M1 on that track. While it holds the
playing pattern the stock CV and gate are silenced. Its own engine is silent
(Conductor's README says the same of its engine); the machine acts through track
control.

`control(state, input, overlay)` runs on the GUI side once per stock GUI tick
(about 60 Hz). Its display is separate code (a synth drawing display) that reads
words the control passes in `overlay.display` through `from_control(index)`.

`Input` on staging has: `track`, `values[16][58]` (the live parameter words of every
track, the machine's own eight controls at `values[11][0..7]`), `elapsed_us`,
`transport`, `page_key` (M1 to M4) and `muted`. `Overlay` has parameter overlays
(`add`), stored parameter writes (`store`, which the SDK ignores on the machine's
own track), and 4 display words.

### 3.2 Requirement against the SDK

| Requirement | Staging | With #378 (open) |
| --- | --- | --- |
| Keyboard picture, encoder 2 split, exact zone colors | Possible. The display is a drawing display with a palette (up to 16 entries); nodes can be recolored each frame, so the exact #323232, #969696 and #646464 colors are available, unlike the player. | Same |
| Encoders 1 and 3 as destination tracks 1 to 8 | Possible. They are ordinary enum parameters, saved, sequenced and lockable like any track parameter. | Same |
| Encoder 4 unused | Possible. An absent slot on an aux page turns nothing (#360). | Same |
| Shift + encoder 1 and 3 for the transposition | **Not possible.** For SDK-owned machines Shift + turn maps back to the same position with a finer step (`abi-1.2.1.md`, "Alternate controls"); stock's rule that Shift edits parameters 4 to 7 applies to stock engines only. The display cannot read Shift either (`display.md`: a synth page reads 0 for `shift`). The control cannot read it. | Possible, differently from stock: `Input.shift` and `own_turns`, with the machine keeping the transposition as its own state (see 3.4). |
| Receive keyboard key presses | **Not possible.** `Input` has no keyboard events. The extension events cover the selected instrument track only (`recordable_note_on`, `selected_note_off`), and `input_activity` has no note. Track 12 is not an instrument track. | **Not possible** |
| Send notes to tracks 1 to 8 | **Not possible.** | `opxy::control::play(overlay, track, pitch, velocity, length_us)`, with limits (3.3) |
| Record the routed notes | **Not possible** | **Not possible**: `play()` is "never recorded" (3.3) |

The statement that aux machines may send notes to other tracks is therefore true
only of #378, which is not merged, and only for unrecorded notes.

### 3.3 Notes: pull request #378

Open, by mmockett, reopening #346 (which was merged and then reverted by mistake in #377).
Its branch was cut from an older staging, so it needs a rebase before it can
be checked out against current staging. It is tracked by issue #345; Conductor depends
on it (`gh pr checkout 378` to build against it).

**SDK finding.** It adds:

- `play()`, which starts a note on an instrument track (0 to 7) through stock's live
  note-on, "as a track's keyboard would play them but never recorded". Limits: 32
  notes per tick, 48 sounding across all machines, length 1 microsecond to 8 s, and
  a zero length is dropped.
- Notes end after their length, when the sequencer stops (a transition from playing
  to stopped), or when the machine leaves its track or is muted. There is no
  note-off call, so a held key cannot be mirrored with an early end.
- `own_turns`, `Input::shift` and `Input::turns` (a detent has a slot and a
  direction). While `own_turns` is set, the track's encoders edit nothing and the
  machine receives every turn of every encoder.
- 16 display words instead of 4.
- Notes start on a GUI tick. Conductor measured 0 to 17 ms late (median 5.5 ms) on
  the device. That is audible latency for live playing.

**SDK finding.** The code calls stock's live note-on `8d595738` and note-off
`8d595420` with source 1, flags 0 and no event, which is why the notes are not
recorded (`track_control.cpp` in the #378 branch).

### 3.4 Shift

**SDK finding.** With #378 a machine sees Shift and raw turns, but Shift is not a
parameter bank: the machine would keep the two transpositions in its own saved state
(`savedBytes` with `control_save` and `control_load`, saved in the project
companion). They would not be sequenced or parameter-locked.

**Unverified.** `own_turns` is read for the next tick, and it claims all four
encoders. To keep encoders 1 to 3 as ordinary saved parameters, the machine would ask
for it only while Shift is held. A turn in the first tick after Shift is pressed would
then reach stock's editor as a shifted turn of a parameter (a finer step of the
destination or split), which needs checking on the device.

### 3.5 Keyboard input and recording

**SDK finding.**

- Stock's immediate input accepts keyboard key codes 26 to 49 (`abi-1.2.1.md`), the
  24 physical keys. The SDK already hooks the aux controller's key handler (`8c08fd30`)
  for M1 to M4, so key codes are available there in principle.
- On the audio side, a note on track 12 reaches stock's CV gate call `8d50e95c`, which
  the SDK skips while a machine holds the track.
- The extension runtime has actions (`insert_notes`, `replace_notes`) that write notes
  into any instrument track's pattern, but they work only inside a `queued_control`
  callback for a key the extension claims (the Record double tap), so they cannot
  record live key presses.

**Unverified.**

- Whether stock exposes a key's velocity at those sites.
- Whether a hook on key codes 26 to 49 on the aux controller is feasible, and whether
  the audio-side site can hand events to the GUI (they share no memory; the SDK uses
  published words and marks).
- The keyboard octave of track 12: an aux machine is not told it (`sdk_track_octaves`
  covers instrument tracks). A physical key index from the key codes would make the
  split exact without it.
- Whether stock's recorder can be made to record a note routed to another track.
  Stock records live keyboard notes on the selected track. Nothing in the SDK does
  this for another track, and it would need analysis of the stock OS.

### 3.6 Timing and other limits

- Notes start on a GUI tick (about 60 Hz), so up to one tick (about 17 ms) late.
- Up to 32 notes per tick and 48 held across all machines. A GUI stall plays held
  notes at once and drops past 32 (Conductor).
- Only tracks 1 to 8 are targets, and the machine must not target its own track.
- Conductor, the only known aux machine, depends on #378 and cannot be built against
  staging.

## 4. Proposed design

### 4.1 Shared code

**Proposal.** Move what the player and the aux machine share to a new directory at the
repository root, outside `machines/` so it is not taken for a machine:

```txt
common/splitter/zones.hpp      split and zone maths, encoder decoding, constants
common/splitter/keyboard.py    key geometry from designs/splitter.svg, pixel snapping, shared by both artwork scripts
machines/splitter-player/      refactored to use them; its tests must stay green
machines/splitter-aux/         the new machine
```

Rules for the header: `#pragma once` (the SDK's lint rejects `#if`, `#ifndef`), plain
C++11, only `<opxy/types.hpp>`, one-line documented functions as in the player.

**Unverified.** That `#include "../../common/splitter/zones.hpp"` from a machine's
source builds. The SDK lint does not forbid it, but build provenance covers only
files under the machine folder, so a trial build must confirm it works and what
provenance says. Fallback: a small script that copies the shared files into each
machine folder, with a test that fails when the copies differ.

### 4.2 Machine files

Modeled on Conductor (`control.cpp`, `display.cpp`, `display.h`, `words.h`,
`definition.json`, `panel.svg.fragment`, `tests/`):

| File | Purpose |
| --- | --- |
| `machine.json` | `kind: synth`, `sdk: 1.9` at least (to be confirmed with the maintainer) |
| `definition.json` | Machine id `splitter_aux`, the parameters in 4.3, `trackControl` (`unique`, `aux: [12]`, `stateBytes`, and `savedBytes` if the transpositions are kept) |
| `control.cpp` | Reads the controls and key events, works out zones, plays notes, tracks Shift |
| `display.cpp`, `display.h` | The page, from the words in `words.h` |
| `words.h` | What the control tells the display each tick: split, destinations, transpositions and Shift |
| `panel.svg.fragment`, `artwork.py` | Page artwork, from the shared key geometry |
| `tests/` | Host tests of the control with a fake `Input` |

### 4.3 Parameters

| Encoder | Id | Label | Choices | Default (proposal) |
| --- | --- | --- | --- | --- |
| 1 | `zone1_dest` | `z1dest` | tracks 1 to 8 | 1 |
| 2 | `split_point_position` | `pos` | keys 2 to 24 | 13 |
| 3 | `zone2_dest` | `z2dest` | tracks 1 to 8 | 2 |
| 4 | none | none | absent slot | |

Shift + encoder 1 and 3: transposition -4 to +4, default 0 (requirement), as machine
state (3.4). The id and label of encoder 2 and the default destinations are
proposals; the owner has not chosen them.

### 4.4 Behavior (once the SDK supports it)

- Zone: from the physical key index, `key < split` is zone 1 and otherwise zone 2.
- Routing: the note goes to the destination track of its zone, at the key's pitch plus
  `12 * zoneOctaves`, dropped when outside MIDI 0 to 127 (as in the player).
- Release: the note ends with the key. This needs a note-off or a length the
  machine can end (3.3).
- Not recording: the note is played on the destination track.
- Recording: the note is also recorded on the destination track (requirement, not
  currently possible).
- Settings persist like any track parameter. The transpositions persist through
  the machine's saved state.

## 5. Phases

| Phase | Content | Needs |
| --- | --- | --- |
| 1 | Shared code and the player's refactor; a `splitter_aux` with the three parameters, the absent encoder 4, the keyboard page drawn with the palette (same look as the player), host tests. Makes no sound. | Staging only. The player's tests unchanged. |
| 2 | Receive key presses and releases; route notes with `play()` | #378 merged; a new SDK event for keyboard input on a held aux track (physical key index 0 to 23, velocity if stock has one); a note-off or early end for `play()` |
| 3 | Shift + encoder 1 and 3 transposition | #378 (`Input.shift`, `own_turns`) |
| 4 | Recording the routed notes | Analysis of stock's recording path and probably a new SDK capability. Might not be possible. |

Phase 1 is possible today but was postponed with the rest (owner decision,
2026-11-09).

## 6. Acceptance criteria (for the finished machine)

- [ ] `splitter_aux` can be chosen on track 12 (Shift + M1), and is not offered on tracks 1 to 8.
- [ ] The page shows the keyboard with both zones, updated when the split changes, as the player does.
- [ ] Encoders 1 and 3 choose destination tracks 1 to 8. Encoder 2 moves the split between key 2 and key 24. Encoder 4 does nothing, with or without Shift.
- [ ] Shift + encoder 1 and 3 set the zone transpositions, -4 to +4, with no second row of parameters.
- [ ] A key pressed while the machine is on screen and not recording sounds on its zone's destination track, transposed.
- [ ] While recording, the note is recorded on its destination track, transposed.
- [ ] Released keys release their notes. No stuck notes when a setting changes.
- [ ] Settings persist with the project.
- [ ] Stock aux behavior is unchanged, and the Splitter Player's tests still pass.
- [ ] Heavily commented code, in the style of the player.

## 7. Open questions

**For the owner.**

1. Phase 1 on its own once work resumes, or wait for the SDK work?
2. Recording: keep it as a goal if Phase 4 turns out to be impossible, or drop it?
3. Split-point marker: the same look as the player (no #646464 marker), or the original
   marker, which the palette now allows?
4. Without #378: leave the transposition unavailable until it lands? A second row
   of parameters was ruled out.
5. Default destinations, and the id and label of encoder 2.

**For the maintainer.**

1. The status and plan for #378, which needs a rebase, and whether it will stay within
   SDK 1.9 or become 1.10.
2. Keyboard input for a held aux track: is a new event acceptable, which site, which
   thread, and does stock give a velocity?
3. A way to end a played note early, for a held key.
4. Whether recording routed notes on another track is in scope for the SDK at all.
5. The keyboard octave of track 12, if physical key indices are not provided.
6. Whether shared code outside the machine folder is acceptable for provenance and the
   catalog.

## 8. Out of scope

Changing stock aux behavior, a second row of parameters switched by clicking an encoder,
more than two zones, routing to tracks 9 to 16 or to MIDI channels, and any SDK
change made without the maintainer.
