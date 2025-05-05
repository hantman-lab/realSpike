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

## ISSUES

- store size is very small (0.25GB), will only process that much data before maxmemory exceeded errors