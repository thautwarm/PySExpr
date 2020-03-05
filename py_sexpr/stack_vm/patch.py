def bytecode_recursion_opt():
    from bytecode import SetLineno
    from bytecode import cfg

    def compute_stack_size(block, size, maxsize):

        coro = _compute_stack_size(block, size, maxsize)
        coroutines = []
        args = None
        try:
            while True:
                args = coro.send(None)
                while isinstance(args, int):
                    coro = coroutines.pop()
                    args = coro.send(args)
                coroutines.append(coro)
                coro = _compute_stack_size(*args)
        except IndexError:
            assert args is not None
            return args

    def _compute_stack_size(block, size, maxsize):

        if block.seen or block.startsize >= size:
            yield maxsize

        def update_size(delta, size, maxsize):
            size += delta
            if size < 0:
                msg = "Failed to compute stacksize, got negative size"
                raise RuntimeError(msg)
            maxsize = max(maxsize, size)
            return size, maxsize

        block.seen = True
        block.startsize = size

        for instr in block:
            if isinstance(instr, SetLineno):
                continue

            if instr.has_jump():
                # first compute the taken-jump path
                taken_size, maxsize = update_size(
                    instr.stack_effect(jump=True), size, maxsize
                )
                maxsize = yield instr.arg, taken_size, maxsize

                if instr.is_uncond_jump():
                    block.seen = False
                    yield maxsize

            # jump=False: non-taken path of jumps, or any non-jump
            size, maxsize = update_size(instr.stack_effect(jump=False), size, maxsize)
        if block.next_block:
            maxsize = yield block.next_block, size, maxsize

        block.seen = 0
        yield maxsize

    cfg._compute_stack_size = compute_stack_size
