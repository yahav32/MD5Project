import hashlib

class BruthForce:

    def __init__(self,hash,used_key):
        self.hash = hash
        self.used_key = list(used_key)
        self.index_map = {ch: i for i, ch in enumerate(self.used_key)}

    def cracker(self,from_pass,to_pass):
        password = from_pass
        flag = "301"
        while hashlib.md5(password.encode()).hexdigest() != self.hash:
            password = self.inc_key(password)
            if password == to_pass: 
                flag = "404"
                break

        return password, flag

    def inc_key(self,string):
        chars = list(string)
        i = len(chars) - 1

        while i >= 0:
            if chars[i] != self.used_key[-1]:
                index = self.index_map[chars[i]]
                chars[i] = self.used_key[index + 1]
                break
            else:
                chars[i] = self.used_key[0]
                i -= 1

        return ''.join(chars)