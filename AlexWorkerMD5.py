import hashlib
import string
import threading
from socket import socket
import time

class Worker:

    def __init__(self, ip, port):
        print(f"[INIT] Creating worker...")
        self.soc = socket()
        self.soc.connect((ip, port))
        print(f"[CONNECTED] Connected to manager at {ip}:{port}")
        self.running = True
        self.job_active = False

    def start(self):
        print("[START] Starting listener thread...")
        listen_thread = threading.Thread(target=self.listen, daemon=True)
        listen_thread.start()

    def listen(self):
        print("[LISTEN] Listening for messages...")
        while self.running:
            try:
                data = self.soc.recv(1024)
                print(data.decode())
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
                print("[PING] Received ping, sending pong")
                self.soc.sendall(b"pong")
                continue

            if not self.job_active:
                try:
                    target_hash, start, end, chars = msg.split()
                except ValueError:
                    print("[WARN] Malformed message. Ignoring.")
                    continue

                print(f"[JOB] Starting job: {start} → {end}, hash={target_hash}")
                work_thread = threading.Thread(
                    target=self.do_work,
                    args=(target_hash, start, end, chars),
                    daemon=True
                )
                work_thread.start()

    def do_work(self, target_hash, start, end, chars):
        self.job_active = True
        found = self.bruteforce(target_hash, start, end, chars)

        if not self.running:
            print("[CANCEL] Job canceled due to STOP.")
            self.job_active = False
            return

        if found:
            print(f"[FOUND] Match found: {found}")
            self.soc.sendall(f"{found} 303".encode())
        else:
            print("[NOT FOUND] No match in assigned range.")
            self.soc.sendall(" 404".encode())

        print("[JOB COMPLETE] Job finished.")
        self.job_active = False

    def bruteforce(self, target_hash, start, end, chars):
        chars_list = list(chars)
        index_map = {c: i for i, c in enumerate(chars_list)}
        combo = list(start)
        target = target_hash.lower()

        while self.running:
            combo_str = ''.join(combo)

            if hashlib.md5(combo_str.encode()).hexdigest() == target:
                return combo_str

            if combo_str == end:
                break

            if not self.increment(combo, chars_list, index_map):
                break

        return None

    def increment(self, combo, chars, index_map):
        i = len(combo) - 1
        while i >= 0:
            c = combo[i]
            pos = index_map[c]

            if pos + 1 < len(chars):
                combo[i] = chars[pos + 1]
                return True
            else:
                combo[i] = chars[0]
                i -= 1
        return False


worker = Worker("10.30.56.149", 5000)
worker.start()
print("[MAIN] Worker started. Waiting for tasks...")

try:
    while worker.running:
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\n[MAIN] Ctrl+C pressed. Stopping worker...")
    worker.running = False

print("[MAIN] Exiting program.")