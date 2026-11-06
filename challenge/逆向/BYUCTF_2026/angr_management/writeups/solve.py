from pwn import *
import angr
import networkx as nx

def solve(binary_name):
    # Create an angr Project object with auto_load_libs turned off
    p = angr.Project(binary_name, auto_load_libs=False)
    loader = p.loader

    # Generate the control flow graph
    cfg = p.analyses.CFGFast()
    cfg_graph = cfg.model.graph

    # Get the start and end of the main function
    main_func = cfg.kb.functions['main']
    main_start = main_func.addr
    main_end = 0
    for i, block in enumerate(list(main_func.blocks)):
        main_end = max(main_end, block.instruction_addrs[0])

    source_node = cfg.model.get_any_node(main_start)
    sink_node = cfg.model.get_any_node(main_end)

    # Remove calls to printf, puts and get_input from the CFG
    printf_addr = cfg.kb.functions['printf'].addr
    puts_addr = cfg.kb.functions['puts'].addr
    get_input_addr = cfg.kb.functions['get_input'].addr

    addrs_to_remove = [printf_addr, puts_addr, get_input_addr]
    for addr in addrs_to_remove:
        node = cfg.model.get_any_node(addr)
        cfg_graph.remove_node(node)

    # Find a path from the start to the end of main which doesn't enter any disallowed functions
    cfg_path = nx.shortest_path(cfg_graph, source_node, sink_node)

    # Parse the sequence of inputs required to realize the aforementioned path
    # The following loop finds the responsible cmp instructions and extracts the immediate value from each
    computed_path = list()
    for i, cfgnode in enumerate(cfg_path):
        try:
            cfgnode_attrs = cfg.graph.get_edge_data(cfgnode, cfg_path[i+1])
        except:
            pass

        # Verify experimentally-determined conditions for the code to branch to the next goto are met
        if cfgnode_attrs['jumpkind'] == 'Ijk_Boring' and cfgnode_attrs['stmt_idx'] > -2:
            for instruction in cfgnode.block.capstone.insns:
                # Find the cmp instruction responsible and convert the immediate value to decimal; store it
                if instruction.mnemonic == 'cmp':
                    poss = instruction.op_str.split("], ", 1)
                    desired_branch = int(poss[-1], 16)
                    computed_path.append(desired_branch)
                    break

        # print(f"Block at addr {hex(cfgnode.block.addr)}")
        # for instruction in cfgnode.block.capstone.insns:
        #     print(f"  {hex(instruction.address)}: {instruction.mnemonic} {instruction.op_str}")

    # Now solve with pwntools
    elf = context.binary = ELF("./" + binary_name, checksec=False)
    p = elf.process()

    # Send the computed imputs line by line
    for val in computed_path:
        result = p.recvline()
        input = str(val).encode()
        p.sendline(str(val).encode())

    p.recvline()
    flag = p.recvline()[:-1].decode()
    
    p.close()

    return flag
    
print(solve("angr_management_test"))
print(solve("angr_management"))
