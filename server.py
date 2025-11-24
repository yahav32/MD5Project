import socket
import hashlib 
import string
import select
import time
from conversions import n_to_decimal, decimal_to_n
from Constants import Constants
import threading 
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
        self.shutdown_event = threading.Event()  # Event to signal server shutdown
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
    def ping(self):
        while not self.shutdown_event.is_set():
            dead_sockets = []

            # Locking for thread-safety
            with threading.Lock():
                for soc in self.active_soc[1:]:  # Start from index 1 to skip the server socket
                    if soc is None:
                        continue

                    try:
                        soc.sendall("ping".encode())
                        reply = soc.recv(1024).decode()
                        print(reply)
                        print(f"[REPLY] {reply}")
                        if reply != "pong":
                            dead_sockets.append(soc)

                    except socket.error as e:
                        print(f"Socket error: {e}")
                        dead_sockets.append(soc)
                    except Exception as e:
                        print(f"Error while pinging socket: {e}")
                        dead_sockets.append(soc)

            # Remove dead sockets safely after checking all
            with threading.Lock():
                for ds in dead_sockets:
                    print(f"Removing dead client {ds}")
                    if ds in self.active_soc:
                        self.active_soc.remove(ds)
                        ds.close()

            if not self.shutdown_event.is_set(): time.sleep(Constants.MIN * Constants.SEC)

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.HOST, self.PORT))
        server_socket.listen(4)
        self.active_soc = [server_socket]
        print(f"Server listening on {self.HOST}:{self.PORT}")
        index = 0
        ping_thread = threading.Thread(target=self.ping, args=())
        ping_thread.start()
        while True:
            open_requests, open_outputs, open_exept = select.select(self.active_soc,[],[])
            time.sleep(1)
            for req in open_requests:
                if req == server_socket:
                    if len(self.active_soc) - 1 >= Constants.CLIENT_NUM:
                        temp_soc, addr = server_socket.accept()
                        print("SERVER FULL")
                        temp_soc.send("SERVER_FULL".encode())
                        temp_soc.close()
                        break
                    else:
                        try:
                            new_soc, add = req.accept()
                            self.active_soc.append(new_soc)
                            from_pass, to_pass = self.chunks[index]
                            msg = f"{self.target_hash} {from_pass} {to_pass} {self.used_key}"
                            new_soc.send(msg.encode())
                            print("Server sent:", msg)
                            print(f"Got connection from ip: {add[0]}")
                        except IndexError as e:
                            print(f"index out of range {e}")
                else:
                    try:
                        data = req.recv(1024).decode()
                        print(data)
                    except:
                        print("ERROR DATA")
                    try:
                        password, status = data.split(" ")
                    except:
                        print("INVALID PASSWORD PROTOCOL SENT")
                        break

                    if status == "303":  # Password found
                        print("PASSWORD FOUND:", password)

                        req.send("301".encode()) 
                        self.active_soc.remove(req)  

                        for r in self.active_soc[1:]: 
                            try:
                                r.send("301".encode())  
                                r.close()  
                                self.active_soc.remove(r) 
                            except Exception as e:
                                print(f"Error closing client {r}: {e}")
                        self.shutdown_event.set()
                        server_socket.close()
                        print("Server has shut down.")
                        return
                    elif status == "404":
                        if index < len(self.chunks):
                        # send next chunk
                            from_pass, to_pass = self.chunks[index]
                            msg = f"{self.target_hash} {from_pass} {to_pass} {self.used_key}"
                            req.send(msg.encode())
                            print("Server sent:", msg)
                            index += 1 
                        else:
                            try:
                                from_pass, to_pass = self.chunks[index]
                                msg = f"{self.target_hash} {from_pass} {to_pass} {self.used_key}"
                                req.send(msg.encode())
                                print("Server sent:", msg)
                            except:
                                print("Index out of range")
                index += 1
                
passw = "$d67ad"
mng = Manager(passw)
mng.start_server()



