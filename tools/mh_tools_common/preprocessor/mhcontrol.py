"""Process and store a single line of text containing an MH preprocessor control statement."""
import re



class CONTROL_TYPES:  # noqa: N801
    """Valid mh_... preprocessor types."""

    mh_if = "mh_if"
    mh_else = "mh_else"
    mh_else_if = "mh_else_if"
    mh_end_if = "mh_end_if"

    all = {
        mh_if,
        mh_else,
        mh_else_if,
        mh_end_if,
    }



class MHControl:
    """Hold and parse a single preprocessor control statement."""

    @staticmethod
    def has_mh_if(line: str) -> bool:
        """Strictly check whether or not the given line has a valid mh_if statement."""
        if "mh_if" in line:
            if re.match(r"^[ \t]*#[ \t]?mh_if[ \t]*[\w\d \t_]+:", line):
                return True
            if line.count("#") == 1:
                print(f"Warning! the following line may have a malformed `mh_if` statement:\n{line}")
        return False


    @staticmethod
    def has_mh_include_if(line: str) -> bool:
        """Strictly check whether or not the given line has a valid mh_include_if statement."""
        if "mh_include_if" in line:
            if re.match(r"^[ \t]*#[ \t]?mh_include_if[ \t]*[\w\d \t_]+:", line):
                return True
            if line.count("#") == 1:
                print(f"Warning! the following line may have a malformed `mh_include_if` statement:\n{line}")
        return False


    @staticmethod
    def has_mh_else(line: str) -> bool:
        """Strictly check whether the line has a `# mh_else:` statement."""
        if "mh_else" in line:
            if re.match(r"^[ \t]*#[ \t]?mh_else[ \t]*:", line):
                return True
            if line.count("#") == 1 and "mh_else_if" not in line:
                print(f"Warning! the following line may have a malformed `mh_else` statement:\n{line}")
        return False


    @staticmethod
    def has_mh_else_if(line: str) -> bool:
        """Strictly check whether the line has a `# mh_else_if ... :` statement."""
        if "mh_else_if" in line:
            if re.match(r"^[ \t]*#[ \t]?mh_else_if[ \t]+[\w\d_]*[ \t]*:", line):
                return True
            if line.count("#") == 1:
                print(f"Warning! the following line may have a malformed `mh_else_if` statement:\n{line}")
        return False


    @staticmethod
    def has_mh_end_if(line: str) -> bool:
        """Strictly check whether the line has a `# mh_end_if` statement."""
        if "mh_end_if" in line:
            if re.match(r"^[ \t]*#[ \t]?mh_end_if[ \t]?(?:$|#)", line):
                return True
            if line.count("#") == 1:
                print(f"Warning! the following line may have a malformed `mh_end_if` statement:\n{line}")
        return False


    @staticmethod
    def has_mh_control_statement(line: str) -> bool:
        """Check if this line contains an mh control statement."""
        return "mh_" in line and (
            MHControl.has_mh_if(line)
            or MHControl.has_mh_end_if(line)
            or MHControl.has_mh_else(line)
            or MHControl.has_mh_else_if(line)
        )


    @staticmethod
    def extract_type(line: str) -> str:
        """Find and return the control type in the given string.

        Raises ValueError when no valid control type is found.
        """
        matches = re.findall(r"#[ \t]*(mh_[\w_]+)(?::|(?:[\w \d\t]*:?))", line)
        if matches and matches[0] in CONTROL_TYPES.all:
            return matches[0]
        raise ValueError(
            "MHControl.extract_type failed: The following line does not appear to contain a valid mh_control type"
            f" ({matches=}):\n{line}"
        )


    def __init__(self, line: str):
        """Construct an MHControl wrapping the given line."""
        self.line = line
        self.type = self.extract_type(line)



if __name__ == "__main__":
    print("Running basic MHControl tests...\n")

    def test(title: str, assertion: bool):
        """A simple little sanity testing helper."""
        print(f"Testing {title}: {'passed' if assertion else 'failed'}")

    print()
    test("mh_if", MHControl.has_mh_if("# mh_if True:"))
    test("mh_if", MHControl.has_mh_if("  #mh_if True and False:"))
    test("mh_if", not MHControl.has_mh_if("# this is not a valid mh_if line :)"))

    print()
    test("mh_else", MHControl.has_mh_else("# mh_else:"))
    test("mh_else", MHControl.has_mh_else("  #mh_else:"))
    test("mh_else", not MHControl.has_mh_else("# mh_else_if not_a_plain_else:"))
    test("mh_else", not MHControl.has_mh_else(" mh_else # malformed on purpose")) # should be malformed

    print()
    test("mh_else_if", MHControl.has_mh_else_if("# mh_else_if test:"))
    test("mh_else_if", MHControl.has_mh_else_if("  #mh_else_if False:"))
    test("mh_else_if", not MHControl.has_mh_else_if("# mh_else:"))
    test("malformed mh_else_if", not MHControl.has_mh_else_if("# mh_else_if:")) # should be malformed

    print()
    test("mh_include_if", MHControl.has_mh_include_if("# mh_include_if test:"))
    test("mh_include_if", MHControl.has_mh_include_if("  #mh_include_if  False: "))
    test("mh_include_if", not MHControl.has_mh_include_if("# mh_if:"))
    test("malformed mh_include_if", not MHControl.has_mh_include_if("# mh_include_if:")) # should be malformed

    print()
    test("extract_type", MHControl.extract_type("    # mh_if TEST:\n") == CONTROL_TYPES.mh_if)
    test("extract_type", MHControl.extract_type("# mh_else:\n") == CONTROL_TYPES.mh_else)
    test("extract_type", MHControl.extract_type("# mh_else_if TEST:") == CONTROL_TYPES.mh_else_if)
    test("extract_type", MHControl.extract_type("#mh_end_if") == CONTROL_TYPES.mh_end_if)

    try:
        MHControl.extract_type("#mh_fake test:")
    except ValueError as e:
        print("(This is expected to fail):", e)
