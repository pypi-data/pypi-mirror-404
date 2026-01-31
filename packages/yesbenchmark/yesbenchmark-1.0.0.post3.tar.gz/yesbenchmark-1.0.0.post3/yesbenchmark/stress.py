import subprocess
import time
import platform

# Troublesome imports
try:
    import psutil
    psutilExist = True
except ImportError:
    psutilExist = False

from yaspin import yaspin
from yaspin.spinners import Spinners

from .resources import *
from .freq import *
from .exceptions import *
if platform.system() == "Darwin":
    from .darwin_shenanigans import *

def run_stress_bench():
    spinner = yaspin(Spinners.line)
    if platform.system() == "Darwin":
        cpuPfunc = cpu_percent_macos
    else:
        cpuPfunc = psutil.cpu_percent
    print("Running stress benchmark for 30 seconds...")
    result_30sec = []
    process = subprocess.Popen(['yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time() + 30
    spinner.start()
    if psutilExist:
        nothingInParticular = cpuPfunc(interval=None) # initialize psutil
    while time.time() < end:
        result_30sec.append(cpuPfunc(interval=1))
    spinner.stop()
    process.terminate()
    print("Running stress benchmark for 60 seconds...")
    result_60sec = []
    process = subprocess.Popen(['yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time() + 60
    spinner.start()
    if psutilExist:
        nothingInParticular = cpuPfunc(interval=None) # initialize psutil again
    while time.time() < end:
        result_60sec.append(cpuPfunc(interval=1))
    spinner.stop()
    process.terminate()
    return result_30sec, result_60sec
