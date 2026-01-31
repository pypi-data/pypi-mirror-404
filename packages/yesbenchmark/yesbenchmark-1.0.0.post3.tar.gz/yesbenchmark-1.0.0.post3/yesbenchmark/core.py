import os
import subprocess
import time
import statistics

from yaspin import yaspin
from yaspin.spinners import Spinners

from .resources import *
from .freq import *
from .exceptions import *
from .stress import *
from .compute import *

def run_timed_bench(multicore=False):
    spinner = yaspin(Spinners.line)
    print("Running time benchmark for 30 seconds...")
    result_30sec = 0
    process = subprocess.Popen(['yes'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    end = time.time() + 30
    if not multicore:
        spinner.start()
    while time.time() < end:
        chunk = process.stdout.read(65536)
        if not chunk:
            break
        result_30sec += chunk.count(b'\n')
    if not multicore:
        spinner.stop()
    process.terminate()
    print("Running time benchmark for 60 seconds...")
    result_60sec = 0
    process = subprocess.Popen(['yes'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    end = time.time() + 60
    if not multicore:
        spinner.start()
    while time.time() < end:
        chunk = process.stdout.read(65536)
        if not chunk:
            break
        result_60sec += chunk.count(b'\n')
    if not multicore:
        spinner.stop()
    process.terminate()
    return result_30sec, result_60sec

def multicore():
    cpucount = os.cpu_count()
    spinner = yaspin(Spinners.line)
    spinner.start()
    results_30sec, results_60sec = multirun(run_timed_bench_multicore, cpucount)
    spinner.stop()
    total_30sec = sum(results_30sec)
    total_60sec = sum(results_60sec)
    return results_30sec, results_60sec, total_30sec, total_60sec

def run_timed_bench_multicore():
    return run_timed_bench(multicore=True)

def run_bench(mode):
    global spinner
    def processComputeResults(goal, computed, elapsedTime, suggestedK):
        print(f"Total processed chunks: {computed:,}")
        seconds = elapsedTime
        elapsedTime = format_hms(elapsedTime)
        print(f"Total time taken to compute: {elapsedTime}")
        score = computed / (seconds * suggestedK)
        score = round(score)
        return score

    if mode == "time":
        results = run_timed_bench()
        avg_30sec = results[0] / 30
        avg_60sec = results[1] / 60
        print("Results for time-based benchmark:")
        print(f"Lines in 30 seconds: {results[0]}")
        print(f"Lines in 60 seconds: {results[1]}")
        print("Averages:")
        print(f"Average lines per second (30 sec): {avg_30sec}")
        print(f"Average lines per second (60 sec): {avg_60sec}")
    
    elif mode == "multicore":
        results_30sec, results_60sec, total_30sec, total_60sec = multicore()
        for i in range(os.cpu_count()):
            print(f"Core #{i+1}:")
            print(f"  Lines in 30 seconds: {results_30sec[i]}")
            print(f"  Lines in 60 seconds: {results_60sec[i]}")
            avg_30sec = results_30sec[i] / 30
            avg_60sec = results_60sec[i] / 60
            print("  Averages:")
            print(f"    Average lines per second (30 sec): {avg_30sec}")
            print(f"    Average lines per second (60 sec): {avg_60sec}")
        print("All cores:")
        print(f"Total lines in 30 seconds: {total_30sec}")
        print(f"Total lines in 60 seconds: {total_60sec}")
        print("Averages:")
        avg_percore_30sec = total_30sec / os.cpu_count()
        avg_percore_60sec = total_60sec / os.cpu_count()
        print(f"Average lines per core (30 sec): {avg_percore_30sec}")
        print(f"Average lines per core (60 sec): {avg_percore_60sec}")
        avg_percore_30sec = avg_percore_30sec / 30
        avg_percore_60sec = avg_percore_60sec / 60
        print(f"Average lines per second per core (30 sec): {avg_percore_30sec}")
        print(f"Average lines per second per core (60 sec): {avg_percore_60sec}")
    
    elif mode == "freq":
        try:
            results_30sec, results_60sec = run_freq_bench()
        except PlatformNotSupportedError:
            print("The frequency benchmark is only supported on Linux and macOS. Please check that you are not using an unsupported environment, especially Windows.\nSkipping benchmark...")
            return
        avg_30sec = sum(results_30sec) / len(results_30sec)
        avg_60sec = sum(results_60sec) / len(results_60sec)
        max_30sec = max(results_30sec)
        max_60sec = max(results_60sec)
        min_30sec = min(results_30sec)
        min_60sec = min(results_60sec)
        print("Results for frequency-based benchmark:")
        print("Averages:")
        print(f"Average frequency (30 sec): {avg_30sec} MHz")
        print(f"Average frequency (60 sec): {avg_60sec} MHz")
        print("Your core reached the following maximum and minimum frequencies:")
        print(f"Maximum frequency (30 sec): {max_30sec} MHz")
        print(f"Maximum frequency (60 sec): {max_60sec} MHz")
        print(f"Minimum frequency (30 sec): {min_30sec} MHz")
        print(f"Minimum frequency (60 sec): {min_60sec} MHz")
    
    elif mode == "multi-freq":
        try:
            results = run_freq_bench_multicore()
        except PlatformNotSupportedError:
            print("The frequency benchmark is only supported on Linux and macOS. Please check that you are not using an unsupported environment, especially Windows.\nSkipping benchmark...")
            return
        for i in range(os.cpu_count()):
            print(f"Core #{i+1}:")
            max_30sec = max(results[i][0])
            max_60sec = max(results[i][1])
            min_30sec = min(results[i][0])
            min_60sec = min(results[i][1])
            print(f"  Max frequency achieved during 30-second bench: {max_30sec} MHz")
            print(f"  Min frequency achieved during 30-second bench: {min_30sec} MHz")
            print(f"  Max frequency achieved during 60-second bench: {max_60sec} MHz")
            print(f"  Min frequency achieved during 60-second bench: {min_60sec} MHz")
            avg_30sec = sum(results[i][0]) / len(results[i][0])
            avg_60sec = sum(results[i][1]) / len(results[i][1])
            print("  Averages:")
            print(f"    Average frequency (30 sec): {avg_30sec} MHz")
            print(f"    Average frequency (60 sec): {avg_60sec} MHz")
        print("All cores:")
        print("Averages:")
        avg_30sec = sum(sum(core_result[0]) for core_result in results) / sum(len(core_result[0]) for core_result in results)
        avg_60sec = sum(sum(core_result[1]) for core_result in results) / sum(len(core_result[1]) for core_result in results)
        print(f"Average frequency (30 sec): {avg_30sec} MHz")
        print(f"Average frequency (60 sec): {avg_60sec} MHz")
        print("Your cores reached the following maximum and minimum frequencies:")
        all_30sec = [freq for (r30, r60) in results for freq in r30]
        min_30sec = min(all_30sec)
        max_30sec = max(all_30sec)
        all_60sec = [freq for (r30, r60) in results for freq in r60]
        min_60sec = min(all_60sec)
        max_60sec = max(all_60sec)
        print(f"Maximum frequency (30 sec): {max_30sec} MHz")
        print(f"Maximum frequency (60 sec): {max_60sec} MHz")
        print(f"Minimum frequency (30 sec): {min_30sec} MHz")
        print(f"Minimum frequency (60 sec): {min_60sec} MHz")

    elif mode == "stress":
        results_30sec, results_60sec = run_stress_bench()
        avg_30sec = sum(results_30sec) / len(results_30sec)
        avg_60sec = sum(results_60sec) / len(results_60sec)
        max_30sec = max(results_30sec)
        max_60sec = max(results_60sec)
        min_30sec = min(results_30sec)
        min_60sec = min(results_60sec)
        stddev_30sec = statistics.stdev(results_30sec)
        stddev_60sec = statistics.stdev(results_60sec)
        print("Results for stress/utilization benchmark:")
        print("Averages:")
        print(f"Average utilization (30 sec): {avg_30sec}%")
        print(f"Average utilization (60 sec): {avg_60sec}%")
        print("Your CPU reached the following maximum and minimum utilizations:")
        print(f"Maximum utilization (30 sec): {max_30sec}%")
        print(f"Maximum utilization (60 sec): {max_60sec}%")
        print(f"Minimum utilization (30 sec): {min_30sec}%")
        print(f"Minimum utilization (60 sec): {min_60sec}%")
        print("Standard Deviations:")
        print(f"Stability over 30 seconds (standard deviation): {stddev_30sec}%")
        print(f"Stability over 60 seconds (standard deviation): {stddev_60sec}%")

    elif mode == "compute":
        goal, computed, elapsedTime, suggestedK = run_compute_bench(level="performance")
        score = processComputeResults(goal, computed, elapsedTime, suggestedK)
        print(f"Score: P{score:,}")
    elif mode == "compute-xt":
        goal, computed, elapsedTime, suggestedK = run_compute_bench(level="extreme")
        score = processComputeResults(goal, computed, elapsedTime, suggestedK)
        print(f"Score: X{score:,}")
