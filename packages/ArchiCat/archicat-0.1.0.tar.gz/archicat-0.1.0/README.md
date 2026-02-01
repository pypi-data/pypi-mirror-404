# ArchiCat - Text-based Scratch

ArchiCat is a text-based representation of the visual programming language [Scratch](https://scratch.mit.edu). This project features a transpiler that converts text- into .sb3-Files.
Its main purpose is simplifying the generation of .sb3-Files by computers.

## Installation

The installation of ArchiCat is really simple as it can be installed with `pip`, Python's built-in package manager. It requires Python >= 3.12.
`python3 -m pip install archicat`
(The Python command might vary depending on your OS)

## Example

```
sprite Cat {
    costume CatCostume = "./assets/CatCostume.svg"

    default {
        x = 0
        y = 0
    }

    WhenFlagClicked {
        SayForSecs("Hello!",2)
        Repeat(360,{
            TurnLeft(1)
        })
    }
}
```

## Limitations

ArchiCat does support all blocks included by default in Scratch, but does not support extensions yet. All other major features of Scratch are supported.