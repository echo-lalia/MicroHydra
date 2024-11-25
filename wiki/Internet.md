## Connecting to the internet

MicroPython's built-in [`network`](https://docs.micropython.org/en/latest/library/network.WLAN.html#network.WLAN) module makes it easy to connect to the internet on an ESP32 device.  
You can also use MicroHydra's `hydra.config` module to easily access the user-set wifi configuration.

Here's a really simple script that connects to WiFi using these:

```Py
import network
from lib.hydra.config import Config

# Create the object for network control
nic = network.WLAN(network.STA_IF)
# Get the MicroHydra config
config = Config()

# Turn on the WiFi
if not nic.active():
    nic.active(True)

# Connect to the user-set wifi network
if not nic.isconnected():
    nic.connect(
        config['wifi_ssid'],
        config['wifi_pass'],
    )
```

The `nic.connect` command doesn't block while waiting for a connection. So, your script will need to wait until the connection is made.  
There can also be some unpredictable errors raised when calling the connection method.

Here's an example connection function that tries to handle these potential obsticals *(similar to the function used in `getapps.py`)*:  
```Py
import time
import network
from lib.hydra.config import Config


nic = network.WLAN(network.STA_IF)
config = Config()


def connect_wifi():
    """Connect to the configured WiFi network."""
    print("Enabling wifi...")

    if not nic.active():
        nic.active(True)

    if not nic.isconnected():
        # tell wifi to connect (with FORCE)
        while True:
            try:  # keep trying until connect command works
                nic.connect(config['wifi_ssid'], config['wifi_pass'])
                break
            except OSError as e:
                print(f"Error: {e}")
                time.sleep_ms(500)

        # now wait until connected
        attempts = 0
        while not nic.isconnected():
            print(f"connecting... {attempts}")
            time.sleep_ms(500)
            attempts += 1

    print("Connected!")

connect_wifi()
```



## Getting Data From the Internet

MicroPython provides a lower-level [`socket`](https://docs.micropython.org/en/latest/library/socket.html#module-socket) module, but the easiest way to make internet requests in most cases is to use the other built-in [`requests`](https://github.com/micropython/micropython-lib/tree/e4cf09527bce7569f5db742cf6ae9db68d50c6a9/python-ecosys/requests) module.

Here's a super simple example that fetches a random cat fact from meowfacts.herokuapp.com:


```Py
import json
import requests

# Make a request to meowfacts
response = requests.get("https://meowfacts.herokuapp.com/")
# Verify that the request worked
if response.status_code != 200:
    raise ValueError(f"Server returned {response.status_code}.\n{response.reason}")

# Decode the returned JSON data, and extract the random fact
fact = json.loads(response.content)['data'][0]
print(fact)
```
