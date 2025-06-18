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

### Redis Tips

```python
# check the size of the store
self.client.client.info()['used_memory_human']

# check the number of keys in the store
self.client.client.dbsize()

# manually add something to the store
self.client.client.set(data_id, data, nx=True)

# delete something from the store
self.client.client.delete(data_id)
```

### Compressing the data using `numpy`

```python
# compress data to bytes
data = data.tobytes()
# generate data_id
data_id = str(os.getpid()) + str(uuid.uuid4())

# decompress the data
np.frombuffer(self.client.client.get(data_id)).reshape(384, 150)
```

# 5/22/25

## Installing `pyschopy` is painful!!
- python pinned to `<3.12`, need environment with 3.11
- also, installing `wxPython` on Fedora41 is painful 
  - install using wheels from online 

```bash
# install wx python from old wheels 
pip install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/fedora-38/wxPython-4.2.1-cp311-cp311-linux_x86_64.whl
```
- additionally, with Fedora41 when you install one of the dependencies `libtiff`, it only has the 
  shared object file for version 6 and the `wx` wheels are looking for version 5
  - SOLUTION: create a symlink from version 6 so it can be found as version 5

```bash
sudo ln -s /usr/lib64/libtiff.so.6 /usr/lib64/libtiff.so.5
sudo ldconfig
```

## Other
- Each actor only has one `q_out`
  - If actor needs to send two different things to two different actors, put the data in the store 
    under different ids and send the data in the queue as a tuple (unpack appropriately in the downstream actors)

# 6/17/2025

- Redis store setting the data at a particular `key`, keyword argument `nx` specifies whether the data at a particular `key`, if it exists, can be overwritten or not
  - If trying to reuse key, need to specify `nx=False`
 
# 6/18/2025
- Working with a windows machine (bleh)
  - activating a venv: `./venvs/bah/Scripts/Activate.ps1`
- Weird certification error when trying to install things with `pip`:  `pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org <package_name>`
