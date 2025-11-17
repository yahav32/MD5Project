import socket
import hashlib 
import string
import select
import time

length = 3
used_key = string.ascii_lowercase + string.digits + "!@#$%^&*"


def next_block_range(start_block, chars, length):
    index = chars.index(start_block)

    from_pass = start_block * length

    if index == len(chars) - 1:
        to_pass = chars[-1] * length
        next_block = None
    else:
        next_block = chars[index + 1]
        to_pass = next_block * length

    return from_pass, to_pass, next_block


HOST = '0.0.0.0'
PORT = 5000
target_pass = "!!!"
target_hash = hashlib.md5(target_pass.encode()).hexdigest()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
active_soc = [server_socket]
print(f"Server listening on {HOST}:{PORT}")

# conn, addr = server_socket.accept()
# print(f"Client connected from {addr}")

curr_block = used_key[0]
next_block = ""
while True:
    open_requests, open_outputs, open_exept = select.select(active_soc,[],[])
    time.sleep(1)

    for req in open_requests:
        if next_block != None and req == server_socket:
            new_soc, add = req.accept()
            active_soc.append(new_soc)
            from_pass, to_pass, next_block = next_block_range(curr_block, used_key, length)
            msg = f"{target_hash} {from_pass} {to_pass} {used_key}"
            print(f"[DEBUG] {msg}")
            new_soc.send(msg.encode())
            print("Server sent:", msg)
            print(f"Got connection from ip: {add[0]}")
        else:
            data = req.recv(1024).decode()
            password, status = data.split(" ")
            

            if status == "303":
                print("PASSWORD FOUND:", password)
                for r in active_soc:
                    req.send("301".encode())
                    active_soc.remove(req)
                    req.close()
            elif status == "404":
                if next_block is None:
                    print("FINISHED ALL RANGES — password NOT found.")
                    req.send("301".encode())
                    active_soc.remove(req)
                    req.close()
                    print("end communication")
                else:
                    from_pass, to_pass, next_block = next_block_range(curr_block, used_key, length)
                    msg = f"{target_hash} {from_pass} {to_pass} {used_key}"
                    req.send(msg.encode())
                    print("Server sent:", msg)
            curr_block = next_block

active_soc = None
server_socket.close()
