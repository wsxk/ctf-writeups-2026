## Angr Management Writeup

The user must traverse through the GOTO maze in order to get the flag.

The intended solve is to extract the program's control flow graph using a tool like `angr` and then to use `nx.shortest_path` (Dijkstra's algorithm) to compute the solve path from the start of the maze to the end.

Using `angr`, we can grab the address at the start of the `main` function and an address near the end of `main`. We can then obtain the `CFGNode` object corresponding to each of these locations in the program. The control flow graph itself is a graph of `CFGNode`s, so this prepares us to use a shortest path algorithm on the graph.

```python
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
```

Wait a second! If we call `nx.shortest_path(cfg_graph, source_node, sink_node)` we will get a very short path since calls to library functions like `printf`, `puts`, and `get_input` connect the source node and sink node prematurely. So we need to manually remove these destinations from our CFG before proceeding:

```python
    # Remove calls to printf, puts and get_input from the CFG
    printf_addr = cfg.kb.functions['printf'].addr
    puts_addr = cfg.kb.functions['puts'].addr
    get_input_addr = cfg.kb.functions['get_input'].addr

    addrs_to_remove = [printf_addr, puts_addr, get_input_addr]
    for addr in addrs_to_remove:
        node = cfg.model.get_any_node(addr)
        cfg_graph.remove_node(node)
```

Now we can determine the shortest path:

```python3
    # Find a path from the start to the end of main which doesn't enter any disallowed functions
    cfg_path = nx.shortest_path(cfg_graph, source_node, sink_node)
```

There is still work to do... we need to actually extract the correct destination names from the code. With some luck and consulting the `angr` documentation, we can examine the types of jumps `angr` has computed between the `CFGNode`s in our `cfg_path`. Turns out that jumps of the type `Ijk_Boring` are what we want. We also require `stmt_idx` to not equal -2 for each of the jumps. See the following code:

```python
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
```

Input each of the numbers in `computed_path` in succession, and we get the flag.
`byuctf{g3t_w1th_th3_c0ntr01_fl0w}`
