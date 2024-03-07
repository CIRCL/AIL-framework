import json
import requests
import subprocess
import re
import os
import shutil
from time import sleep
from typing import List, Optional
from pathlib import Path

BUILD_PATH = "/opt/ailbuilder/build"

class Repo:
    """Base class for repository tracking and update checking."""

    def __init__(self, id: str, args: List[str], name: str, outputdir: str) -> None:
        self.id = id
        self.args = args
        self.name = name
        self.outputdir = outputdir
        self.last_seen_update = None

    def _check_for_new_update(self) -> bool:
        latest_update = self._get_latest_update()
        if latest_update and (latest_update != self.last_seen_update):
            print(f"New update found for {self.id}")
            self.last_seen_update = latest_update
            return True
        return False

    def _get_latest_update(self):
        raise NotImplementedError
    
    def _save_state(self):
        try:
            with open(f'{BUILD_PATH}/systemd/state.json', 'r') as file:
                states = json.load(file)
        except FileNotFoundError:
            states = {}

        states[self.id] = self.last_seen_update

        with open(f'{BUILD_PATH}/systemd/state.json', 'w') as file:
            json.dump(states, file)
        
    def load_state(self):
        try:
            with open(f'{BUILD_PATH}/systemd/state.json', 'r') as file:
                states = json.load(file)
        except FileNotFoundError:
            states = {}

        self.last_seen_update = states.get(self.id, None)

    def build(self) -> None:
        if self._check_for_new_update():
            try:
                cmd = [f'{BUILD_PATH}/build.sh'] + self.args + ["-o", self.outputdir]
                print(f"Running {cmd}")
                result = subprocess.run(cmd, check=False)
                if result.returncode != 0:
                    print(f"Failed to run {cmd} for {self.id}")
                    return
                most_recent_dir = max((d for d in Path(self.outputdir).iterdir() if d.is_dir()), key=os.path.getctime, default=None)
                relative_path = most_recent_dir.relative_to(Path(self.outputdir))
                if os.path.exists(f"{self.outputdir}/latest_{self.name}"):
                    os.remove(f"{self.outputdir}/latest_{self.name}")
                os.symlink(relative_path, f"{self.outputdir}/latest_{self.name}")
                print(f"Created symlink {self.outputdir}/latest_{self.name} to {relative_path}")
                self._save_state()
            except Exception as e:
                print(f"Failed to run {cmd} for {self.id}: {e}")

    def cleanup(self, num_to_keep: int) -> None:
        files = os.listdir(self.outputdir)
        repo_images = [f for f in files if f.startswith(self.name)]
        if len(repo_images) > num_to_keep:
            repo_images.sort(key=lambda x: os.path.getmtime(os.path.join(self.outputdir, x)))
            for image in repo_images[:-num_to_keep]:
                shutil.rmtree(os.path.join(self.outputdir, image))

class GitHub(Repo):
    """Class for tracking GitHub repositories."""

    def __init__(self, id: str, mode: str, args: List[str], name: str, outputdir: str) -> None:
        super().__init__(id, args, name, outputdir)
        self.mode = mode

    def _get_latest_update(self) -> Optional[str]:
        print(f"Fetching {self.mode} for {self.id}")
        url=f'https://api.github.com/repos/{self.id}/{self.mode}'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()[0]['sha']
        else:
            print(f"Failed to fetch {self.mode} for {self.id}")
            return None

class APT(Repo):
    """Class for tracking APT packages."""

    def __init__(self, id: str, args: List[str], name: str, outputdir: str) -> None:
        super().__init__(id, args, name, outputdir)

    def _get_latest_update(self) -> Optional[str]:
        try:
            cmd = ["apt-cache", "policy", self.id]
            print (f"Running {cmd}")
            output = subprocess.check_output(cmd).decode('utf-8')
            match = re.search(r'Candidate: (\S+)', output)
            if match:
                return match.group(1)
            else:
                return None
        except:
            return None

def main():
    with open(f'{BUILD_PATH}/conf/tracker.json') as f:
        config = json.load(f)

    repos = []
    for repo in config["github"]:
        repos.append(GitHub(repo["id"], repo["mode"], repo["args"], repo["name"], config["outputdir"]))

    aptpkg = []
    for package in config["apt"]:
        aptpkg.append(APT(package["id"], package["args"], package["name"], config["outputdir"]))
    
    for repo in repos + aptpkg:
        if config["sign"]:
            repo.args.append("-s")
        repo.load_state()

    while True:
        for repo in repos:
            repo.build()
            repo.cleanup(num_to_keep=3)
        for package in aptpkg:
            package.build()
            repo.cleanup(num_to_keep=3)
        sleep(config["check_interval"])
    
if __name__ == "__main__":
    main()
