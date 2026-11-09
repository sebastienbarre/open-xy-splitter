# Implementation Specification: Splitter Player for OP-XY

## 1. Objective

Implement a new OP-XY player named `splitter`.

The purpose of this player is to divide the OP-XY's 24-key physical keyboard into exactly two zones. Each zone can apply an independently configurable octave transposition to incoming notes.

The player must follow the existing OP-XY player architecture and conventions. In particular, it should behave like the stock `arpeggio`, `hold`, and `maestro` players.

### 1.1 Player semantics

A player is a non-destructive note-mapping mechanism.

Players operate on notes that originate from either:

- Physical keyboard input played by the user.
- Notes recorded in the sequencer on the instrument track to which the player is assigned.

A player transforms or maps incoming notes into other notes or chords. It does not reach out to other instrument tracks, trigger other instruments, or perform instrument-track routing.

The `splitter` player must follow these principles:

- It operates exclusively on the instrument track to which it is assigned.
- It divides incoming notes into two zones based on their physical keyboard position.
- It applies the appropriate octave transposition according to the zone.
- It does not change the instrument track receiving the notes.
- It does not directly interact with other instrument tracks or their engines.
- It does not modify the underlying recorded note data destructively.

The player must use the existing note-processing mechanisms to transform incoming notes, rather than implementing its own instrument-triggering or track-routing infrastructure.

## 2. Understanding the OP-XY keyboard

### 2.1 Physical keyboard

The OP-XY has 24 physical keys spanning two octaves.

At its default octave setting (0), the keyboard covers:

- Leftmost key: F3
- Rightmost key: E5

The keyboard contains 24 chromatic keys, covering F3 through E5 inclusive. This is commonly described as a two-octave keyboard, although the interval between its extreme keys is 23 semitones.

The keyboard should be considered a fixed collection of 24 physical key positions, numbered 1 through 24, from left to right.

### 2.2 Virtual keyboard range

Although the OP-XY has only 24 physical keys, the user can shift their octave using the `-` and `+` buttons.

The default octave setting is 0:

| Octave setting | Keyboard range |
| - | - |
| -4 | F-1 – E1 |
| -3 | F0 – E2 |
| -2 | F1 – E3 |
| -1 | F2 – E4 |
| 0 | F3 – E5 |
| +1 | F4 – E6 |
| +2 | F5 – E7 |
| +3 | F6 – E8 |
| +4 | F7 – E9 |

The full playable range therefore extends from F-1 to E9.

The octave buttons shift the entire physical keyboard by one octave at a time. They do not change the physical arrangement or number of keys.

The implementation must preserve this existing behavior.

### 2.3 Physical position versus musical pitch

An important distinction for this implementation:

- Physical key position determines which zone a note belongs to.
- The current keyboard octave determines the note's initial pitch.
- Zone transposition determines the final pitch produced by the player.

Changing the global keyboard octave must never change the physical split point.

The player must also support notes originating from the sequencer, not just live keyboard input. Where applicable, it must use the physical key position or equivalent source-note information available to the player architecture to determine zone membership.

If the existing architecture does not preserve the necessary physical-position information for sequencer notes, investigate how existing players handle note mapping and determine the appropriate way to associate sequencer notes with the two zones. Do not assume that physical key positions can always be reconstructed from MIDI pitches.

## 3. Player activation

The new player must be registered as `splitter`, following the same mechanism used by the existing stock players.

A user activates keyboard splitting by selecting `splitter` as the player for an instrument track.

The player establishes exactly two zones.

Both zones belong to the instrument track on which the player is activated.

There must always be exactly two zones. Supporting additional zones is explicitly outside the scope of this implementation.

## 4. Zone definition and split point

### 4.1 Default configuration

The 24 physical keys are divided into two contiguous zones.

By default, the split point is between physical keys 12 and 13:

- Zone 1: keys 1–12 (12 keys).
- Zone 2: keys 13–24 (12 keys).

### 4.2 Adjustable split point

The user can adjust the split point using encoder (knob) #2.

There are 23 possible split positions:

