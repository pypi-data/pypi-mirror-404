# RCDL

Riton Coomer Download Manager  
`rcdl` is a tool to automatically download the videos of your favorites creators from [coomer.st](https://coomer.st) and [kemono.cr](https://kemono.cr)


## Install
### Dependencies
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [aria2](https://github.com/aria2/aria2)
- [ffmpeg](https://www.ffmpeg.org/download.html) (Only for `fuse` command)  
- [HandBrakeCLI](https://handbrake.fr/docs/en/latest/cli/cli-options.html) (Only for `opti` command)
Recommended install:
```bash
pipx install yt-dlp streamlit
sudo apt update
sudo apt install aria2 ffmpeg handbrake-cli python3-tk
```
### Install RCDL
It is recommended to use `pipx` to install `rcdl`
```bash
pipx install rcdl
```
or else:  
```bash
pip install rcdl
```

## How to use

Run the CLI with:

```bash
rcdl --help
```

By default all files will live in `~/Videos/rcdl/`. Cache, configuration and log file will be in a hidden `rcdl/.cache/` folder.

Main function:  
```bash
rcdl refresh    # look creators.json and find all possible videos
rcdl dlsf       # download all found videos
rcdl discover   # Discover new creator (WIP)
rcdl opti       # Optimized video to reduce disk storage usage
rcdl fuse       # Fuse all videos within a same post if they are fully downloaded
```

Manage creators:  
```bash
rcdl list   # list all current creators
rcdl add [URL]
rcdl add [service]/[creator_id]
rcdl remove [creator_id]
```

Helper function:  
```bash
rcdl status     # give number of entry in the database per tables and status
rcdl clean --all      # remove all partially downloaded file, external dependencies cache, etc...
rcdl show-config        # print all config var and theirs value (paths, etc...)
```

### Settings
Default settings file:
```toml
[app]
default_max_page = 10
max_fail_count = 7
timeout = 10

[fuse]
max_width = 1920
max_height = 1080
fps = 30
preset = "veryfast"
threads = 0

[paths]
base_dir = "~/Videos/rcdl"
handbrake_run_cmd = "HandBrakeCLI"
```

In `rcdl/.cache/config.toml`:
```toml
[paths]
handbrake_run_cmd = "HandBrakeCLI"  # if installed via apt
handbrake_run_cmd = "flatpak run --command=HandBrakeCLI fr.handbrake.ghb"   # if installed via flatpak
```

## Dev
### Install
```bash
git clone https://github.com/ritonun/cdl.git rcdl
cd rcdl
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Deploy
```bash
python3 -m pip install --upgrade build
python3 -m pip install --upgrade twine
```
