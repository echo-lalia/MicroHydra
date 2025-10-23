"""Simple interface for saving/loading small pieces of data from flash."""
import os
import json


class Preferences:
    def __init__(self, domain: str):
        self.domain = domain
        self.data = {}
        try:
            with open(f"/prefs/{domain}.json") as f:
                self.data.update(json.loads(f.read()))
        except OSError:
            pass


    def __getitem__(self, name: str):
        return self.data[name]


    def __contains__(self, name: str) -> bool:
        return (name in self.data)


    def get(self, name: str, default=None):
        """Fetch an item from preferences, and return `default` if that item doesn't exist.."""
        return self.data.get(name, default)


    def __setitem__(self, name: str, val):
        self.data[name] = val


    def save(self):
        """Save the preference data."""
        if "prefs" not in os.listdir("/"):
            os.mkdir("/prefs")
        with open(f"/prefs/{self.domain}.json", "w") as f:
            f.write(json.dumps(self.data))

