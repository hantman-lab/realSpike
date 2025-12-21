# Streaming data from disk 

Practice streaming raw voltage data from disk, performing MUA, and visualizing it.

```
├── stream_data
│   ├── actors
│   │   ├── generator.py
│   │   ├── processor.py
│   │   ├── visual.py
│   ├── stream.yaml
│   └── viz.py
└── 
```

## Usage

1. Start the TUI and call setup

```bash
improv run ./real_spike/stream_data/stream.yaml 

setup
```

2. Run the visualization python file `viz.py` 

```bash
python ./real_spike/stream_data/viz.py
```

**Should see output "Made connection" in terminal.**

3. Call `run` in the TUI