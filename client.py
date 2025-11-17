import socket
from bruthForce import BruthForce
HOST = '127.0.0.1'
PORT = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))


while True:
    data = client_socket.recv(1024).decode()
    if data == "DONE":
        print("Client: DONE received, closing connection.")
        break

    print(f"Client gets {data}")
    HASH, FROM, TO, USED_KEY = (data.split(" "))[1::2]
    print(f"[DEBUG]: {HASH}, {FROM}, {TO}, {USED_KEY}")

    bruthforcer = BruthForce(hash=HASH,used_key=USED_KEY)
    password,status = bruthforcer.cracker(from_pass=FROM,to_pass=TO)
    client_socket.sendall(f"{password} {status}".encode())

    if status == "301":
        print("Client: PASSWORD FOUND, closing connection.")
        break



client_socket.close()
