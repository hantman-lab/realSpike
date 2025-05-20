# Notes

A place to keep detailed notes of progress.

## 5/1/25

- Update to a newer version of [SpikeGLX-CPP-SDK](https://github.com/billkarsh/SpikeGLX-CPP-SDK/tree/main)
    - Good news! The repo has now been updated so that we can compile to Linux with no issues

```bash
git clone https://github.com/billkarsh/SpikeGLX-CPP-SDK.git

cd SpikeGLX-CPP-SDK/LINUX/API/

# make the file executable
sudo chmod +x make-install.sh 

# run the file 
./make-install.sh 
```

The shared object file `libSglxApi.so` that is created can be copied into the `realSpike` directory 
and gives access to the necessary SpikeGLX API calls for making a connection/fetching data. 

## 5/5/25

- Get working environment 
  - install `improv` (see below) 
    - must have `redis` already installed!
  - install other dependencies via `pip install -r requirements.txt`

For now, need to work off of a branch from Richard's fork.
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

# 5/6/25

- Increasing maximum store size
  - include as a setting in the yaml file 

```yaml
actors: ... 

connections: ...

settings: 
  - store_size = 5_000_000_000
```

# 5/20/25

- Latency issues
  - Main issues seems to be when data is saved in the store using `zlib.compression` (increases latency of that operation to ~6-7ms)
  - For now, manually editing the `improv.store put()` method to not compress the data
    - later will do a PR to add `compression` as a bool flag kwarg