# Streaming data from disk 

Practice streaming raw voltage data from disk, performing MUA, and visualizing it.

```
├── stream_data
│   ├── actors
│   │   ├── generator.py
│   │   ├── processor.py
│   │   ├── visual.py
│   ├── stream.yaml
│   └── viz.ipynb
└── 
```

## TODO
- [x] send chunks of data from the generator to the processor
- [x] perform MUA in the processor
- [x] send data from the processor to the visual
- [x] send data from visual to ipynb for viz via fpl
- [ ] add benchmarking for latency 
  - [ ] whole chunk of data? (~8 GB)
  - [ ] one segment of data?
  - [ ] from generator to processor to viz? 
- [ ] optimize the plotting code better so it streams easier (just change y values)
- [ ] fix the relative import for the utils

## Usage

1. Start the TUI and call setup

```bash
improv run ./real_spike/stream_data/stream.yaml 

setup
```

2. In the jupyter lab notebook run all the cells until you see initial plot 

3. Call `run` in the TUI