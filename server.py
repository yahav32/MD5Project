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
    def __init__(self,target_pass=None,HOST=Constants.HOST,PORT=Constants.PORT,length=Constants.LENGTH,used_key=Constants.USED_KEY,client_num=Constants.CLIENT_NUM):
        self.length = length
        self.used_key = used_key
        self.HOST = HOST
        self.PORT = PORT
        self.target_pass = target_pass
        self.target_hash = hashlib.md5(target_pass.encode()).hexdigest()
        self.chunks = self.get_chunks(client_num)
    
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

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.HOST, self.PORT))
        server_socket.listen(1)
        active_soc = [server_socket]
        print(f"Server listening on {self.HOST}:{self.PORT}")
        
        while True:
            open_requests, open_outputs, open_exept = select.select(active_soc,[],[])
            time.sleep(1)
            index = 0
            for req in open_requests:
                if index < Constants.CLIENT_NUM and req == server_socket:
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
passw = "aba"
mng = Manager(passw)
mng.start_server()
        
