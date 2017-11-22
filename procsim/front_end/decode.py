from procsim.pipeline_stage import PipelineStage
import procsim.front_end.instructions as ins

class Decode(PipelineStage):
    """Decode decodes an Instruction string to an Instruction.

    Args:
        reservation_station: ReservationStation to feed results to.

    Attributes:
        DELAY: Number of clock cycles required to decode an Instruction.
            (default 1)
    """

    def __init__(self, reservation_station):
        super().__init__()
        self.res_stat = reservation_station
        self.DELAY = 1
        self.current_inst = None
        self.current_timer = 0
        self.future_inst = None
        self.future_timer = 0

    def feed(self, instruction):
        """Feed the Decode stage an Instruction string to decode.

        Args:
            instruction: A dictionary containing at least the instruction_str
            key with value being a string to decode.
        """
        assert self.future_inst is None, 'Decode fed when full'
        self.future_inst = instruction
        self.future_timer = max(0, self.DELAY - 1)

    def full(self):
        """Return True if the Decode stages future state is non-empty."""
        return self.future_inst is not None

    def operate(self):
        """Feed decoded Instruction to the ReservationStation if possible."""
        if self.current_inst and self.current_timer == 0 and not self.res_stat.full():
            instruct = _decode(self.current_inst)
            self.res_stat.feed(instruct)

    def trigger(self):
        """Advance the state of the Decode stage and init a new future state."""
        # Update current state.
        self.current_inst = self.future_inst
        self.current_timer = self.future_timer
        # Initialize future state.
        if self.current_inst is None or self.current_timer == 0:
            self.future_inst = None
            self.future_timer = 0
        else:
            self.future_inst = self.current_inst
            self.future_timer = max(0, self.current_timer - 1)

def _decode(instruction):
    """Return the instruction string decoded into an Instruction.

    Args:
        instruction: Dictionary containing instruction_str to decode.

    Returns:
        Instruction if instruction_str is valid.
    """
    # Very naive parser.
    gen_ins = {'add': lambda args: ins.Add(args[0], args[1], args[2]),
               'addi': lambda args: ins.AddI(args[0], args[1], int(args[2])),
               'sub': lambda args: ins.Sub(args[0], args[1], args[2]),
               'subi': lambda args: ins.SubI(args[0], args[1], int(args[2])),
               'mul': lambda args: ins.Mul(args[0], args[1], args[2]),
               'muli': lambda args: ins.MulI(args[0], args[1], int(args[2])),
               'ldr': lambda args: ins.Load(args[0], args[1]),
               'str': lambda args: ins.Store(args[0], args[1]),
               'j': lambda args: ins.Jump(int(args[0])),
               'blth': lambda args: ins.Blth(args[0], args[1], int(args[2]))}
    fields = instruction['instruction_str'].split(' ')
    try:
        front_end_ins = gen_ins[fields[0]](fields[1:])
        if fields[0] == 'blth':
            front_end_ins.branch_info = instruction['branch_info']
        return front_end_ins
    except:
        raise ValueError('unknown instruction %r' % instruction)
