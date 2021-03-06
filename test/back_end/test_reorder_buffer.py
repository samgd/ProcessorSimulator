import math
import random
import unittest

from procsim.back_end.load_store_queue import LoadStoreQueue
from procsim.back_end.reorder_buffer import ReorderBuffer
from procsim.back_end.reservation_station import ReservationStation
from procsim.back_end.result import Result
from procsim.branch.branch_info import BranchInfo
from procsim.front_end.instructions.addi import AddI
from procsim.front_end.instructions.add import Add
from procsim.front_end.instructions.blth import Blth
from procsim.memory import Memory
from procsim.register_file import RegisterFile
from test.back_end.bus_log import BusLog
from test.feed_log import FeedLog
from test.flushable_log import FlushableLog

class TestReorderBuffer(unittest.TestCase):

    def setUp(self):
        self.n_gpr_registers = 31
        self.rf = RegisterFile(self.n_gpr_registers)
        self.memory = Memory(128)
        self.bus = BusLog()
        self.log = FeedLog()
        self.lsq = LoadStoreQueue(self.memory, self.bus, capacity=32)
        self.generate_add = lambda cap: Add('r%d' % random.randint(0, cap - 1),
                                        'r%d' % random.randint(0, cap - 1),
                                        'r%d' % random.randint(0, cap - 1))

    def test_invalid_capacity(self):
        """Test exception thrown when initialized with invalid capacity."""
        for _ in range(100):
            invalid = random.randint(-1000, 0)
            with self.assertRaises(ValueError):
                ReorderBuffer(self.rf, self.log, self.lsq, capacity=invalid)

    def test_feed_full(self):
        """Test full operation when feeding Instructions."""
        for rob_capacity in [1, 5, 25, 200]:
            for rs_capacity in [1, 5, 25, 200]:
                for lsq_capacity in [1, 5, 25, 200]:
                    register_limit = min(rob_capacity, rs_capacity)
                    memory_limit = min(rob_capacity, lsq_capacity)

                    rs = ReservationStation(capacity=rs_capacity)
                    lsq = LoadStoreQueue(self.memory,
                                         self.bus,
                                         capacity=lsq_capacity)
                    rob = ReorderBuffer(self.rf,
                                        rs,
                                        lsq,
                                        capacity=rob_capacity)

                    for _ in range(register_limit):
                        ins = self.generate_add(self.n_gpr_registers)
                        self.assertFalse(rob.full(ins),
                                         'ReorderBuffer should not be full after < %d feeds' % register_limit)
                        rob.feed(ins)
                    self.assertTrue(rob.full(self.generate_add(self.n_gpr_registers)),
                                    'ReorderBuffer should be full after %d feeds' % register_limit)
                    with self.assertRaises(AssertionError):
                        rob.feed(self.generate_add(self.n_gpr_registers))

    def test_get_queue_id(self):
        """Test that _get_queue_id throws an error on wrap-around."""
        for capacity in [1, 5, 25, 200]:
            rob = ReorderBuffer(self.rf, self.log, self.lsq, capacity=capacity)
            for _ in range(capacity):
                rob._get_queue_id()
            with self.assertRaises(AssertionError):
                rob._get_queue_id()

    def test_instructions_removed_from_queue_on_commit(self):
        """Test that commit frees a slot in the ROB."""
        for capacity in [1, 5, 25, 200]:
            log = FeedLog()
            rob = ReorderBuffer(self.rf, log, self.lsq, capacity=capacity, width=4)
            # Half fill.
            for _ in range(capacity // 2):
                rob.feed(self.generate_add(self.n_gpr_registers))
            rob.tick() # Instructions now in current queue.
            # Remove all fed from ROB queue by giving values.
            self.assertEqual(capacity // 2, len(log.log))
            for ins in log.log:
                rob.receive(Result(ins.tag, 5))
            for _ in range(math.ceil(capacity / rob.width)):
                rob.tick()
            # Should now be able to feed capacity instructions.
            for _ in range(capacity):
                rob.feed(self.generate_add(self.n_gpr_registers))

    def test_inorder_commit(self):
        """Ensure instruction Results are committed in-order."""
        for _ in range(30):
            for capacity in [1, 5, 25, 200]:
                # Initialize test components.
                self.log.reset()
                zeros = {'r%d' % i: 0 for i in range(capacity)}
                act_rf = RegisterFile(capacity, init_values=zeros)
                exp_rf = RegisterFile(capacity, init_values=zeros)
                width = random.randint(1, 2*capacity)
                rob = ReorderBuffer(act_rf,
                                    self.log,
                                    self.lsq,
                                    capacity=capacity,
                                    width=width)

                # Feed instructions into ROB.
                n_ins = random.randint(1, capacity)
                register_names = []
                for i in range(n_ins):
                    add = self.generate_add(capacity)
                    register_names.append(add.rd)
                    rob.feed(add)
                rob.tick()

                # Generate a Result value for each fed instruction.
                result_vals = [random.randint(1, 10000) for _ in range(n_ins)]

                # Publish all but first result in reverse order to ROB. Should be
                # no updates to act_rf as the first instruction is stalled!
                for i in reversed(range(1, n_ins)):
                    rob.receive(Result(self.log.log[i].tag, result_vals[i]))
                    rob.tick()
                    self.assertEqual(exp_rf, act_rf)

                # Publish result of first instruction - all can now be comitted in
                # turn.
                rob.receive(Result(self.log.log[0].tag, result_vals[0]))

                # Group updates into ROB width chunks.
                updates = list(zip(register_names, result_vals))
                group_updates = [updates[i:i + rob.width]
                                 for i in range(0, len(updates), rob.width)]

                # Ensure in-order commit of width instructions per tick.
                for group in group_updates:
                    rob.tick()
                    for (name, result) in group:
                        exp_rf[name] = result
                    self.assertEqual(exp_rf, act_rf)
                rob.tick()

    def test_conditional_instructions_correct_prediction_commit(self):
        """Test Conditional Instructions with correct predicate commit OK."""
        # Initialize units.
        rs = FeedLog()
        lsq = FeedLog()
        rob = ReorderBuffer(self.rf, rs, lsq, capacity=32)
        rob.WIDTH = 4
        self.rf['r4'] = 0
        self.rf['r5'] = 0

        # Initialize instructions to be fed.
        cond = Blth('r4', 'r5', 2)
        cond.branch_info = BranchInfo(False, 2, 2, None)
        cond.DELAY = 0
        add = AddI('r1', 'r1', 1)
        add.DELAY = 0

        # Feed pairs of (cond, add) instructions.
        n_pairs = 5
        for i in range(n_pairs):
            rob.feed(cond)
            rob.feed(add)
        rob.tick() # Insert into current queue.

        # Receive result for each pair in turn.
        r1_value = 0
        for i in range(0, n_pairs, 2):
            rob.receive(Result(rs.log[i].tag, False))
            rob.receive(Result(rs.log[i + 1].tag, r1_value))
            rob.tick()
            self.assertEqual(self.rf['r1'], r1_value)
            r1_value += 1

    def test_conditional_instructions_incorrect_prediction_no_commit(self):
        """Test that Conditional Instructions with incorrect predicate do not commit."""
        # Initialize units.
        root = FlushableLog()
        rs = FeedLog()
        lsq = FeedLog()
        rob = ReorderBuffer(self.rf, rs, lsq, capacity=32)
        rob.set_pipeline_flush_root(root)
        rob.WIDTH = 4
        self.rf['r4'] = 0
        self.rf['r5'] = 10

        # Initialize instructions to be fed.
        cond = Blth('r4', 'r5', 100)
        cond.branch_info = BranchInfo(False, 100, 1, None)
        cond.DELAY = 0
        add = AddI('r1', 'r1', 1)
        add.DELAY = 0

        # Feed pairs of (cond, add) instructions.
        n_pairs = 5
        for i in range(n_pairs):
            rob.feed(cond)
            rob.feed(add)
        rob.tick() # Insert into current queue.

        # Receive result for each pair in turn.
        for i in range(0, n_pairs, 2):
            rob.receive(Result(rs.log[i].tag, True))
            rob.receive(Result(rs.log[i + 1].tag, 0))
            rob.tick()
            self.assertEqual(self.rf['r1'], 0)
        self.assertEqual(self.rf['pc'], 100)

    def test_flush(self):
        """Ensure flush of ReorderBuffer, LoadStoreQueue and ReservationStation."""
        rs = FlushableLog()
        rs.full = lambda: False
        rs.feed = lambda x: None
        lsq = FlushableLog()
        lsq.full = lambda: False
        lsq.feed = lambda x: None

        for rob_capacity in [1, 5, 25, 200]:
            for rs_capacity in [1, 5, 25, 200]:
                for lsq_capacity in [1, 5, 25, 200]:
                    register_limit = min(rob_capacity, rs_capacity)

                    rs.reset()
                    lsq.reset()
                    rob = ReorderBuffer(self.rf, rs, lsq, capacity=rob_capacity)

                    for _ in range(register_limit):
                        rob.feed(self.generate_add(self.n_gpr_registers))
                    rob.flush()
                    self.assertFalse(rob.full(self.generate_add(self.n_gpr_registers)),
                                     'ReorderBuffer should not be full after flush')
                    self.assertEqual(rs.n_flush, 1,
                                     'ReorderBuffer must flush ReservationStation')
                    self.assertEqual(lsq.n_flush, 1,
                                     'ReorderBuffer must flush LoadStoreQueue')
