

from typing import Set, Tuple, Iterable
import os
import time
import subprocess
import re
import signal
from pathlib import Path
import asyncio
import socket



def trim_old_files(dir_path: str | Path, max_files: int) -> int:
    if max_files < 0:
        raise ValueError("max_files must be >= 0")

    p = Path(dir_path)
    if not p.is_dir():
        raise NotADirectoryError(p)

    files = [f for f in p.iterdir() if f.is_file()]
    count = len(files)

    if count <= max_files:
        return 0

    files.sort(key=lambda f: f.stat().st_mtime)

    to_delete = count - max_files
    for f in files[:to_delete]:
        f.unlink()

    return to_delete




def is_port_in_use(port: int, proto: str = "tcp") -> bool:
    if proto == "tcp":
        sock_type = socket.SOCK_STREAM
    elif proto == "udp":
        sock_type = socket.SOCK_DGRAM
    else:
        raise ValueError("proto должен быть 'tcp' или 'udp'")
    
    s = socket.socket(socket.AF_INET, sock_type)
    try:
        s.bind(("0.0.0.0", port))
    except OSError:
        return True
    finally:
        s.close()
    return False


class AsyncLogWriter:
    def __init__(self, path: str, flush_interval: int = 3):
        self.file = open(path, "a+")
        self.flush_interval = flush_interval
        self._stop = False
        self._start = False

    async def _flusher(self):
        while not self._stop:
            await asyncio.sleep(self.flush_interval)
            self.file.flush()

    def write(self, msg: str):
        self.file.write(msg + "\n")

        if not self._start:
            asyncio.create_task(self._flusher())
            self._start = True

    def close(self):
        self._stop = True
        self.file.flush()
        self.file.close()


def _domain_from_web2_to_web5(domain: str) -> str:
    return domain.replace('.-.', '~').replace('.-1-.', '<').replace('.-2-.', '>').replace('.-3-.', '?').replace('.-4-.', '*').replace('.-5-.', ':').replace('.-5-.', '#')
def _domain_from_web5_to_web2(domain: str) -> str:
    return domain.replace('~', '.-.').replace('<', '.-1-.').replace('>', '.-2-.').replace('?', '.-3-.').replace('*', '.-4-.').replace(':', '.-5-.').replace('#', '.-5-.')


def _kill_process_by_port(port: int):

    def _run(cmd: list[str]) -> Tuple[int, str, str]:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return p.returncode, p.stdout.strip(), p.stderr.strip()
        except FileNotFoundError:
            return 127, "", f"{cmd[0]} not found"

    def pids_from_fuser(port: int, proto: str) -> Set[int]:
        # fuser понимает 59367/udp и 59367/tcp (оба стека)
        rc, out, _ = _run(["fuser", f"{port}/{proto}"])
        if rc != 0:
            return set()
        return {int(x) for x in re.findall(r"\b(\d+)\b", out)}

    def pids_from_lsof(port: int, proto: str) -> Set[int]:
        # lsof -ti UDP:59367  /  lsof -ti TCP:59367
        rc, out, _ = _run(["lsof", "-ti", f"{proto.upper()}:{port}"])
        if rc != 0 or not out:
            return set()
        return {int(x) for x in out.splitlines() if x.isdigit()}

    def pids_from_ss(port: int, proto: str) -> Set[int]:
        # ss -H -uapn 'sport = :59367'  (UDP)  /  ss -H -tapn ... (TCP)
        flag = "-uapn" if proto == "udp" else "-tapn"
        rc, out, _ = _run(["ss", "-H", flag, f"sport = :{port}"])
        if rc != 0 or not out:
            return set()
        pids = set()
        for line in out.splitlines():
            # ... users:(("python3",pid=1234,fd=55))
            for m in re.finditer(r"pid=(\d+)", line):
                pids.add(int(m.group(1)))
        return pids

    def _find_pids(port: int, proto: str | None) -> Set[int]:
        protos: Iterable[str] = [proto] if proto in ("udp","tcp") else ("udp","tcp")
        found: Set[int] = set()
        for pr in protos:
            # Порядок: fuser -> ss -> lsof (достаточно любого)
            found |= pids_from_fuser(port, pr)
            found |= pids_from_ss(port, pr)
            found |= pids_from_lsof(port, pr)
        # не убивать себя
        found.discard(os.getpid())
        return found

    def find_pids(port: int, proto: str):
        table = {
            "udp": "/proc/net/udp",
            "udp6": "/proc/net/udp6",
            "tcp": "/proc/net/tcp",
            "tcp6": "/proc/net/tcp6",
        }

        inodes = set()

        # 1) найдём inode сокетов с этим портом
        for tname, path in table.items():
            try:
                with open(path) as f:
                    next(f)
                    for line in f:
                        cols = line.split()
                        local = cols[1]
                        inode = cols[9]

                        # local = "00000000:31F7"
                        hexport = local.split(":")[1]
                        if int(hexport, 16) == port:
                            inodes.add(inode)
            except FileNotFoundError:
                continue

        if not inodes:
            return set()

        # 2) по этим inode найдём PID
        result = set()

        for pid in filter(str.isdigit, os.listdir("/proc")):
            fd_dir = f"/proc/{pid}/fd"
            if not os.path.isdir(fd_dir):
                continue
            try:
                for fd in os.listdir(fd_dir):
                    try:
                        link = os.readlink(f"{fd_dir}/{fd}")
                        # пример: 'socket:[123456]'
                        if link.startswith("socket:["):
                            inode = link[8:-1]
                            if inode in inodes:
                                result.add(int(pid))
                    except OSError:
                        pass
            except PermissionError:
                pass

        return result
    
    def kill_pids(pids: Set[int]) -> None:
        if not pids:
            return
        me = os.getpid()
        for sig in (signal.SIGTERM, signal.SIGKILL): # type: ignore
            still = set()
            for pid in pids:
                if pid == me:
                    continue
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    continue
                except PermissionError:
                    print(f"[WARN] No permission to signal {pid}")
                    still.add(pid)
                    continue
                still.add(pid)
            if not still:
                return
            # подождём чуть-чуть
            for _ in range(10):
                live = set()
                for pid in still:
                    try:
                        os.kill(pid, 0)
                        live.add(pid)
                    except ProcessLookupError:
                        pass
                still = live
                if not still:
                    return
                time.sleep(0.1)

    def wait_port_free(port: int, proto: str | None, timeout: float = 3.0) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout:
            if not find_pids(port, proto): # type: ignore
                return True
            time.sleep(0.1)
        return not find_pids(port, proto) # type: ignore

    for proto in ("udp", "tcp"):
        pids = find_pids(port, proto)
    

        print(f"Гашу процессы на порту {port}: {sorted(pids)}")
        kill_pids(pids)

        if wait_port_free(port, proto):
            print(f"Порт {port} освобождён.")
        else:
            print(f"[ERROR] Не удалось освободить порт {port}. Возможно, другой netns/служба перезапускает процесс.")
