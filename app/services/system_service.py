import os
import subprocess
from app.schemas.recommendation import SystemInfo


def get_system_info(db_path: str) -> SystemInfo:
    def run(cmd: str) -> str:
        return subprocess.check_output(cmd, shell=True).decode().strip()

    return SystemInfo(
        uptime=subprocess.check_output("uptime").decode().strip(),
        total_ram_mb=run("free -m | awk 'NR==2{print $2}'"),
        available_ram_mb=run("free -m | awk 'NR==2{print $7}'"),
        cpu_model=run("grep 'model name' /proc/cpuinfo | uniq | awk -F: '{print $2}'"),
        cpu_clock_mhz=run("grep 'cpu MHz' /proc/cpuinfo | uniq | awk -F: '{print $2}'"),
        database_size=run(f"du -sh '{db_path}'"),
    )
