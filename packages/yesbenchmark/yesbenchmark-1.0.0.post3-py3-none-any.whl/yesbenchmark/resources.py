import platform
import subprocess
import re
from concurrent.futures import ProcessPoolExecutor
import cowsay
import datetime

def multirun(func, n):
    x = []
    y = []

    with ProcessPoolExecutor() as ex:
        futures = [ex.submit(func) for i in range(n)]
        for f in futures:
            a, b = f.result()
            x.append(a)
            y.append(b)

    return x, y

def multirun_coreArg(func, n):
    x = ()
    y = ()

    with ProcessPoolExecutor() as ex:
        futures = [ex.submit(func, core=i) for i in range(n)]
        for f in futures:
            a, b = f.result()
            x += (a,)
            y += (b,)

    return x, y

def dna(string="", level=0):
    if string:
        level = string.count("v")
    if level == 0:
        print("There are no Easter Eggs in this program.")
    elif level == 1:
        print("There really are no Easter Eggs in this program.")
    elif level == 2:
        print("Did I not tell you there are no Easter Eggs in this program?")
    elif level == 3:
        print("Go away!")
    elif level == 4:
        print("If I give you an easter egg, will you please go away?")
    elif level == 5:
        print("Alright, you win.")
        message = "TACGATTGA\n---------\nATGCTAACT"
        if platform.system() == "Linux":
            cowsay.tux(message)
        elif platform.system() == "Darwin":
            cowsay.daemon(message)
        else:
            cowsay.cow(message)
    elif level >= 6:
        print("It's what you get if you re-populate the DNA sequence with the other half from its first half.")

def get_proc_mhz():
    freqs = []
    with open("/proc/cpuinfo") as f:
        for line in f:
            if "cpu MHz" in line:
                freqs.append(float(line.split(":")[1].strip()))
    return freqs

def get_darwin_mhz():
    cmd = [
        "sudo", "powermetrics",
        "--samplers", "cpu_power",
        "-n", "1",
        "-i", "500",
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )

    cpu_freqs = {}
    pattern = re.compile(r"CPU\s+(\d+)\s+frequency:\s+(\d+)\s+MHz")

    for line in result.stdout.splitlines():
        match = pattern.search(line)
        if match:
            cpu = int(match.group(1))
            freq = int(match.group(2))
            cpu_freqs[cpu] = freq

    return [cpu_freqs[i] for i in sorted(cpu_freqs)]

def format_hms(total_seconds):
    return str(datetime.timedelta(seconds=total_seconds))