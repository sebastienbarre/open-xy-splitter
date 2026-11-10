#include <opxy/player.hpp>

// Splitter player.
//
// The OP-XY's 24-key keyboard is divided into two zones, each with its own
// octave transposition:
//   zone 1: keys 1 .. split - 1     zone 2: keys split .. 24
// where key 1 is the lowest (left-most) key and "split" is the number of the
// first key of zone 2, from 2 to 24.
//
// Encoders:
//   1  zone 1 transposition, -4 .. +4 octaves for example
//   2  split point position: the number of the first key of zone 2, 2 .. 24
//   3  zone 2 transposition, -4 .. +4 octaves for example
//   4  unused
//
// A key is identified by its position, the note minus the keyboard's lowest
// key (`Controls::lowest_key`). Because `lowest_key` follows the track's
// keyboard octave, the split stays on the same physical keys whatever the
// octave. A live note already carries the keyboard octave, so the pitch played
// is the note plus 12 per octave of its zone's transposition.
//
// A sequenced note keeps the pitch it was recorded with and is placed against
// the keyboard octave at playback. Notes below key 1 fall in zone 1 and notes
// above key 24 in zone 2.
//
// A transposed note outside MIDI 0..127 is not played; it is never clamped or
// wrapped, as in the chords player.
//
// The player keeps no state. Its settings live in the four encoders, which the
// SDK saves with the project. A release is left to the stock player, which
// releases the tone played for the note that was pressed, so changing a
// setting while a key is held cannot leave a note sounding.
namespace splitter_player {
using opxy::u8;
using opxy::u32;
using opxy::i32;
using opxy::player::Controls;
using opxy::player::Display;
using opxy::player::Plan;

// The SDK requires a State type even when a player has nothing to remember.
struct State {};

namespace {
// Number of physical keys on the keyboard.
const u32 kKeysCount = 24;

// Number of the first possible key of zone 2 when encoder 2 is fully counter-clockwise.
// Key 1 can never start zone 2, or zone 1 would be empty.
const u32 kMinSplitPosition = 2;

// Number of positions the split can take, key 2 to key 24, so each zone keeps
// at least one key.
const u32 kSplitPositionsCount = kKeysCount - kMinSplitPosition + 1;

// Smallest transposition in octaves. Do make sure to keep in sync w/ enums in definition.json
const i32 kMinOctaves = -4;

// Largest transposition in octaves. Do make sure to keep in sync w/ enums in definition.json
const i32 kMaxOctaves = 4;

// Number of choices of a transposition encoder: kMinOctaves .. kMaxOctaves octaves (say, -4 .. +4).
const u32 kTranspositionsCount = kMaxOctaves - kMinOctaves + 1;

// Index of the encoder for zone 1's transposition (the SDK numbers them from 0).
const u32 kZone1TranspositionEncoder = 0;

// Index of the encoder for the split.
const u32 kSplitPositionEncoder = 1;

// Index of the encoder for zone 2's transposition.
const u32 kZone2TranspositionEncoder = 2;

// Converts an encoder's Q31 value into the number of the choice it selects.
//   value  the encoder's value, 0 .. 0x7fffffff; a negative value counts as 0
//   count  the number of choices, at most 65536
// Returns the choice, 0 .. count - 1. An enum parameter stores the centre of
// its choice, so this returns exactly the choice the user selected.
u32 steps(i32 value, u32 count) {
    const u32 v = value < 0 ? 0u : static_cast<u32>(value) >> 16;
    const u32 step = (v * count) >> 15;
    return step < count ? step : count - 1;
}

// Reads a zone's transposition from its encoder.
//   controls  the player's four encoders
//   zone      0 for zone 1, 1 for zone 2
// Returns the transposition in octaves, kMinOctaves .. kMaxOctaves.
i32 octaves(const Controls& controls, u32 zone) {
    const u32 encoder = zone == 0 ? kZone1TranspositionEncoder : kZone2TranspositionEncoder;
    return static_cast<i32>(steps(controls.value[encoder], kTranspositionsCount)) + kMinOctaves;
}

// Reads the split from its encoder.
//   controls  the player's four encoders
// Returns the number of the first key of zone 2, kMinSplitPosition .. kKeysCount.
u32 split_key(const Controls& controls) {
    return kMinSplitPosition + steps(controls.value[kSplitPositionEncoder], kSplitPositionsCount);
}

// Appends text to a string, dropping what does not fit.
//   out     the string; terminated on return
//   length  the number of characters already in `out`; updated
//   size    the capacity of `out`, including its terminator
//   s       the text to append
void append(char* out, u32& length, u32 size, const char* s) {
    while (*s && length + 1 < size) out[length++] = *s++;
    out[length] = 0;
}

// Appends a number in decimal, dropping the digits that do not fit.
//   out, length, size  as for the text overload
//   n                  the number to append
void append(char* out, u32& length, u32 size, u32 n) {
    char digits[10];
    u32 count = 0;
    do { digits[count++] = static_cast<char>('0' + n % 10); n /= 10; } while (n);
    while (count) { const char c[2] = {digits[--count], 0}; append(out, length, size, c); }
}

// Note names from C, for MIDI note 0 = C-1, so MIDI note 53 = F3 at the keyboard's default octave.
const char* const kNoteNames[12] = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

// Appends a note's name and octave, such as "F3" or "C#-1".
//   out, length, size  as for the text overload
//   note               the MIDI note, 0 .. 127
void append_note(char* out, u32& length, u32 size, u32 note) {
    append(out, length, size, kNoteNames[note % 12]);
    const i32 octave = static_cast<i32>(note / 12) - 1;
    if (octave < 0) append(out, length, size, "-");
    append(out, length, size, static_cast<u32>(octave < 0 ? -octave : octave));
}

// Appends the notes a zone's keys play, such as "F3..E4", clamped to MIDI 0 .. 127.
//   out, length, size  as for the text overload
//   controls           the player's four encoders and the keyboard's lowest key
//   zone               0 for zone 1, 1 for zone 2
// Appends "-" when the whole zone falls outside MIDI 0 .. 127, so it is silent.
void append_range(char* out, u32& length, u32 size, const Controls& controls, u32 zone) {
    const i32 split = static_cast<i32>(split_key(controls));
    const i32 lowest = static_cast<i32>(controls.lowest_key);
    const i32 first = zone == 0 ? lowest : lowest + split - 1;
    const i32 last = zone == 0 ? lowest + split - 2 : lowest + static_cast<i32>(kKeysCount) - 1;
    const i32 shift = 12 * octaves(controls, zone);
    const i32 low = first + shift < 0 ? 0 : first + shift;
    const i32 high = last + shift > 127 ? 127 : last + shift;
    if (low > high) {
        append(out, length, size, "-");
        return;
    }
    append_note(out, length, size, static_cast<u32>(low));
    append(out, length, size, "..");
    append_note(out, length, size, static_cast<u32>(high));
}
}

// Plays a pressed key, live or sequenced, in the zone it belongs to.
//   state     unused
//   controls  the encoders and the keyboard's lowest key
//   note      the pressed note, MIDI 0..127
//   velocity  its velocity, 0..127
//   plan      receives the tone to play; its count is 0 when nothing sounds
// Returns true: the player always takes the note, so the instrument never
// plays it unchanged. A note whose transposition leaves MIDI 0..127 is taken
// and left silent.
bool press(State&, const Controls& controls, u32 note, u32 velocity, Plan& plan) {
    plan.count = 0;
    if (note > 127 || velocity > 127) return true;
    const i32 position = static_cast<i32>(note) - static_cast<i32>(controls.lowest_key);
    // Position 0 is key 1, so key `split` is at position split - 1.
    const bool upper = position >= static_cast<i32>(split_key(controls)) - 1;
    const i32 pitch = static_cast<i32>(note) + 12 * octaves(controls, upper ? 1 : 0);
    if (pitch < 0 || pitch > 127) return true;
    plan.count = 1;
    plan.tones[0].pitch = static_cast<u8>(pitch);
    plan.tones[0].velocity = static_cast<u8>(velocity);
    plan.tones[0].delay = 0;
    return true;
}

// Ends a pressed key.
//   state  unused
//   note   the released note, unused
// Returns false: no key is held silently, so the stock player releases the
// tone it played for this note.
bool release(State&, u32) { return false; }

// Fills the page: the three encoder values and the zone 1 overlay to show.
//   state     unused
//   controls  the encoders
//   display   receives the page
// `display.lit` has one bit set: dot k is the zone 1 overlay for a split at
// key k + 2 (keys 1 .. k + 1), drawn over the zone 2 keyboard. The values are
// the two transpositions, such as "+0", and the split's key number. The text is
// the notes each zone plays, after transposition and clamped to MIDI 0 .. 127.
void display(const State&, const Controls& controls, Display& display) {
    // zone 1 overlay
    const u32 key = split_key(controls);
    display.lit = 1u << (key - kMinSplitPosition);

    // zone 1 and zone 2 transposition values
    for (u32 zone = 0; zone < 2; ++zone) {
        char* out = display.values[zone == 0 ? kZone1TranspositionEncoder : kZone2TranspositionEncoder];
        const i32 n = octaves(controls, zone);
        u32 length = 0;
        out[0] = 0;
        append(out, length, sizeof(display.values[0]), n < 0 ? "-" : "+");
        append(out, length, sizeof(display.values[0]), static_cast<u32>(n < 0 ? -n : n));
    }

    // split position
    char* out = display.values[kSplitPositionEncoder];
    u32 length = 0;
    out[0] = 0;
    append(out, length, sizeof(display.values[kSplitPositionEncoder]), key);

    // encoder 4 is not used
    display.values[3][0] = 0;

    // Use the player API-provided text caption to display both zones' notes, such as "F3..E4 | F4..E5"
    length = 0;
    display.text[0] = 0;
    append_range(display.text, length, sizeof(display.text), controls, 0);
    append(display.text, length, sizeof(display.text), " | ");
    append_range(display.text, length, sizeof(display.text), controls, 1);
}
}
