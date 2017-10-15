from procsim.instructions.instruction import Instruction

class Jump(Instruction):
    """Jump instruction.

    Args:
        imm: Immediate address to Jump to.
    """

    def __init__(self, imm):
        self.imm = imm

    def __repr__(self):
        return 'Jump(%r)' % self.imm