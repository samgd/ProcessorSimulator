from procsim.back_end.result import Result
from procsim.instructions.instruction import Instruction

class SubI(Instruction):
    """Subtract immediate instruction.

    Args:
        rd: Destination Register name.
        r1: Source 1 Register name.
        imm: Immediate value.
    """

    def __init__(self, rd, r1, imm):
        super().__init__()
        self.rd = rd
        self.r1 = r1
        self.imm = imm

    def execute(self, register_file):
        """Execute subi and return the Result.

        Note: This does _not_ write to the Result to the RegisterFile.

        Args:
            register_file: A RegisterFile to read Register values from.

        Returns:
            The Result.
        """
        return Result(self.rd, register_file[self.r1] - self.imm)

    def __repr__(self):
        return 'SubI(%r, %r, %r)' % (self.rd, self.r1, self.imm)

    def __str__(self):
        return 'subi %s %s %s' % (self.rd, self.r1, self.imm)
