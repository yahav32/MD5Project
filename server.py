import socket
import hashlib 
import string


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


HOST = '127.0.0.1'
PORT = 5000
target_pass = "!!!"
target_hash = hashlib.md5(target_pass.encode()).hexdigest()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"Server listening on {HOST}:{PORT}")

conn, addr = server_socket.accept()
print(f"Client connected from {addr}")

curr_block = used_key[0]

while True:
    from_pass, to_pass, next_block = next_block_range(curr_block, used_key, length)
    if next_block is None:
        print("FINISHED ALL RANGES — password NOT found.")
        conn.send("DONE".encode())
        break
    

    msg = f"HASH {target_hash} from {from_pass} to {to_pass} chars {used_key}"
    conn.send(msg.encode())
    print("Server sent:", msg)

    data = conn.recv(1024).decode()
    password, status = data.split(" ")

    if status == "301":
        print("PASSWORD FOUND:", password)
        conn.send("DONE".encode())
        break
    
    curr_block = next_block

conn.close()
server_socket.close()
print("Server closed.")

