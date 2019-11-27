#!/usr/bin/env python3
# portid.py: Static service identifier using port number
#
# author: antipatico - https://github.com/antipatico
# 2019 - All wrongs reversed.

"""Static service identifier using port number

Usage:
    portid id PORT [-y]
    portid list [-r] [SERVICE] [-y] 
    portid update-db [-y]
    portid -h

Commands:
    id              List all the services using port number PORT.
    list            Retrieve a list of services and used ports matching SERVICE,
                    if SERVICE is not provided, list all services.
    update-db       Update database files (ports.json, services.json,
                    0fun-ports.json and 0fun-services.json).

Options:
    PORT            The port number you want to identify (must be between 0 and
                    65535).
    SERVICE         Filter ports by the service name or description.
    -r, --regex     Treat SERVICE as a regex.
    -y, --yes       Do not prompt for confirmation when download is needed.
    -h, --help      Shows this help message.

Author:
    antipatico - https://github.com/antipatico
    2019 - All wrongs reversed.
"""
import requests
from docopt import docopt
from tqdm import tqdm
import re
from pathlib import Path
import json


class Portid:
    __disclaimer = """\
You are trying to update the internal database.

Proceeding will result in the loss of the old data. Moreover, you are going to
download a json file, via https from github. Portid will later use that file
to identify and list services. Eventual bugs in json deserialization, or in the
requests module may cause a command execution.

By continuing you are trusting the author of this tool (antipatico), the author
of ports.json and services.json (silverwind), request's module developers,
github, python's developers, locally installed Certiface Authorities, and,
unless you are running this on Linux From Scratch, the maintainers of your
distribution.

Are you sure do you want to continue (y/N)? \
"""
    __DB_NAME = "portid.json"
    __UPDATE_URL = "https://raw.githubusercontent.com/antipatico/portid/master/portid.json"
    version = 0.1
    localpath = Path.home() / ".local" / "share" / "portid"

    

    def __init__(self, args = {}):
        self.args_yes = args["--yes"]
        self.args_regex = args["--regex"]
        if not self.localpath.exists():
            self.updateDatabase()
    
    @classmethod
    def __promptConfirmation(cls):
        return input(cls.__disclaimer).lower() in ["y", "yes"]
    
    # inspired from https://gist.github.com/wy193777/0e2a4932e81afc6aa4c8f7a2984f34e2
    @classmethod
    def __downloadFile(cls, url, dst):
        file_size = int(requests.head(url).headers['Content-Length'])
        header = {"User-Agent": f"portid.py {cls.version}"}
        pbar = tqdm(
            total=file_size, initial=0,
            unit='B', unit_scale=True, desc=url.split('/')[-1])
        req = requests.get(url, headers=header, stream=True)
        if req.status_code != 200:
            raise RuntimeError(f"Response code was {req.status_code} for {url}.")
        with(dst.open('wb')) as f:
            for chunk in req.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(1024)
        pbar.close()
        return file_size 

    def updateDatabase(self, yes=False):
        yes = self.args_yes if self.args_yes else yes
        if yes or self.__promptConfirmation():
            print("Updating database...")
            self.localpath.mkdir(exist_ok=True)
            self.__downloadFile(self.__UPDATE_URL, self.localpath / self.__DB_NAME)

    def identify(self, port):
        if int(port) < 0 or int(port) > 65535:
            raise ValueError("Port must be between 0 and 65535")
        db = json.load((self.localpath / self.__DB_NAME).open("r"))
        protocols = db["ports"].get(port, [])
        services = []
        for proto in protocols:
            for svc in db["ports"][port][proto]:
                if svc["name"] not in services:
                    services.append(svc["name"])
                print(f"{port}/{proto} {svc['name']} \"{svc['description']}\"")


def main():
    args = docopt(__doc__, version=f"portid.py {Portid.version}")
    portid = Portid(args)
    if args["update-db"]:
        portid.updateDatabase()
    if args["id"]:
        portid.identify(args["PORT"])

if __name__ == "__main__":
    main()
