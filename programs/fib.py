from procsim.memory import Memory

MEMORY = Memory(1)

PROGRAM = ['addi r4 r4 0',
           'addi r0 r0 1',
           'addi r1 r1 1',
           'str r0 r4',
           'add r2 r0 r1',
           'addi r0 r1 0',
           'addi r1 r2 0',
           'j 3']