import aiohttp.web
from threading import Thread
import hashlib
import os

token_path = "admin.txt"
with open(token_path, "rb") as f:
    token = f.read()

path = "C:\\Users\\chris\\OneDrive - Exeter College\\Programming\\nea\\game\\resources"

amalgamate = bytes()
def hash_folder(path):
    global amalgamate
    out = {}
    for dir in sorted(os.listdir(path=path)):
        temp = f"{path}\\{dir}"
        if os.path.isdir(temp):
            out[dir] = hash_folder(temp)
        else:
            with open(temp, "rb") as f:
                myfile = f.read()
                amalgamate += myfile
                out[dir] = hashlib.sha512(myfile).hexdigest()
    return out

def hash_out():
    global hash, hashes
    hashes = hash_folder(path)
    hash = hashlib.sha512(amalgamate).hexdigest()

def verify_request(dat, hashes):
    out = {}
    for x in dat:
        if isinstance(dat, dict):
            out[x] = verify_request(dat[x], hashes[x])
        else:
            if dat[x] != hashes[x]:
                out[x] = 

async def verify(request):
    return aiohttp.web.json_response({"global": hash, "individual": hash})

async def init():
    app = aiohttp.web.Application()
    app.router.add_get("/api/bitches", bitches)
    return app

if __name__ == "__main__":
    Thread(target=edit).start()
    aiohttp.web.run_app(init(), port=19940)