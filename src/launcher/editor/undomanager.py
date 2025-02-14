"""Class for recording and undoing/redoing editor actions."""
from collections import namedtuple


_UNDO_STEPS = const(5)


# Container for detailing undo/redo steps to be replayed.
Step = namedtuple("Step", ("action", "value", "cursor_x", "cursor_y"))



class UndoManager:
    """Record and replay editor actions."""

    def __init__(self, editor, cursor):
        """Initialize the undo manager with the editor and main cursor."""
        self.editor = editor
        self.cursor = cursor
        self.undo_steps = []
        self.redo_steps = []


    def record(self, action: str, value: str):
        """Record an undo step."""
        last_undo_step = self.undo_steps[-1] if self.undo_steps else None

        # If this action is the same as the last action, we may be able to combine them.
        if (last_undo_step is not None and action == last_undo_step.action
            # But only if the cursor has not moved:
            and last_undo_step.cursor_y == self.cursor.y
            and ((action == "insert" and last_undo_step.cursor_x == self.cursor.x + 1)
            or (action == "backspace" and last_undo_step.cursor_x == self.cursor.x - 1))
            # And only if there are no line breaks in either step:
            and "\n" not in value and "\n" not in last_undo_step.value):

            self.undo_steps[-1] = Step(
                action,
                # append or prepend depending on the action we are doing:
                last_undo_step.value + value if action == "backspace" else value + last_undo_step.value,
                self.cursor.x,
                self.cursor.y,
            )

        # Otherwise, just add a new undo step like normal:
        else:
            self.undo_steps.append(
                Step(action, value, self.cursor.x, self.cursor.y),
            )

        # Maintain undo step max length
        if len(self.undo_steps) > _UNDO_STEPS:
            self.undo_steps.pop(0)
        # Don't keep outdated redo-steps
        if self.redo_steps:
            self.redo_steps = []


    def _undo_redo(self, source_record: list, dest_record: list):
        """Do both undo and redo actions.

        source_record is the list with the action to replay,
        dest_record is the other list, where the replayed action will be moved.
        (ex: when undoing, source_record = self.undo_steps, and dest_record = self.redo_steps).
        """
        if not source_record:
            # Do nothing if there are no undo/redo steps to replay.
            return

        # Get the next undo/redo step to perform
        recorded_step = source_record.pop(-1)

        # Move cursor to correct/recorded location
        self.cursor.x = recorded_step.cursor_x
        self.cursor.y = recorded_step.cursor_y
        self.cursor.clamp_to_text(self.editor.lines)

        # perform recorded action,
        # inverting it into a new undo/redo step in the dest_record.
        if recorded_step.action == "insert":
            # Insert each character
            for char in recorded_step.value:
                self.editor.lines.insert(char, self.cursor)
            # Create a new redo action that reverses this change
            dest_record.append(
                Step(
                    "backspace",
                    recorded_step.value,
                    self.cursor.x,
                    self.cursor.y,
                ),
            )

        else:  # action == "backspace"
            # Backspace each character
            for char in recorded_step.value:
                self.editor.lines.backspace(self.cursor)
            # Create a new redo action that reverses this change
            dest_record.append(
                Step(
                    "insert",
                    recorded_step.value,
                    self.cursor.x,
                    self.cursor.y,
                ),
            )


    def undo(self):
        """Undo the previous action, converting the undo step into a redo step."""
        self._undo_redo(self.undo_steps, self.redo_steps)


    def redo(self):
        """Redo the last undo, converting the redo into an undo."""
        self._undo_redo(self.redo_steps, self.undo_steps)
