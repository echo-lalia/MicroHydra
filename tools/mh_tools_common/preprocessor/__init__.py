"""MicroHydra preprocessor module.

File data structure can be visualised like this:

FileDataBlock(
    "Data...",
    ConditionalStatementBlock(
        MHStatement(
            MHControl("# mh_if TDECK:"),
            FileDataBlock(),
            None, # optional
        ),
        MHStatement(
            MHControl("# mh_else:"),
            FileDataBlock(),
            MHControl("# mh_end_if"),
        ),
    ),
    "Data...",
)
"""

from .mhcontrol import MHControl
from .datablock import DataBlock


