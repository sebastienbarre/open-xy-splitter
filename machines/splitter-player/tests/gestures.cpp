#include "../player.cpp"
#include <cstdio>
#include <cstdlib>
#include <string>
#define require(x) do { if (!(x)) { std::fprintf(stderr, "line %d: %s\n", __LINE__, #x); std::abort(); } } while (0)
using namespace opxy;
using namespace opxy::player;
namespace {
const u32 F3 = 53;  // the keyboard's lowest key at octave 0

i32 choice(u32 index, u32 count) { return static_cast<i32>((static_cast<double>(index) + 0.5) / count * 2147483647.0); }
i32 transpose(i32 octaves) { return choice(static_cast<u32>(octaves + 4), 9); }
i32 split(u32 key) { return choice(key - 2, 23); }

struct Rig {
    splitter_player::State state = {};
    Controls controls = {{transpose(0), split(13), transpose(0), 0}, F3};
    Plan plan = {};
    void on(u32 note, u32 velocity = 90) { require(splitter_player::press(state, controls, note, velocity, plan)); }
    bool off(u32 note) { return splitter_player::release(state, note); }
    void one(u32 pitch, u32 velocity = 90) {
        require(plan.count == 1 && plan.tones[0].pitch == pitch && plan.tones[0].velocity == velocity &&
                plan.tones[0].delay == 0);
    }
};

void defaults() {
    Rig r;
    for (u32 key = 1; key <= 24; ++key) { r.on(F3 + key - 1); r.one(F3 + key - 1); }
}

void zones_at_every_split() {
    for (u32 s = 2; s <= 24; ++s) {
        Rig r;
        r.controls.value[1] = split(s);
        r.controls.value[0] = transpose(-1);
        r.controls.value[2] = transpose(2);
        for (u32 key = 1; key <= 24; ++key) {
            r.on(F3 + key - 1);
            r.one(key < s ? F3 + key - 1 - 12 : F3 + key - 1 + 24);
        }
    }
}

void transposition_is_independent() {
    Rig r;
    r.controls.value[0] = transpose(3);
    r.on(F3); r.one(F3 + 36);
    r.on(F3 + 12); r.one(F3 + 12);
    r.controls.value[0] = transpose(0);
    r.controls.value[2] = transpose(-4);
    r.on(F3); r.one(F3);
    r.on(F3 + 12); r.one(F3 + 12 - 48);
}

void keyboard_octave_moves_pitch_not_the_split() {
    for (int octave = -3; octave <= 3; ++octave) {
        Rig r;
        r.controls.lowest_key = F3 + 12 * octave;
        r.controls.value[2] = transpose(-1);
        r.on(r.controls.lowest_key + 11); r.one(r.controls.lowest_key + 11);
        r.on(r.controls.lowest_key + 12); r.one(r.controls.lowest_key);
    }
}

void sequenced_notes() {
    Rig r;
    r.controls.value[0] = transpose(1);
    r.controls.value[2] = transpose(-1);
    r.on(F3 - 5); r.one(F3 - 5 + 12);   // below the keyboard: zone 1
    r.on(F3 + 40); r.one(F3 + 40 - 12); // above it: zone 2
    // The split read at playback moves a recorded note between zones.
    r.on(F3 + 6); r.one(F3 + 6 + 12);
    r.controls.value[1] = split(5);
    r.on(F3 + 6); r.one(F3 + 6 - 12);
}

void pitch_limits() {
    Rig r;
    r.controls.value[0] = transpose(-4);
    r.on(40); require(r.plan.count == 0);
    r.controls.value[0] = transpose(4);
    r.controls.lowest_key = 113;
    r.on(120); require(r.plan.count == 0);
    r.controls.lowest_key = F3;
    r.controls.value[2] = transpose(4);
    r.on(79); r.one(127);
    r.on(80); require(r.plan.count == 0);
    r.on(128); require(r.plan.count == 0);
    r.on(60, 128); require(r.plan.count == 0);
}

void note_lifecycle() {
    Rig r;
    r.on(F3); r.one(F3);
    require(!r.off(F3));
    // A release carries the key's own note, so parameter changes cannot strand it.
    r.on(F3 + 12); r.one(F3 + 12);
    r.controls.value[2] = transpose(-2);
    r.controls.value[1] = split(2);
    require(!r.off(F3 + 12));
    r.on(F3 + 12); r.one(F3 + 12 - 24);
    r.on(F3 + 12, 40); r.one(F3 + 12 - 24, 40);
    r.on(F3); r.one(F3);
}

void display_page() {
    Rig r;
    Display shown = {};
    splitter_player::display(r.state, r.controls, shown);
    require(shown.lit == 1u << 11 && std::string(shown.text).empty());
    require(std::string(shown.values[0]) == "+0" && std::string(shown.values[1]) == "13" &&
            std::string(shown.values[2]) == "+0" && std::string(shown.values[3]).empty());
    r.controls.value[0] = transpose(-4);
    r.controls.value[1] = split(2);
    r.controls.value[2] = transpose(4);
    splitter_player::display(r.state, r.controls, shown);
    require(shown.lit == 1u && std::string(shown.values[0]) == "-4" && std::string(shown.values[1]) == "2" &&
            std::string(shown.values[2]) == "+4");
    r.controls.value[1] = split(24);
    splitter_player::display(r.state, r.controls, shown);
    require(shown.lit == 1u << 22 && std::string(shown.values[1]) == "24");
    for (u32 s = 2; s <= 24; ++s) {
        r.controls.value[1] = split(s);
        splitter_player::display(r.state, r.controls, shown);
        require(shown.lit == 1u << (s - 2));
        require(std::string(shown.values[1]) == std::to_string(s));
    }
}

void controls_extremes() {
    Rig r;
    r.controls.value[1] = 0;
    r.controls.value[2] = transpose(-1);
    r.on(F3); r.one(F3);
    r.on(F3 + 1); r.one(F3 + 1 - 12);  // split at key 2: key 2 is zone 2
    r.controls.value[1] = 0x7fffffff;
    r.controls.value[0] = transpose(1);
    r.on(F3 + 22); r.one(F3 + 22 + 12);  // split at key 24: key 23 is zone 1
}
}

int main() {
    defaults();
    zones_at_every_split();
    transposition_is_independent();
    keyboard_octave_moves_pitch_not_the_split();
    sequenced_notes();
    pitch_limits();
    note_lifecycle();
    display_page();
    controls_extremes();
    std::puts("ok");
}
