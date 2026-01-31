import os
import subprocess
import time
import sys

from yaspin import yaspin
from yaspin.spinners import Spinners
import cowsay

from .resources import *

def spawn_processes(command, n, moo=False):
    processList = []
    for i in range(n):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processList.append(process)
    if moo:
        cowsay.cow("Is your program mooing along smoothly today?")
    return processList

def run_compute_bench(level="performance"):
    cores = os.cpu_count()
    goal = 27000000000
    if level == "extreme":
        goal *= 10
        suggestedK = 1000000
    elif level == "performance":
        suggestedK = 10000
    else:
        print("ERROR: Invalid difficulty level")
        sys.exit(1)
    spinner = yaspin()

    computed = 0
    spinner.start()
    spinner.text = f"Starting compute benchmark in {level} mode, this may take a while..."
    time.sleep(1)
    start = time.perf_counter()
    processes = spawn_processes(["yes"], cores)
    while computed < goal:
        for process in processes:
                chunk = process.stdout.read(65536)
                if not chunk:
                    break
                computed += chunk.count(b'\n')
        spinner.text = f"{computed}/{goal} chunks done"
    for process in processes:
        process.terminate()
    end = time.perf_counter()
    elapsedTime = end - start
    spinner.stop()

    return goal, computed, elapsedTime, suggestedK
