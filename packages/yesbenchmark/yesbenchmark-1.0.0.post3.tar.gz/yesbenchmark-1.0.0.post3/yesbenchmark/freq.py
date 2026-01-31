import os
import subprocess
import time
import platform
import sys

from yaspin import yaspin
from yaspin.spinners import Spinners

from .resources import *
from .exceptions import *

def run_freq_bench(multicore=False, core=0):
    if platform.system() == "Darwin":
        print("This benchmark requires sudo privileges on macOS, please enter your password if prompted:")
        os.system("sudo -v")
        PMCheck = os.system("command -v powermetrics > /dev/null")
        if PMCheck != 0:
            print("The `powermetrics` utility is not present on this system and required by the macOS version of this benchmark. Please install it to continue.")
            print("NOTE: Perhaps your OS X version is too old.")
            sys.exit(PMCheck)
    elif platform.system() == "Linux":
        pass
    else:
        raise PlatformNotSupportedError("Frequency benchmark is only supported on Linux and macOS.")
    spinner = yaspin(Spinners.line)
    print("Running frequency benchmark for 30 seconds...")
    result_30sec = []
    if platform.system() == "Linux":
        process = subprocess.Popen(['taskset', '-c', str(core), 'yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif platform.system() == "Darwin":
        process = subprocess.Popen(['yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time() + 30
    if not multicore:
        spinner.start()
    if platform.system() == "Linux":
        while time.time() < end:
            time.sleep(1)
            result_30sec.append(get_proc_mhz()[core])
    elif platform.system() == "Darwin":
        while time.time() < end:
            time.sleep(1)
            freqs = get_darwin_mhz()
            if not multicore:
                if freqs:
                    max_freq = max(freqs)
                    result_30sec.append(max_freq)
            else:
                coreFreq = freqs[core]
                result_30sec.append(coreFreq)
    if not multicore:
        spinner.stop()
    process.terminate()
    print("Running frequency benchmark for 60 seconds...")
    result_60sec = []
    if platform.system() == "Linux":  
        process = subprocess.Popen(['taskset', '-c', str(core), 'yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif platform.system() == "Darwin":
        process = subprocess.Popen(['yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time() + 60
    if not multicore:
        spinner.start()
    if platform.system() == "Linux":
        while time.time() < end:
            time.sleep(1)
            result_60sec.append(get_proc_mhz()[core])
    elif platform.system() == "Darwin":
        while time.time() < end:
            time.sleep(1)
            freqs = get_darwin_mhz()
            if not multicore:
                if freqs:
                    max_freq = max(freqs)
                    result_60sec.append(max_freq)
            else:
                coreFreq = freqs[core]
                result_60sec.append(coreFreq)
    if not multicore:
        spinner.stop()
    process.terminate()
    return result_30sec, result_60sec

def run_freq_bench_multicore():    
    if platform.system() == "Darwin":
        print("This benchmark requires sudo privileges on macOS, please enter your password if prompted:")
        os.system("sudo -v")
        PMCheck = os.system("command -v powermetrics")
        if PMCheck != 0:
            print("The `powermetrics` utility is not present on this system and required by the macOS version of this benchmark. Please install it to continue.")
            print("NOTE: Perhaps your OS X version is too old.")
            sys.exit(PMCheck)
    results_30sec = ()
    results_60sec = ()
    coreCount = os.cpu_count()
    spinner = yaspin(Spinners.line)
    spinner.start()
    results_30sec, results_60sec = multirun_coreArg(freq_bench_multicore_worker, coreCount)
    spinner.stop()
    return list(zip(results_30sec, results_60sec))

def freq_bench_multicore_worker(core=0):
        return run_freq_bench(multicore=True, core=core)