| Split position | Zone 1 | Zone 2 |
| - | - | - |
| Between keys 1 and 2 | 1 key | 23 keys |
| Between keys 2 and 3 | 2 keys | 22 keys |
| ... | ... | ... |
| Between keys 12 and 13 | 12 keys | 12 keys |
| ... | ... | ... |
| Between keys 23 and 24 | 23 keys | 1 key |

Both zones must always contain at least one physical key.

Consequently, the split point must never move before key 1 or after key 23.

The encoder should provide an appropriate representation of the split position, following the conventions of existing players.

Internally, prefer representing the split point as the index of the first key in Zone 2 (`splitAtKey`), with a valid range of 2–24 and a default value of 13.

Zone 2 then starts at `splitAtKey`.

The split point is based exclusively on physical key position. It is not restricted to boundaries between white keys. All 23 physical boundaries must be available, including boundaries between a black key and a white key.

## 5. Independent zone transposition

Each zone has an independently configurable octave transposition.

Both transposition parameters are directly accessible using the primary encoder controls. They are not Shift-modified parameters.

The transposition range is -4 to +4 octaves, inclusive, in increments of one octave.

### 5.1 Zone 1 transposition

Encoder #1 controls the octave transposition for Zone 1.

- Default: +0 octaves.
- Positive values transpose upwards.
- Negative values transpose downwards.

### 5.2 Zone 2 transposition

Encoder #3 controls the octave transposition for Zone 2.

- Default: +0 octaves.
- Positive values transpose upwards.
- Negative values transpose downwards.

### 5.3 Global octave interaction

The existing `-` and `+` keyboard octave controls must continue to work.

They shift the entire physical keyboard together.

The zone-specific octave transpositions must remain unchanged when the global octave is modified.

For example:

- Global keyboard octave: +1.
- Zone 1 transposition: 0.
- Zone 2 transposition: -1.

The resulting pitch ranges are:

- Zone 1: F4–E5.
- Zone 2: F3–E4.

The final note pitch is calculated as:

`finalPitch = originalPitch + (globalOctave * 12) + (zoneOctaveTranspose * 12)`

Use the existing OP-XY pitch representation and note conversion utilities wherever possible.

The allowable transposition range should follow the existing player/engine conventions and the supported pitch range. Inspect the existing implementation before choosing limits. Do not arbitrarily introduce a new pitch range.

If the resulting pitch exceeds the supported range, follow the existing note-range handling conventions rather than introducing undocumented wrapping or clipping behavior.

### 5.4 Transposition independence

Changing the transposition of one zone must never affect the other.

Changing the global keyboard octave must never modify either zone's configured transposition.

The player must preserve the relative pitch relationship between the two zones when the global octave changes.

## 6. User interface

### 6.1 General layout

When the `splitter` player is selected, the screen should display:

1. The usual player parameter interface at the top, with four encoder parameter slots laid out horizontally.
2. A graphical representation of the 24 physical OP-XY keyboard keys below it.

The visual keyboard must resemble the actual OP-XY keyboard, not a conventional piano keyboard.

Refer to the `splitter.svg` SVG file to build the layout. Each UI element in this SVG has a unique `id`. More on this below.

Do not introduce a generic piano keyboard graphic.

### 6.2 Encoder parameter display

The four encoder slots should display the following parameters:

| Encoder | Parameter | Description | SVG `id` of label | Label to use | SVG `id` of value | Values to use |
| - | - | - | - | - | - | - |
| #1 | Zone 1 Transpose | Octave transposition for Zone 1 | `param1` | "tr1" | `value1` | -4, -3, -2, -1, +0, +1, +2, +3, +4 |
| #2 | Split Point | Boundary between the two zones | `param2` | "pos" | `value2` | value of `splitAtKey` with the note shown in parenthesis after it, without the octave, e.g. "13 (F)" |
| #3 | Zone 2 Transpose | Octave transposition for Zone 2 | `param3` | "tr2" | `value3` | -4, -3, -2, -1, +0, +1, +2, +3, +4 |

Encoder #4 is unused for now.

All three active parameters are primary controls and should be displayed in the normal player UI without requiring Shift.

The values displayed should reflect the current configuration.

### 6.3 Keyboard visualization

Display all 24 physical keys in their actual left-to-right order.

The keys are already preset in the `splitter.svg` SVG file, under the group with `keyboard` ID.

