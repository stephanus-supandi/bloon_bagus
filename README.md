```text
  ____    _    ____ _   _ ____
 | __ )  / \  / ___| | | / ___|
 |  _ \ / _ \| |   | | | \___ \
 | |_) / ___ \ |___| |_| |___) |
 |____/_/   \_\____|\___/|____/

        B A G U S   :   F I N E - F M

 Basically A Generally Useless Solver
 Fluid Idiot's Numerical Engine for Fluid Mechanics

                 (yes, seriously)

      +--------------------------------------+
      |          BLOON  STACK               |
      |                                      |
      |   FINE-FM                            |
      |     |                                |
      |     v                                |
      |   BLOON                             |
      |     |                                |
      |     v                                |
      |   BLOON_MACHINE                     |
      |                                      |
      +--------------------------------------+

              \  water in bucket  /
               \      _____      /
                \    /     \    /
                     | ~~~ |
                     | ~~~ |
                     |_____| 

     The wrapper is a joke.
     The numbers are expected to be correct.

     Fluid statics, because apparently
     we needed a software architecture
     to tell us that water has pressure.
```

BAGUS: FINE-FM is the fluid-statics companion demo for the BLOON stack.

Supported problems:

- Hydrostatic pressure: `P = P0 + rho*g*h`
- Pressure difference: `dP = rho*g*dh`
- Pascal hydraulic: `F2 = F1*A2/A1`
- Buoyancy: `FB = rho_f*g*V`
- Hydrostatic surface force: `F = integral(p dA)`
- Water in a bucket: deliberately trivial, deliberately included

No build step. Pure Python. The project uses `NumericBackend` as the numerical seam and keeps the domain layer separate from numerical evaluation and the BLOON_MACHINE policy gate.

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

The Pygame companion entry point is `examples/main.py`.
