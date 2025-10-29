"""A block of MHConditional statements."""
from mhcontrol import MHControl



class MHSingleStatement:
    """Hold a single conditional statement."""

    def __init__(self, *data: list[str]):
        """Initialize the single statement with `data`."""
        assert(len(data) >= 2)  # noqa: S101
        assert(MHControl.has_mh_control_statement(data[0]))  # noqa: S101

        self.control = data[0]
        self.conditional_type = MHControl.extract_type(self.control)
        self.end_control = data[-1] if MHControl.has_mh_end_if(data[-1]) else None
        self.content = data[1:-1]