Each key is made of two elements:

- a box representing the outline of the physical key. This is a SVG `path` with an ID starting with the letter `r` and followed by the index of the key (e.g. `r13`).
- a circle representing the area inside the physical key that the user is making contact with. This is a SVG `ellipse` with an ID starting with the letter `k` and followed by the index of the key (e.g. `k13`).

The visualization must distinguish Zone 1 from Zone 2. To do so, each SVG box in Zone 1 should have its `fill:none` attribute changed to RGB(50, 50, 50) i.e. hex #323232, and each SVG box in Zone 2 should have its `fill:none` changed to RGB(150, 150, 150) i.e. hex #969696. The `stroke` attribute should NOT be changed.

The split point must be represented by changing the `fill:none` attribute of the SVG ellipse of the first key belonging to Zone 2 to RGB(100, 100, 100) i.e. #646464.

For example, with the default split:

- Keys 1–12 belong to Zone 1 and should all have their boxes set to fill #323232.
- Keys 13–24 belong to Zone 2 and should all have their boxes set to fill #969696.
- Key 13 should have its ellipse set to fill #646464.

When the user changes the split point with encoder #2:

- The visual division between the zones must update immediately.
- The position of the split point on the new first key of Zone 2 should be updated immediately.

These visual cues should be correct regardless of whether the first key of Zone 2 is a white or black key.

The visualization should remain fixed in physical-key space when the global keyboard octave changes.

### 6.4 Shift behavior

The three active parameters are controlled directly by their respective encoders.

Holding Shift must not change the meaning of these three controls.

In particular:

- Encoder #1 continues to control Zone 1 transposition.
- Encoder #2 continues to control the split point.
- Encoder #3 continues to control Zone 2 transposition.

There are no alternate Shift-modified parameters required for this initial implementation.

Follow existing player conventions for displaying the UI while Shift is held, without introducing additional parameters or changing the behavior described above.

## 7. State and parameter model

The implementation should maintain the following logical state:

- `splitAtKey`: first physical key belonging to Zone 2, integer 2–24, default 13.
- `zone1Transpose`: octave transposition for Zone 1, default 0.
- `zone2Transpose`: octave transposition for Zone 2, default 0.

The two zones are derived from `splitAtKey`:

- Zone 1 contains physical keys 1 through `splitAtKey - 1`.
- Zone 2 contains physical keys `splitAtKey` through 24.

There is no destination instrument track state. Both zones operate on the instrument track to which the player is assigned.

Parameter changes should be reflected immediately in the UI and in subsequent note processing.

Follow the existing player parameter persistence and serialization conventions. Ensure that the default values are correctly restored when creating a new player instance.

## 8. Note processing and edge cases

The following behaviors must be handled correctly.

### 8.1 Zone boundaries

- Key 1 always belongs to Zone 1.
- Key 24 always belongs to Zone 2.
- The split boundary is inclusive for Zone 2 and exclusive for Zone 1.
- Every physical key belongs to exactly one zone.

For a split start at key 13:

- Keys 1–12 belong to Zone 1.
- Keys 13–24 belong to Zone 2.

### 8.2 Note mapping

For every incoming note:

1. Determine its zone using the physical key position or equivalent source-note information.
2. Select the transposition configured for that zone.
3. Calculate the resulting pitch.
4. Pass the transformed note through the existing player/note-processing mechanism.
5. Preserve the original note's other properties unless existing player conventions specify otherwise.

The resulting note must remain on the same instrument track.

The player must not:

- Route notes to another instrument track.
- Trigger another instrument engine directly.
- Bypass the existing player processing pipeline.
- Modify the original sequencer note data destructively.

### 8.3 Note-on and note-off

Note-off events must correspond to the transformed pitch of their associated note-on events.

Do not recalculate routing or pitch using the current configuration when a note-off arrives.

This matters because the user may change the split point or transposition while notes are being held.

Maintain whatever active-note bookkeeping is necessary to preserve this relationship, following the existing player architecture.

Handle repeated notes, overlapping notes, and simultaneous notes correctly.

### 8.4 Configuration changes during playback

Changing the split point or either transposition should affect subsequent note-processing events.

