import argparse
import csv
import datetime
import os.path
import sys
import time

import psutil

DATA_FILE = "data.csv"


class InfoType:
    TIME = "TIME"
    CPU_PERCENT = "%CPU"
    MEM_WSET = "MEM_WSET"
    MEM_PRIVATE = "MEM_PRIVATE"
    MEM_RSS = "MEM_RSS"
    MEM_VMS = "MEM_VMS"
    NUM_HANDLES = "NUM_HANDLES"
    NUM_FDS = "NUM_FDS"


class ProcessMonitor:
    def __init__(self, executable_path: str, interval: int):
        self.executable_path = executable_path
        self.interval = interval
        self.process = None

    def _run_process(self):
        try:
            self.process = psutil.Popen(self.executable_path)
        except FileNotFoundError:
            sys.exit(f"The specified file cannot be found: "
                     f"'{self.executable_path}'")
        except OSError:
            sys.exit(f"The specified file is not executable: "
                     f"'{self.executable_path}'")

    def _get_process_info(self):
        try:
            with self.process.oneshot():
                process_info = {
                    InfoType.TIME: str(datetime.datetime.now()),
                    InfoType.CPU_PERCENT: self.process.cpu_percent()
                }
                memory_info = self.process.memory_info()
                if psutil.WINDOWS:
                    process_info.update({
                        InfoType.MEM_WSET: memory_info.wset,
                        InfoType.MEM_PRIVATE: memory_info.private,
                        InfoType.NUM_HANDLES: self.process.num_handles()
                    })
                else:
                    process_info.update({
                        InfoType.MEM_RSS: memory_info.rss,
                        InfoType.MEM_VMS: memory_info.vms,
                        InfoType.NUM_FDS: self.process.num_fds()
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Stop monitoring if the process is stopped
            sys.exit()
        else:
            return process_info

    def start(self, print_process_info=False):
        self._run_process()
        data_file_exists = os.path.exists(DATA_FILE)
        with open(file=DATA_FILE, mode="a", newline='') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=get_field_names())
            if not data_file_exists:
                writer.writeheader()
            while self.process.is_running():
                process_info = self._get_process_info()
                if print_process_info:
                    print("\t".join(
                        f"{key}: {value}" for key, value in process_info.items()
                    ))
                writer.writerow(process_info)
                csv_file.flush()
                time.sleep(self.interval)


def get_field_names():
    """
    Get headers for CSV data file
    """
    field_names = [InfoType.TIME,
                   InfoType.CPU_PERCENT]
    if psutil.WINDOWS:
        field_names.extend([InfoType.MEM_WSET,
                            InfoType.MEM_PRIVATE,
                            InfoType.NUM_HANDLES])
    else:
        field_names.extend([InfoType.MEM_RSS,
                            InfoType.MEM_VMS,
                            InfoType.NUM_FDS])
    return field_names


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--executable",
                        required=True,
                        help="Path to the executable file for the process",
                        type=str)
    parser.add_argument("-i", "--interval",
                        required=True,
                        help="Time interval between data collection (in seconds)",
                        type=int)
    parser.add_argument("-p", "--print-process-info",
                        help="Print collected process info",
                        action="store_true")

    return parser.parse_args()


def main():
    args = get_args()
    proc_monitor = ProcessMonitor(
        executable_path=args.executable,
        interval=args.interval)
    proc_monitor.start(print_process_info=args.print_process_info)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
