import hashlib
import threading
from socket import socket
import time

## שתי הפונקציות האלה הם האלגוריתמים בשביל להפוך את ההודעות למספרים וכד

def n_to_decimal(s, chars):
    base = len(chars)
    value = 0
    for c in s:
        value = value * base + chars.index(c)
    return value

def decimal_to_n(value, chars, length):
    base = len(chars)
    out = []
    for _ in range(length):
        out.append(chars[value % base])
        value //= base
    return ''.join(reversed(out))


## קלאס עובד שמתחיל להרציץ את הכל הקוד
class Worker:
    def __init__(self, ip, port):
        print(f"[INIT] Creating worker...")
        self.soc = socket()
        self.soc.connect((ip, port))
        print(f"[CONNECTED] Connected to manager at {ip}:{port}")

        self.running = True
        self.job_active = False

        self.found_password = None
        self.lock = threading.Lock()

    def start(self):
        print("[START] Starting listener thread...")
        listen_thread = threading.Thread(target=self.listen, daemon=True)
        listen_thread.start()

    def listen(self):
        print("[LISTEN] Listening for messages...")
        while self.running:
            try:
                data = self.soc.recv(1024)
            except OSError:
                print("[ERROR] Socket error while receiving.")
                break

            if not data:
                print("[DISCONNECTED] Manager closed the connection.")
                break

            msg = data.decode().strip()
            print(f"[RECEIVED] {msg}")

            if msg == "301":
                print("[STOP] Received STOP (301) from manager.")
                self.running = False
                return

            if msg == "ping":
                print("[PING] Received ping → sending pong")
                self.soc.sendall(b"pong")
                continue

            if not self.job_active:
                try:
                    target_hash, start, end, chars = msg.split()
                except ValueError:
                    print("[WARN] Malformed message. Ignoring.")
                    continue

                self.chars = list(chars)
                self.length = len(start)

                print(f"[JOB] Starting job range: {start} → {end}  | hash={target_hash}")

                t = threading.Thread(
                    target=self.dispatch_bruteforce,
                    args=(target_hash, start, end),
                    daemon=True
                )
                t.start()

    ##ניהול פיצול הthreads לעוד עבודות

    def dispatch_bruteforce(self, target_hash, start, end, threads=6):
        self.job_active = True
        self.found_password = None

        splits = self.split_range(start, end, threads)

        print(f"[SPLIT] Range split into {threads} parts:")
        for s, e in splits:
            print(f"        - {s} → {e}")

        ts = []
        for s, e in splits:
            t = threading.Thread(
                target=self.bruteforce_range,
                args=(target_hash, s, e),
                daemon=True
            )
            ts.append(t)
            t.start()

        for t in ts:
            t.join()

        if self.found_password:
            print(f"[FOUND] Found match: {self.found_password}")
            self.soc.sendall(f"{self.found_password} 303".encode())
        else:
            print("[NOT FOUND] No match in any subrange.")
            self.soc.sendall(b" 404")

        print("[JOB COMPLETE] Finished.")
        self.job_active = False
    
    ## שתי הפונקציות הבאות נועדו כדי לפצל את ההעבודה לעוד threads

    def bruteforce_range(self, target_hash, start, end):
        start_num = n_to_decimal(start, self.chars)
        end_num = n_to_decimal(end, self.chars)
        target = target_hash.lower()

        for num in range(start_num, end_num + 1):

            if not self.running:
                return

            with self.lock:
                if self.found_password is not None:
                    return

            combo = decimal_to_n(num, self.chars, self.length)

            if hashlib.md5(combo.encode()).hexdigest() == target:
                with self.lock:
                    self.found_password = combo
                return

    def split_range(self, start, end, parts):
        start_num = n_to_decimal(start, self.chars)
        end_num = n_to_decimal(end, self.chars)

        total = end_num - start_num + 1
        chunk = total // parts

        ranges = []

        for i in range(parts):
            r_start = start_num + i * chunk

            if i == parts - 1:
                r_end = end_num
            else:
                r_end = start_num + (i + 1) * chunk - 1

            s = decimal_to_n(r_start, self.chars, self.length)
            e = decimal_to_n(r_end,   self.chars, self.length)

            ranges.append((s, e))

        return ranges


worker = Worker("10.30.56.127", 5000)
worker.start()
print("[MAIN] Worker started. Waiting for tasks...")

try:
    while worker.running:
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\n[MAIN] Ctrl+C pressed. Stopping worker...")
    worker.running = False

print("[MAIN] Exiting program.")