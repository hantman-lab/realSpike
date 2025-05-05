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

