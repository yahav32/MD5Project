import socket
import hashlib 
import string
import select
import time
from conversions import n_to_decimal, decimal_to_n
from Constants import Constants
"""
Need to implement\check:
- Ping message to check if client is alive
- Handle client disconnection
- Check if the communication functions well after the changes
"""
class Manager:
    def __init__(self,target_pass=None,HOST=Constants.HOST,PORT=Constants.PORT,used_key=Constants.USED_KEY,client_num=Constants.CLIENT_NUM):
        self.length = len(target_pass)
        self.used_key = used_key
        self.HOST = HOST
        self.PORT = PORT
        self.target_pass = target_pass
        self.target_hash = hashlib.md5(target_pass.encode()).hexdigest()
        self.chunks = self.get_chunks(client_num)
        print(self.chunks)
    
    def get_chunks(self,how_many_chunks):
        n = len(self.used_key)**self.length
        chunk_size = n // how_many_chunks 
        lst = []
        for i in range(how_many_chunks):
            start = i * chunk_size
            if i == how_many_chunks - 1:
                end = n - 1
            else:
                end = (i + 1) * chunk_size
            lst.append((decimal_to_n(start,self.used_key,self.length),decimal_to_n(end,self.used_key,self.length)))
        return lst
    def ping(self, active_soc):
        dead_sockets = []

        for soc in active_soc:
            if soc is None or soc is active_soc[0]:
                continue
            try:
                soc.sendall("ping".encode())
                reply = soc.recv(1024).decode()

                if reply != "pong":
                    dead_sockets.append(soc)

            except Exception:
                dead_sockets.append(soc)


        for ds in dead_sockets:
            print(f"Removing dead client {ds}")
            if ds in active_soc:
                active_soc.remove(ds)
                ds.close()

        time.sleep(Constants.MIN*Constants.SEC)

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.HOST, self.PORT))
        server_socket.listen(4)
        active_soc = [server_socket]
        print(f"Server listening on {self.HOST}:{self.PORT}")
        index = 0
        thread = threading.Thread(target=self.ping, args=(active_soc,))
        thread.start()
        thread.join()
        while True:
            open_requests, open_outputs, open_exept = select.select(active_soc,[],[])

            time.sleep(1)
            
            for req in open_requests:
                if req == server_socket:
                    if len(active_soc) - 1 >= Constants.CLIENT_NUM:
                        temp_soc, addr = server_socket.accept()
                        temp_soc.send("SERVER_FULL".encode())
                        temp_soc.close()
                        continue
                    else:
                        new_soc, add = req.accept()
                        active_soc.append(new_soc)
                        from_pass, to_pass = self.chunks[index]
                        msg = f"{self.target_hash} {from_pass} {to_pass} {self.used_key}"
                        new_soc.send(msg.encode())
                        print("Server sent:", msg)
                        print(f"Got connection from ip: {add[0]}")
                else:
                    data = req.recv(1024).decode()
                    print(data)
                    password, status = data.split(" ")
                    

                    if status == "303":
                        print("PASSWORD FOUND:", password)
                        for r in active_soc:
                            req.send("301".encode())
                            active_soc.remove(req)
                            req.close()
                    elif status == "404":
                        if index == Constants.CLIENT_NUM is None:
                            print("FINISHED ALL RANGES — password NOT found.")
                            req.send("301".encode())
                            active_soc.remove(req)
                            req.close()
                            print("end communication")
                        else:
                            from_pass, to_pass = self.chunks[index]
                            msg = f"{self.target_hash} {from_pass} {to_pass} {self.used_key}"
                            req.send(msg.encode())
                            print("Server sent:", msg)
                index += 1
passw = "&*a"
mng = Manager(passw)
mng.start_server()
        




