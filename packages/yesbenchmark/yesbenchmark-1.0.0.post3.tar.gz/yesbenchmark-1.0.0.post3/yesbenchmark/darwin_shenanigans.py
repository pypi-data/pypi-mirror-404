import ctypes
import time
import subprocess

libc = ctypes.CDLL("/usr/lib/libc.dylib")

HOST_CPU_LOAD_INFO = 3
CPU_STATE_USER = 0
CPU_STATE_SYSTEM = 1
CPU_STATE_IDLE = 2
CPU_STATE_NICE = 3

class host_cpu_load_info(ctypes.Structure):
    _fields_ = [("cpu_ticks", ctypes.c_uint * 4)]

def cpu_percent_macos(interval=1.0):
    def read():
        count = ctypes.c_uint(4)
        info = host_cpu_load_info()
        libc.host_statistics( 
            libc.mach_host_self(),
            HOST_CPU_LOAD_INFO,
            ctypes.byref(info),
            ctypes.byref(count)
        )
        user, system, idle, nice = info.cpu_ticks
        idle_total = idle
        non_idle = user + system + nice
        total = idle_total + non_idle
        return idle_total, total

    idle1, total1 = read()
    time.sleep(interval)
    idle2, total2 = read()

    return (1 - (idle2 - idle1) / (total2 - total1)) * 100.0

def getMacOSVersion():
    rawVersion = subprocess.check_output(['/usr/bin/sw_vers', '-productVersion'], text=True)
    majorVersion, _ = rawVersion.rsplit(".", 1)
    return majorVersion
