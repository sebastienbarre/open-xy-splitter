# Open-XY machines

Machines build on the Open-XY SDK, for the OP-XY on OS 1.2.1. They are built with the
[Open-XY SDK](https://github.com/etcetc000/open-xy) and reach the [builder](https://open-xy.com)
through its catalog, which pins a tagged commit of this repository.

| Machine | Kind | What it shows |
| --- | --- | --- |
| [Splitter Player](machines/splitter-player) | Player | A player that allows the user to split the OP-XY keyboard into two zones that can be assigned different octave transpositions. Non-destructive, doesn't record, only maps keys to notes. |
| [Splitter Aux](machines/splitter-aux) | Aux | An Aux machine that allows the user to split the OP-XY keyboard into two zones that can be assigned different instrument tracks and octave transpositions. Can record mapped notes. NOT IMPLEMENTED. |

Each folder is one machine: `machine.json` (kind, SDK version and the numbers it
prefers), `definition.json` (controls), its C++ and, for a synth, its artwork.
Some have their own sound tests in `tests/`.

## Checks

Clone the SDK next to this repository, then from here:

```sh
python ../open-xy/sdk.py test --machine machines/splitter-player
```

## Licences

MIT ([LICENSE](LICENSE)), except vendored code under its own terms, if any.