Already-active notes must retain their original note-off correspondence.

Avoid stuck notes when parameters change while keys are held.

### 8.5 Sequencer playback

The player must operate on notes recorded in the sequencer, in addition to live keyboard input.

The same zone and transposition rules should apply to sequencer notes.

The player must not destructively rewrite the recorded notes.

Disabling the player or selecting another player should restore the original note behavior, according to the existing player architecture.

Do not implement a separate sequencer playback system. Use the existing mechanism through which stock players process sequencer notes.

### 8.6 Multiple simultaneous notes

The player must support polyphonic note input.

Notes in both zones may be played simultaneously.

Each note must be transformed according to its own zone, without affecting other active notes.

### 8.7 Pitch limits

If a transposed note exceeds the supported pitch range, follow existing OP-XY player conventions.

Do not introduce undocumented pitch wrapping, clipping, or note-dropping behavior.

### 8.8 Sequencer Notes and Dynamic Split Mapping

The splitter player must apply the same zone classification and transposition rules to notes originating from the sequencer as it does to notes played live on the keyboard.

- **Recording:** Notes must be recorded at their original, un-transposed pitches. The splitter must not modify the notes stored in the sequencer.
- **Playback:** When a sequencer note is played, the splitter evaluates its pitch against the current split point and determines which zone it belongs to. It then applies that zone's current octave transposition.
- **Dynamic configuration:** Zone classification and transposition are evaluated at playback time, using the current split point and zone settings. Changing the split point or either zone's transposition must therefore affect subsequent sequencer playback without requiring notes to be re-recorded.
- **Consistent behavior:** Live keyboard input and sequencer playback must follow the same mapping logic. The sequencer does not need to preserve the physical key position originally used to enter a note; the note's original pitch is sufficient to determine its zone relative to the current split.

The transformation must remain non-destructive: the original recorded notes are preserved, and the splitter applies its mapping only as notes pass through the player during playback.

## 9. Implementation approach

You are currently in the `open-xy-splitter` repository.

This player is to be implemented in the `machines/splitter-player` sub-directory, which only contains `machine.json`, `PLAN.md` (this file), `README.md`, and `splitter.svg` files.

This player should use the Open-XY SDK API located in `../open-xy`. Make sure you familiarize yourself with its API. Its documentation is found in `../open-xy/docs`.

The only existing player ever implemented using this SDK is the `chords` player. It is very important that you refer to its source code for this implementation. Its repository is found in `../open-xy-core-machines/machines/chords`, its documentation can be found in `../open-xy-core-machines/machines/chords/README.md`. Make sure to follow its conventions.

Before coding, inspect these above repositories to identify:

1. The registration mechanism for players.
2. The player interface, lifecycle, and parameter definition conventions.
3. How players receive physical keyboard note events.
4. How the OP-XY represents physical key positions separately from note pitches, if applicable.
5. How the current global keyboard octave is applied.
6. How note-on and note-off events are represented and processed.
7. How players transform notes without destructively modifying the underlying sequencer data.
8. How sequencer notes are passed through the player processing pipeline.
9. How encoder parameters are declared, updated, and displayed.
10. How player-specific graphics are rendered and updated.
11. How player configuration is serialized and restored.
12. How existing players handle polyphony and active-note life cycles.

Implement the new player by following existing abstractions and conventions.

Prefer reusing existing mechanisms over introducing new infrastructure.

Do not modify stock player behavior.

Do not introduce unrelated refactoring.

Do not invent API names, event types, drawing methods, or note-processing mechanisms. Derive these from the existing source code and document any architectural limitations discovered.

If the existing architecture does not expose the information needed to distinguish physical key position from note pitch, investigate the existing player behavior and determine how best to implement the split.

Pay particular attention to the distinction between live keyboard input and sequencer playback. Both must produce consistent results.

I repeat. Do not start implementation immediately. First inspect the SDK, its documentation, and the existing `chords` player. Report the relevant APIs, the available note-processing mechanisms, and any architectural limitations. In particular, establish how physical keyboard positions and sequencer notes are represented. Present a proposed implementation approach before modifying any files. Do not proceed with implementation until this investigation is complete.

### Building the player

