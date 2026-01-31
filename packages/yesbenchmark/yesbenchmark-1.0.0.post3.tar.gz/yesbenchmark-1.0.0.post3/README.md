# yesBenchMark
[![PyPI version](https://img.shields.io/pypi/v/yesBenchMark?color=blue)](https://pypi.org/project/yesBenchMark/)
[![License](https://img.shields.io/github/license/matthewyang204/yesBenchMark)](https://github.com/matthewyang204/yesBenchMark/blob/main/LICENSE)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/yesbenchmark?period=total&units=ABBREVIATION&left_color=GREY&right_color=GREEN&left_text=PyPI+downloads)](https://pepy.tech/projects/yesbenchmark)
<img src=https://img.shields.io/github/downloads/matthewyang204/yesBenchMark/total alt="GitHub downloads">


yesBenchMark is a crazy tool for benchmarking the CPU in UNIX & UNIX-like systems. It abuses the `yes` command to load the CPU and measures CPU utilization, speed, and compute.

<img src="https://raw.githubusercontent.com/matthewyang204/yesBenchMark/master/assets/yesbenchmark-demo-linux.gif" width="1000" alt="yesBenchMark demo (animated)">

# Features
- Extremely tiny & light
- Can run on extremely old hardware (OS X 10.4 Tiger is oldest it can run on of all the stuff out there, with a modest G3)
- Can do a ton of different modes, varying in load from light to extremely punishing to see how far you can push your CPU:
    - `time` - See how much the CPU can output in 30 & 60 seconds respectively in a single thread (`yes`)
    - `multicore` - Multi-core version of the `time` benchmark
    - `freq` - Bench how fast your CPU core can turbo
    - `multi-freq` - Multi-core version of `freq` benchmark
    - `stress` - See how little of the total CPU a single thread can use, also includes a stability measurement
    - `compute` - Check how long it takes the CPU to compute 27,000,000,000 hunks of data (each hunk is a single `y\n`)
    - `compute-xt` - `compute` benchmark but with 10x the hunks
- Written in Python & extremely portable, so runs almost anywhere
- Probably one of the most practical benchmarks out there - measures CPU load, CPU frequency, and other things encouuntered in day-to-day workloads; none of the shenanigans that most tools use to grade your CPU's performance

# Usage
```
Usage: yesbenchmark [options]
Options:
  --help, -h          Show this help message
  --mode=MODE         Run specific mode of benchmark

Modes:
all                   Run all modes of benchmarks
time                  Run time-bound benchmark
multicore             Run time-bound benchmark for all cores
freq                  Run frequency-bound benchmark
multi-freq            Run multi-core version of frequency-bound benchmark
stress                Run stress/utilization benchmark
compute               Run compute benchmark (time taken depends on CPU speed)
compute-xt            Run a more extreme version of compute benchmark
```
Well that is...all the capabilities of the program. We recommend the `compute` mode for most people.

Scores for reference (performance is `compute` & extreme is `compute-xt`):

M1 Max with 8 P-cores & 2 E-cores (10 cores total):
- P70,363 → performance mode
- X685 → extreme mode

i7-2600 with 8 cores:
- P55,609 → performance mode
- X557 → extreme mode

G5 with 1 core:
- P572 → performance mode
- {untested} → extreme mode (would take forever on my iMac G5 and overheat it)

Note: Do NOT run the program with zero arguments unless you want to run ALL benchmarks except the `compute-xt` one. This will take a long time and likely overheat your computer.

# Installation
Requirements:
- Python 3.8 or later (we don't test for older, probably works down to 3.6)
- OS X 10.5 Leopard or later (if too old to be supported by Homebrew, please use Tigerbrew to install Python 3.10) or Linux 3.2 or later (BSDs may be supported at a later time when I have time to spin up one in a virtual machine)
    - Other UNIXes are probably going to work, so long as they are at least UNIX-like. We don't currently test for these other systems, but fixes are welcome. We might also start testing for BSD sometime.

To install yesBenchMark via pip:
```
pip install yesbenchmark
```
Or if you have cloned the repo for development (note that this will also allow you to edit the src code without re-installing for ease):
```
pip install -e .
```

## Compiling and installing as a binary
Requirements:
- The above requirements
- If macOS, an Intel x86_64 CPU or better
- MacOSX 10.9 or later if on Mac

To compile:
```
python3 compile.py
```
After that, just copy the binary in dist out and into a directory in your PATH.

# License
This project is licensed under the GNU General Public License v3.0 (GPLv3). Please note that it will also be compatible with any future versions of this license, should they be released. All past and future versions of this software are covered by this license. See the `LICENSE` file for full details.
