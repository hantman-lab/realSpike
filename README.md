# realSpike

Real-time closed loop visualization and analysis for flexible neural manipulation
using two-photon holographic photostimulation

![realSpike](https://github.com/hantman-lab/realSpike/assets/69729525/f2176636-8adc-46c8-9b0d-60b40e6141a5)

## Installation

[//]: # "add note about python version"

```bash
# clone the repo
git clone https://github.com/hantman-lab/realSpike.git

# navigate to the repo
cd realSpike/

# install in editable mode
pip install -e .
```

## Installing `improv`

**You must already have `redis` installed.**

You cannot simply `pip install improv`. Do the following instead:

```bash
# clone
git clone https://github.com/project-improv/improv.git

cd improv/

# add remote
git remote add rwschonberg https://github.com/rwschonberg/improv
# fetch his branches
git fetch rwschonberg
# checkout a new branch off of the zmq branch
git checkout -b redis-only rwschonberg/zmq

### IMPORTANT: relax the numpy constraint in the pyproject.toml before in-place install
pip install -e .
```

## Linting checks

```bash
ruff format
ruff check
```
