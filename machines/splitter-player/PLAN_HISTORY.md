# Plan history: Splitter Player

A chronological record of how the plan in [PLAN.md](PLAN.md) changed from the
original specification. `PLAN.md` says what we are building now; this file says why
it differs.

**About the dates.** The work below happened on 2026-11-08, except the confirmations dated 2026-11-09. The repository's
first commit (`44db806`, 18:02 local) holds the original specification, and the
implementation commit (`f44ee3d`, 22:35 local) holds the first working player. The
entries are in the order the topics came up. Where the clock time or the exact origin
is not evidenced, this file says so.

**Approval labels.** Each entry says who decided:

- **Explicit decision**: the project owner chose it in discussion.
- **Constraint**: forced by an SDK or OP-XY limit found while investigating.
- **Implementation choice**: made while coding; it was reported but not explicitly confirmed.
- **Proposal**: not approved, or deferred.

## H-01 Baseline: the original specification

- **Date:** 2026-11-08, first commit `44db806`. The verbatim original is
  `machines/splitter-player/PLAN.md` at that commit (`git show 44db806:machines/splitter-player/PLAN.md`).
- **Original requirement.** In summary:
  - Two zones over the 24 keys, split by encoder 2 (`splitAtKey` 2 to 24, default 13), with octave transposition -4 to +4
    per zone on encoders 1 and 3 (captions `tr1`, `tr2`, split caption `pos`; the split value shown with its note, e.g. `13 (F)`); encoder 4 unused.
  - Zones decided from the physical key position, also for sequencer notes ("do not assume that physical key positions can
    always be reconstructed from MIDI pitches"), with section 8.8 saying the note's pitch is sufficient to find its zone.
  - Note-offs must follow the transformed note-ons, with no stuck notes when settings change.
  - On screen: the stock player header on top and the OP-XY key picture from `splitter.svg` below. Boxes `r1` to `r24` are
    filled #323232 (zone 1) or #969696 (zone 2); the ellipse of the first zone 2 key is filled #646464.
  - Pitch outside the supported range handled "following existing OP-XY player conventions", without undocumented wrapping,
    clipping or dropping.
  - The machine is named `splitter`.
  - Section 9 required inspecting the SDK and the `chords` player first, reporting the findings and a proposed approach, and
    not implementing until that was done.
- **Discovery or constraint.** None yet; this is the baseline.
- **Adjustment.** None.
- **Rationale.** Starting point.
- **Consequences.** The investigation-first instruction was followed: the SDK and `chords`
  were inspected and a report with a proposed approach was presented before any file
  was written. The visual approach was then discussed (H-09, H-10).

## H-02 Physical key position and sequenced notes

- **Date:** 2026-11-08, during the initial SDK investigation. Type: **constraint**.
- **Original requirement.** Section 2.3 asks that zones follow the physical key position, and warns not to assume it can
  always be reconstructed from the MIDI pitch. Section 8.8 says the note's original pitch is sufficient for sequenced notes.
- **Discovery or constraint.** The SDK delivers a pitch only, and no key identity. `Controls::lowest_key` is the pitch the
  lowest key plays at the track's current octave, so position is `note - lowest_key` (`opxy/player.hpp`). Sequenced notes keep
  the pitch they were recorded with, so their position follows the octave at playback (the header's own words).
- **Adjustment.** Position is computed as `note - lowest_key`, for live and sequenced notes alike. The split is a line through all
  pitches: any position below the split is zone 1 and any position at or above it is zone 2, however far outside the 24 keys of the
  current octave. Nothing is clamped or moved.
- **Rationale.** It is the only source of position the SDK exposes, and it matches the `chords` player and section 8.8.
- **Consequences.** The split follows the keyboard octave for live notes. A sequenced note recorded at one octave and played at
  another can land in a different zone. The project owner confirmed this is the intended behavior (2026-11-08, after the first
  version of `PLAN.md`). A sequenced note that falls beyond the 24 keys at the current octave is assigned to a zone by the same
  line, and its zone's transposition applies. This was first an **implementation choice**. The owner confirmed it on 2026-11-09
  as the intended behavior, after asking what "clamping" meant: nothing is clamped, the split is a line through all pitches.
  Sequenced playback was reported working on the device.

## H-03 Meaning of the final-pitch formula

- **Date:** 2026-11-08, during the initial investigation. Type: **constraint**, no change of behavior.
- **Original requirement.** `finalPitch = originalPitch + 12 * globalOctave + 12 * zoneOctaveTranspose` (section 5.3).
- **Discovery or constraint.** A live note arrives with the keyboard octave already added.
- **Adjustment.** The player computes `note + 12 * zoneOctaves`, which equals the formula when `originalPitch` is the pitch at octave 0.
- **Rationale.** Adding the octave again would shift notes twice.
- **Consequences.** None for the user. The intended behavior is unchanged.

## H-04 Pitch outside the supported range

- **Date:** 2026-11-08, initial investigation; confirmed by the owner later the same day. Type: **implementation choice**, then
  **explicit decision**.
- **Original requirement.** Section 5.3 and 8.7: follow the existing player conventions, with no undocumented wrapping, clipping or dropping.
- **Discovery or constraint.** The only existing player, `chords`, omits tones outside MIDI 0 to 127 and documents it in its README. An empty plan makes the SDK swallow the note.
- **Adjustment.** Notes whose final pitch is outside 0 to 127 are not played. Nothing is clamped or wrapped.
- **Rationale.** It follows `chords`' documented convention.
- **Consequences.** At large transpositions many notes are silent. The report said this explicitly. The project owner confirmed it
  later on 2026-11-08, confirming that dropping notes outside 0 to 127 as `chords` does is intended.

## H-05 Note-off bookkeeping

- **Date:** 2026-11-08, initial investigation. Type: **constraint**, no change of behavior.
- **Original requirement.** Section 8.3 and 8.4: note-offs follow the transformed note-ons, with whatever bookkeeping is needed.
- **Discovery or constraint.** The SDK stores one record per root note, holding the tones played for it, and releases those
  tones when that root is released. A player's `release` returning `false` hands it to the stock player.
- **Adjustment.** The player keeps no bookkeeping and `release` returns `false`.
- **Rationale.** The SDK already gives the required behavior.
- **Consequences.** A setting changed while a key is held cannot strand a note.

## H-06 State and persistence

- **Date:** 2026-11-08, initial investigation. Type: **constraint**.
- **Original requirement.** Section 7: keep `splitAtKey`, `zone1Transpose` and `zone2Transpose` as logical state, persisted by the existing conventions.
- **Discovery or constraint.** Player `State` starts zeroed and holds no settings. Encoder values reach the player as `Controls` and
  are saved as stock player parameters.
- **Adjustment.** The three values are the choices of encoders 1, 2 and 3, with defaults in `definition.json`. `State` is empty.
- **Rationale.** It is the SDK's persistence mechanism.
- **Consequences.** Settings are saved with the project. The split is stored as an encoder choice (2 to 24).

## H-07 The header comes from the SDK

- **Date:** 2026-11-08, initial investigation. Type: **constraint**.
- **Original requirement.** Section 6.2 maps the parameters to SVG elements `param1` to `param3` and `value1` to `value3`.
- **Discovery or constraint.** The player page keeps the stock header. Captions come from the `definition.json` labels (at most 8
  characters) and values from `Display.values` (at most 7 characters). The design file's `param_bar` is not used.
- **Adjustment.** The page artwork contains the keyboard only, and the header text is supplied through the definition and `display()`.
- **Rationale.** It is the only way the SDK draws the header.
- **Consequences.** No change to what the user sees, apart from H-08 and H-12.

## H-08 The split value no longer shows its note

- **Date:** 2026-11-08, after the first device test. Type: **explicit decision**.
- **Original requirement.** The `pos` value shows `splitAtKey` with its note in parentheses, for example `13 (F)`.
- **Discovery or constraint.** The longest value, `14 (F#)`, is 7 characters and was too wide for its header slot on the device.
- **Adjustment.** Show only the key number (`2` to `24`).
- **Rationale.** Fit. The note name was removed rather than the caption changed.
- **Consequences.** The note name is gone, and the `kNoteNames` table was removed from the code.

## H-09 Zone shading through pre-drawn overlays

- **Date:** 2026-11-08, shortly after the initial investigation. Type: **constraint**, then **explicit decision**.
- **Original requirement.** Change the `fill` of the key boxes to #323232 (zone 1) or #969696 (zone 2) as the split moves.
- **Discovery or constraint.** A player page can only show or hide up to 24 pre-drawn shapes (`display_dots = 24`, a 32-bit `lit` mask).
  It cannot change a shape's color. Synth pages can recolor through a palette, but the player page does not use that contract. The
  limit comes from the SDK, which was designed around the `chords` page, not from the OP-XY.
- **Adjustment.** `artwork.py` draws all keys in zone 2's color, plus 23 zone 1 overlays (one per split); the player shows one.
  This was proposed with a fallback and accepted in this form: draw the entire keyboard in zone 2's color, pre-draw every possible
  split position in zone 1's color, and overlay the right one at run time. The generator script builds them from `designs/splitter.svg`.
- **Rationale.** It gives the specified two-color split with the 24-dot limit.
- **Consequences.** Zone colors are as specified. The overlays are confirmed to look right on the device. A recoloring API for players
  was not pursued; an SDK change was not requested.

## H-10 The split marker is dropped

- **Date:** 2026-11-08, same discussion as H-09. Type: **explicit decision**.
- **Original requirement.** The ellipse of the first zone 2 key is filled #646464.
- **Discovery or constraint.** With only show/hide shapes, a marker in a third color needs about twice as many shapes as are allowed.
  The proposed fallback was a marker in zone 1's color (#323232).
- **Adjustment.** The project owner rejected that ("I don't want zone 1 and the dot to be the same color, therefore we are abandoning the
  dot itself"), so no marker is drawn.
- **Rationale.** A marker the same color as zone 1 was not wanted, and the exact color was not possible.
- **Consequences.** The first zone 2 key is recognized by the boundary of the shading only. The acceptance criterion about
  distinguishing it on white and black keys is changed accordingly. It still needs a device check.

## H-11 Strokes, pixel alignment and key pads

- **Date:** 2026-11-08, after viewing the overlays on the device. Type: **explicit decision**, with **implementation choices** inside it.
- **Original requirement.** Keep the `stroke` of the design unchanged (#101010, 0.5 px). Pads are ellipses.
- **Discovery or constraint.** Some line segments looked thicker than others. The cause is fractional coordinates, so strokes straddle
  pixel rows, and edges drawn up to three times accumulate coverage.
- **Adjustment.** The project owner set the stroke to #000000 at 1.0 px (`STROKE_WIDTH`, `EDGE` in `artwork.py`). The script now snaps box
  edges and pad centres to pixel centres, uses square corners, and draws pads as circles of radius 10. After the ellipses still
  looked soft, the owner decided the pads are filled in #000000.
- **Rationale.** Sharper, more uniform lines on the 480 by 220 display.
- **Consequences.** Key widths are 31 or 32 px instead of 31.7 px. The pads are filled black discs. The design file is not modified.
  The SVG was moved by the owner to `designs/splitter.svg`.

## H-12 Parameter captions and ids

- **Date:** 2026-11-08. The exact time is not recorded. Type: **explicit decision**.
- **Original requirement.** Captions `tr1`, `pos`, `tr2`.
- **Discovery or constraint.** None; a naming decision.
- **Adjustment.** The owner renamed the ids to `zone1_transpose`, `split_point_position` and `zone2_transpose`, and the captions to
  `z1tr` and `z2tr`. `pos` is unchanged.
- **Rationale.** Clearer names. The owner did not give a more specific reason.
- **Consequences.** None for behavior.

## H-13 Encoder 4 as a truly absent slot

- **Date:** 2026-11-08. Type: **constraint**, then **explicit decision**.
- **Original requirement.** Encoder 4 is "unused for now" and remains unused following existing conventions.
- **Discovery or constraint.** The SDK let only a synth leave a slot absent, and a player's ordinary parameter needs a label of 1 to 8
  characters. The first build therefore declared encoder 4 as a placeholder `none` off/on enum, which showed a distracting caption. Two
  smaller problems also appeared: the header's initial `0` stayed under an empty value, and turning the slot still edited a stored value.
- **Adjustment.** The owner decided this was an SDK bug and asked for a fix: issue #475 and PR #476, which allow an `absent` slot for players, make
  turns on it do nothing, and clear the initial value. The merged change was verified by unit tests and the SDK check. The definition now declares `unused` as
  an absent slot.
- **Rationale.** It meets the requirement that encoder 4 is unused, without a placeholder.
- **Consequences.** The player needs an SDK that includes PR #476. `machine.json` keeps `"sdk": "1.8"` with no version bump; the owner
  confirmed this is fine. The owner confirmed on 2026-11-08, after the merge, that encoder 4 is hidden correctly on the device.

## H-14 Machine id `splitter_player` and the menu name

- **Date:** 2026-11-08. Type: **explicit decision**, then **constraint**, parked.
- **Original requirement.** The player is registered as `splitter`.
- **Discovery or constraint.** The owner renamed the id to `splitter_player` so a later `splitter_aux` can exist (the SDK requires unique ids; the
  display `name` is not documented as unique). The player menu on the device then showed `splitter_play`: the menu lists the `id`,
  not the `name`, and shows about 13 characters. `splitter_player` has 15.
- **Adjustment.** An optional `menuName` field in `definition.json` was proposed, which would need an SDK change and a hook that draws it in every
  chooser. The owner deferred it ("this seems like a lot, we will cross that bridge later"). The other option, a shorter id, was not chosen.
- **Rationale.** Keep the id pair clear; defer a large SDK change.
- **Consequences.** The menu shows a truncated name for now. The owner decided on 2026-11-08 that this is fine for now, and that a
  `menuName` idea will be reconsidered later with the SDK maintainer. It stays an open item in `PLAN.md`, parked.

## H-15 Setting the split by pressing a key (new idea, deferred)

- **Date:** 2026-11-08. Type: **proposal**, not adopted. Not in the original specification.
- **Original requirement.** Encoder 2 sets the split. Nothing else does.
- **Discovery or constraint.** The owner asked for the split to be settable by pressing a key, either with Shift plus a key or after a click of
  encoder 2. Neither is possible with the SDK: a player's `press` gets only the note and velocity, and the SDK delivers no Shift state or
  encoder click to a player. Also a player cannot change a parameter.
- **Adjustment.** An alternative was proposed and then implemented as a prototype on a local SDK branch: a `learn` off/on setting on
  encoder 4. While it is on, the next key sets the split and turns learn off. It needed a new SDK callback, `edit`, that the GUI applies through
  stock's parameter setter. The prototype's tests and the SDK check passed. The owner then decided it was too extensive to do without the SDK
  maintainer, and asked for both repositories to be reverted. The branch was deleted and never pushed.
- **Rationale.** The change reaches into the SDK's platform layer, which the maintainer should review.
- **Consequences.** Encoder 2 remains the only way to set the split. Design notes for later: an optional `edit(State&, Controls&, Edit&)` callback
  drained like `update`, queued to the GUI and applied once per frame to the selected track only; a `choice_value()` helper; a `learn` parameter
  on encoder 4 (default off); a sequenced note would also set the split while learn is on, because a note callback cannot tell it from a key.

## H-16 SDK test portability (not a change to the plan)

- **Date:** 2026-11-08. Type: **constraint**, background.
- **Discovery or constraint.** `sdk.py check` failed on macOS with Python 3.14 (39 failures, 26 errors), because of macOS's symlinked temporary
  directory, a Python 3.14 behavior in one test, and a Mach-O symbol naming difference. The test code was fixed (issue #477, PR #478, merged).
- **Consequences.** None for this player. It is recorded so a contributor knows why `sdk.py check` now passes on macOS.

## H-17 Shift does not change the controls (confirmation)

- **Date:** 2026-11-08, after the first version of `PLAN.md`. Type: **explicit decision** (a confirmation of the original requirement).
- **Original requirement.** Section 6.4: holding Shift must not change the meaning of the three active encoders, and no Shift
  parameters exist.
- **Discovery or constraint.** The first version of `PLAN.md` listed this as unchecked, because the SDK's turn handler for players
  applies detents with no Shift-dependent meaning, and nobody had looked at the header while Shift is held.
- **Adjustment.** None. The owner confirmed that holding Shift changes nothing.
- **Rationale.** Not applicable.
- **Consequences.** The requirement is met and the acceptance item is closed.

## H-18 Device confirmation of the remaining acceptance items

- **Date:** 2026-11-09. Type: **explicit decision** (confirmations; no change to the plan).
- **Original requirement.** The acceptance criteria of the original plan (section 10).
- **Discovery or constraint.** After `PLAN.md` was rewritten, several items were still marked open only because no device result had
  been reported. They were not known to fail.
- **Adjustment.** None to the requirements. The owner confirmed on the device: encoder 2 moves the split live; encoders 1 and 3
  set the zone transpositions; disabling the player restores normal note behavior; repeated and overlapping notes work; and the
  first zone 2 key is visually distinguishable on both white and black keys (by the boundary of the shading, H-10).
- **Rationale.** Not applicable.
- **Consequences.** The acceptance items are ticked in `PLAN.md`. Release and catalog steps are the only open item.

## H-19 The player builds on its own

- **Date:** 2026-11-09. Type: **constraint**, then **explicit decision**.
- **Original requirement.** Section 9 of the original plan gave a build command that also builds `chords` and `fm2op`, "needed for now
  because of unrelated issues with the building process". The cause was not known.
- **Discovery or constraint.** A collection of players alone failed to compile the SDK's generated `startup.cpp` under `-Wall -Werror`:
  its id helper `value()` is called only by rows for engines, effect pages and sample screens, so with none it was reported unused.
  Adding any engine, such as `fm2op`, made it compile. This was an SDK bug (issue #480), not a property of this player.
- **Adjustment.** The owner asked for the cause to be found and fixed. PR #481 marks the helper unused and adds a regression test; it was
  merged. `PLAN.md` and `README.md` now build with `--machine machines/splitter-player` alone. A build with the player alone succeeded on
  `staging`.
- **Rationale.** The extra machines were a workaround for an SDK defect.
- **Consequences.** The build command is shorter. Building without `chords` removed its entry from the build's `layout.json`, so add it back with
  `--machine` if a device should keep that player. The cause of that entry's removal was not investigated.
