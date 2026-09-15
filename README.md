```text
     ██████╗  █████╗  ██████╗ ██╗   ██╗███████╗
     ██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝
     ██████╔╝███████║██║  ███╗██║   ██║███████╗
     ██╔══██╗██╔══██║██║   ██║██║   ██║╚════██║
     ██████╔╝██║  ██║╚██████╔╝╚██████╔╝███████║
     ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝

             B A G U S  :  F I N E - F M

        Basically A Generally Useless Solver
     Fluid Idiot's Numerical Engine for Fluid Mechanics

                    ~ water.exe ~

        +--------------------------------------+
        |              BLOON STACK             |
        |                                      |
        |   FINE-FM                            |
        |      │                               |
        |      ▼                               |
        |    BLOON                             |
        |      │                               |
        |      ▼                               |
        |  BLOON_MACHINE                       |
        +--------------------------------------+

                    __________
                   /          \
                  /  ~~~~~~~~  \
                 |  ~~~~~~~~~~ |
                 |  ~~~~~~~~~~ |
                 |  ~~~~~~~~~~ |
                 |_____________|

          The wrapper is a joke.
          The numbers are expected to be correct.

          Fluid statics. Six problems.
          One bucket. Zero excuses.
```

BAGUS: FINE-FM is the fluid-statics companion demo for the BLOON stack.

Supported problems:

1. Hydrostatic pressure — `P = P0 + rho*g*h`
2. Pressure difference — `dP = rho*g*dh`
3. Pascal hydraulic — `F2 = F1*A2/A1`
4. Buoyancy — `FB = rho_f*g*V`
5. Hydrostatic surface force — `F = integral(p dA)`
6. Water in a bucket — deliberately trivial, deliberately included

FINE-FM keeps the domain layer separate from numerical evaluation and uses `NumericBackend` as the numerical seam. The intended stack is FINE-FM -> BLOON -> BLOON_MACHINE.

## Run

```bash
python examples/run_fine_fm.py --all
python examples/run_fine_fm.py
python examples/run_fine_fm.py --bucket
python examples/main.py
```

## Test

```bash
python -m pytest tests -v
```

Pygame is the visual companion. Python remains the engine. Water remains suspiciously wet.
