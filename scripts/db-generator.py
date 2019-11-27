#!/usr/bin/env python3

import requests
from pathlib import Path
from tqdm import tqdm

import tempfile
import json

portsjsonurl = "https://raw.githubusercontent.com/silverwind/port-numbers/master/ports.json"

# inspired from https://gist.github.com/wy193777/0e2a4932e81afc6aa4c8f7a2984f34e2
def downloadFile(url, dst):
    file_size = int(requests.head(url).headers['Content-Length'])
    header = {"User-Agent": f"portid gen-db script"}
    pbar = tqdm(
        total=file_size, initial=0,
        unit='B', unit_scale=True, desc=url.split('/')[-1])
    req = requests.get(url, headers=header, stream=True)
    if req.status_code != 200:
        raise RuntimeError(f"Response code was {req.status_code} for {url}.")
    for chunk in req.iter_content(chunk_size=1024):
        if chunk:
            dst.write(chunk)
            pbar.update(1024)
    pbar.close()
    return file_size


def main():
    portsfile = tempfile.NamedTemporaryFile("w+b")
    downloadFile(portsjsonurl, portsfile)
    portsfile.seek(0)
    ports = json.loads(portsfile.read().decode())
    portsfile.close()

    db = {"ports" : {}, "services": [] }
    for k,v in ports.items():
        port = int(k.split("/")[0])
        protocol = k.split("/")[1]
        name = v["name"]
        description = v.get("description", "")

        if name == "":
            continue

        if not db["ports"].get(port):
            db["ports"][port] = {}
        if not db["ports"][port].get(protocol):
            db["ports"][port][protocol] = []
        db["ports"][port][protocol].append({"name": name, "description": description})
        
        search = [s for s in db["services"] if s["name"] == name and s["description"] == description]
        if len(search) < 1:
            db["services"].append({
                "name": name,
                "description": description,
                "ports": { protocol: [port] }
            })
        else:
            svc = search[0]
            if not svc["ports"].get(protocol):
                svc["ports"][protocol] = [port]
            else:
                svc["ports"][protocol].append(port)
    json.dump(db, open("portid.json", "w"))
if __name__ == "__main__":
    main()
