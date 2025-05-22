# Streaming data from disk 

Practice streaming raw voltage data from disk, performing MUA, and visualizing it. Also, practice pattern 
generation using `psychopy`.

```
├── stream_data
│   ├── actors
│   │   ├── generator.py
│   │   ├── patterns.py
│   │   ├── processor.py
│   │   ├── visual.py
│   ├── stream.yaml
│   └── viz.ipynb
│   └── psychopy.py
└── 
```

## Usage

1. Start the TUI and call setup

```bash
improv run ./real_spike/stream_data/stream.yaml 

setup
```

2. In the jupyter lab notebook run all the cells until you see initial plot [OPTIONAL]

3. Run the `psychopy.py` file [OPTIONAL]

```bash
python ./real_spike/stream_data/psychopy_viz.py
```

**Should see output "Made connection" in terminal.**

3. Call `run` in the TUI