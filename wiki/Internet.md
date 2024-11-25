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

I'm not completely certain of the most reliable way to work around these issues, but here's an example connection funciton that tries to do so:  
```Py
def connect_wifi():
    """Connect to the configured WiFi network."""
    TERM.print(I18N["Enabling wifi..."])

    if not NIC.active():
        NIC.active(True)

    if not NIC.isconnected():
        # tell wifi to connect (with FORCE)
        while True:
            try:  # keep trying until connect command works
                NIC.connect(CONFIG['wifi_ssid'], CONFIG['wifi_pass'])
                break
            except OSError as e:
                TERM.print(f"Error: {e}")
                time.sleep_ms(500)

        # now wait until connected
        attempts = 0
        while not NIC.isconnected():
            TERM.print(f"connecting... {attempts}")
            time.sleep_ms(500)
            attempts += 1

    TERM.print(I18N["Connected!"])
```



## Getting Data From the Internet

MicroPython provides a lower-level [`socket`](https://docs.micropython.org/en/latest/library/socket.html#module-socket) module, but the easiest way to make internet requests in most cases is to use the [`requests`](https://github.com/micropython/micropython-lib/tree/e4cf09527bce7569f5db742cf6ae9db68d50c6a9/python-ecosys/requests) module.



