import sys
import platform
import cowsay
import os

from .core import *
from .exceptions import *
from .resources import *

args = sys.argv

windowsMSG = "You're quite right that this program will run correctly on Windows inside of a Cygwin/MSYS/MingW environment... Just don't expect it to be accurate, as that is a LOT of compatibility layers over the NT kernel! It's never going to be as close to bare metal as a proper UNIX system."
if platform.system() == "Windows" and '--allow-windows' not in args:
    raise PlatformNotSupportedError("Windows cannot possibly have coreutils installed and is not a supported configuration. This tool does not have the Super NT (NoodleTech) Powers required to run on Windows. Please install Linux or another UNIX-like system on your computer to continue.")
elif platform.system() == "Windows" and '--allow-windows' in args:
    print("Alright, you win.")
    cowsay.cow(windowsMSG)
    cowsay.cow("Oh, and don't blame ME when the numbers inevitably look like soup.")

def print_version():
    print("yesbenchmark, version 1.0.0")
    print("(C) 2026 Matthew Yang (杨佳明)")

def print_usage():
    print("Usage: yesbenchmark [options]")
    print("Options:")
    print("  --help, -h          Show this help message")
    print("  --mode=MODE         Run specific mode of benchmark")
    print("")
    print("Modes:")
    print("all                   Run all modes of benchmarks")
    print("time                  Run time-bound benchmark")
    print("multicore             Run time-bound benchmark for all cores")
    print("freq                  Run frequency-bound benchmark")
    print("multi-freq            Run multi-core version of frequency-bound benchmark")
    print("stress                Run stress/utilization benchmark")
    print("compute               Run compute benchmark (time taken depends on CPU speed)")
    print("compute-xt            Run a more extreme version of compute benchmark")
    print("")
    print("This benchmarking program does not have Super DNA Powers.")

def main():
    yesCheck = os.system("command -v yes > /dev/null")
    if yesCheck != 0:
        print("The command line utility `yes` is not installed and is required by this program. Please install it to continue.")
        sys.exit(yesCheck)

    if '--help' in args or '-h' in args:
        print_usage()
        sys.exit(0)
    elif '--version' in args or '-v' in args:
        print_version()
        sys.exit(0)
    
    if len(args) > 1:
        if args[1] == "dna":
            if len(args) <= 2:
                dna()
            else:
                dna(args[2])
            sys.exit(0)
    
    if '--mode=time' in args:
        mode = "time"
    elif '--mode=multicore' in args:
        mode = "multicore"
    elif '--mode=freq' in args:
        mode = "freq"
    elif '--mode=multi-freq' in args:
        mode = "multi-freq"
    elif '--mode=stress' in args:
        mode = "stress"
    elif '--mode=compute' in args:
        mode = "compute"
    elif '--mode=compute-xt' in args:
        mode = "compute-xt"
    else:
        mode = "all"

    if mode == "all":
        print("Running ALL benchmarks...")
        print("Running time benchmark:")
        run_bench("time")
        print("Running multicore benchmark:")
        run_bench("multicore")
        print("Running freq benchmark:")
        run_bench("freq")
        print("Running multi-freq benchmark:")
        run_bench("multi-freq")
        print("Running stress/utilization benchmark:")
        run_bench("stress")
        print("Running compute benchmark:")
        run_bench("compute")
        # We skip the compute-xt benchmark because it may cause overheating and other issues on older computers
        print("Benchmarks done! Results are above.")
    else:
        print(f"Running {mode} benchmark...")
        run_bench(mode)
        print("Benchmark finished! Results are printed above.")

if __name__ == "__main__":
    main()