From this `open-xy-splitter` repository, use `../.venv/bin/python ../open-xy/sdk.py build --overwrite --out "../firmware/dev/001" --stock-os ../firmware/1.2.1/os.ldr --machine ../open-xy-core-machines/machines/chords --machine ../open-xy-core-machines/machines/fm2op --machine machines/splitter-player` to build this player.

Note that `--machine ../open-xy-core-machines/machines/chords --machine ../open-xy-core-machines/machines/fm2op` are needed for now because of unrelated issues with the building process.

Once the custom firmware has been built successfully, I can push it to the OP-XY and test any functionality for you manually.

## 10. Acceptance criteria

The implementation is complete when all of the following are satisfied.

### Player registration

- [ ] A new player named `splitter` is available.
- [ ] Selecting it activates split behavior on the selected instrument track.

### Keyboard zones

- [ ] Exactly two zones are created.
- [ ] The default split is between physical keys 12 and 13.
- [ ] Encoder #2 adjusts the split point.
- [ ] The split point can be moved between keys 1/2 and 23/24, inclusive.
- [ ] Neither zone can become empty.
- [ ] All 23 physical boundaries are available, including boundaries involving black keys.
- [ ] The split remains associated with physical key positions when changing octaves.

### Transposition

- [ ] Encoder #1 adjusts Zone 1 octave transposition.
- [ ] Encoder #3 adjusts Zone 2 octave transposition.
- [ ] Both default to zero.
- [ ] Positive and negative octave transpositions work.
- [ ] Global octave changes affect both zones.
- [ ] Zone-specific transposition remains unchanged by global octave changes.
- [ ] The final pitch is the sum of the original pitch, global octave shift, and zone-specific octave shift.
- [ ] Changing one zone's transposition does not affect the other.

### Note processing

- [ ] Notes from Zone 1 receive Zone 1 transposition.
- [ ] Notes from Zone 2 receive Zone 2 transposition.
- [ ] The player operates exclusively on its assigned instrument track.
- [ ] No notes are routed to other instrument tracks.
- [ ] No other instrument engines are directly triggered.
- [ ] Both live keyboard input and sequencer notes are processed.
- [ ] Sequencer note data remains unmodified.
- [ ] Disabling the player restores normal note behavior.
- [ ] Note-off events correctly correspond to their original transformed note-on events.
- [ ] Changing parameters while notes are held does not cause stuck notes.
- [ ] Repeated, overlapping, and simultaneous notes are handled correctly.

### User interface

- [ ] The four encoder parameter slots appear at the top.
- [ ] Encoder #1 displays Zone 1 Transpose.
- [ ] Encoder #2 displays Split Point.
- [ ] Encoder #3 displays Zone 2 Transpose.
- [ ] Encoder #4 remains unused, following existing conventions.
- [ ] All three active parameters are available without holding Shift.
- [ ] Holding Shift does not change the meaning of the three active controls.
- [ ] The keyboard graphic represents the actual OP-XY keyboard based on the provided SVG, not a piano.
- [ ] All 24 physical keys are represented.
- [ ] Zone membership is visually distinguishable.
- [ ] The first key of Zone 2 is visually distinguishable on both white and black keys.
- [ ] The keyboard visualization updates immediately when the split point changes.
- [ ] The visualization remains fixed in physical-key space when changing octaves.

### Quality

- [ ] Player settings persist according to existing conventions.
- [ ] Appropriate tests cover zone assignment, pitch calculation, note processing, and note lifecycle.
- [ ] Tests cover both live keyboard input and sequencer playback if possible.
- [ ] Existing tests continue to pass.
- [ ] No unrelated functionality is modified.

## 11. Scope boundaries

The following features are explicitly excluded from this initial implementation:

- More than two zones.
- Independent semitone transposition (only octave transposition is required).
- Routing notes to different instrument tracks.
- Layering multiple instrument tracks within a zone.
- Directly triggering other instrument engines.
- Independent velocity curves or other per-zone expression processing.
- Configurable physical keyboard layouts.
- Additional Shift-modified parameters.

The implementation should remain small, focused, and consistent with the existing OP-XY player architecture.

The priority is a reliable two-zone live and sequenced note-mapping player with clear visual feedback and predictable note transformation.
