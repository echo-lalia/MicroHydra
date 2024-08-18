## lib.hydra.popup

MicroHydra includes a module called `popup`, which provides some simple, common tools for displaying various UI popups and overlays. 

To use the module, you must first import it, create a display object, and create the `popup.UIOverlay` object to access its methods. 

``` Python
from lib.display import Display
from lib.hydra import popup

# create the display object first
# (Display must be initialized before UIOverlay can work)
display = Display()
# Create our overlay object
overlay = popup.UIOverlay()

# this demo creates a list of options, and allows the user to select one.
demo = overlay.popup_options(
    options = ('text entry', '2d options', 'popup message', 'error message'),
    title = "Pick a demo:"
)

# popup_options returns a string, so we can use this to select another demo to display:
if demo == 'text entry':
    # this allows the user to enter some text, and returns it as a string.
    print(overlay.text_entry(start_value='', title="Enter text:"))

elif demo == '2d options':
    # popup options also allows you to make several columns using nested lists (or tuples)
    print(overlay.popup_options(
            options = (
                ('you', 'also', 'more'),
                ('can', 'make', 'columns.'),
                ('and', 'they', 'can', 'have', 'different', 'lengths')
                ),
    ))

elif demo == 'popup message':
    # this simply displays a message on the screen, and blocks until the user clicks any button
    print(overlay.popup("This is a test"))
    
elif demo == 'error message':
    # this is exactly the same as overlay.popup, but with custom styling for an error message
    print(overlay.error("This is an error message"))
```

