"""Class for recording and undoing/redoing editor actions."""
from collections import namedtuple


_UNDO_STEPS = const(5)


Step = namedtuple("Step", "action", "value", "cursor_x", "cursor_y")



class UndoManager:
    """Record and replay editor actions."""


    def __init__(self, editor, cursor):
        self.editor = editor
        self.cursor = cursor
        self.undo_steps = []
        self.redo_steps = []


    def record(self, action: str, value: str):
        """Record an undo step."""
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
        """Do both undo and redo actions."""
        if not source_record:
            return

        # Get the next undo/redo step to perform
        recorded_step = source_record.pop(-1)

        # Move cursor to correct location
        self.cursor.x = recorded_step.cursor_x
        self.cursor.y = recorded_step.cursor_y
        self.cursor.clamp_to_text(self.editor.lines)

        # perform recorded action,
        # inverting it into a new undo/redo step in the dest_record.
        if recorded_step.action == "insert":
            # Insert each character
            for char in undo_step.value:
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
        
