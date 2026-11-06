> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #19 的连续章节摘录；代码未执行。

## #19 compile_me_maybe

### 1. 题目信息
- **题目名称**：compile_me_maybe
- **题目类型**：REVERSE
- **最终 Flag**：`NepCTF{N0t_th1s_rUNtimE_m4y_be_next_T1me}`

### 2. 题目分析
`compile_me_maybe` 是 C++17 编译期玄学题：主程序本身几乎不做事，真正的逻辑全在 constexpr / 模板约束链里。witness 不对就直接编译失败，属于「过编译器 = 出 flag」那一类。

### 3. 解题思路
顺着 include 和 main 的约束把合法 witness 推出来（或从约束方程反推字节），写成 `generated_witness.hpp`，然后 make run。运行时就是把编译期算好的字节序列 putchar 出去。

### 4. 解题过程
过程大概是：

1. 读 `include/` 和 `src/main.cpp`，摸清 `witness_bytes` / `program` 的约束。
2. 构造正确的 witness header（复现目录里保留了 `generated_witness.hpp`）。
3. `make -C work/19 run`（或当时 `/tmp/nepctf/work19`），g++ 通过后二进制打印 flag。
4. Flag：`NepCTF{N0t_th1s_rUNtimE_m4y_be_next_T1me}`。

早期树在 /tmp 里被冲过一次，所以 WP 里把 witness 和 main 原文贴全了，方便复查。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/19/exp/README_solve.md`
````text
# #19 compile_me_maybe

Flag: `NepCTF{N0t_th1s_rUNtimE_m4y_be_next_T1me}`

## Process (from agent-a2ce3928 session ca4b204e)
1. Reverse `include/` + `src/main.cpp` constexpr constraints
2. Write correct witness header
3. `make -C /tmp/nepctf/work19 run`
4. Binary prints flag

Session tool_result excerpt:
```
wrote witness header
b'NepCTF{N0t_th1s_rUNtimE_m4y_be_next_T1me}'
make: Entering directory '/tmp/nepctf/work19'
g++ -std=c++17 -O2 ... -o build/compile_me_maybe
./build/compile_me_maybe
NepCTF{N0t_th1s_rUNtimE_m4y_be_next_T1me}
```

Full C++ tree was under `/tmp/nepctf/work19` (wiped). This README is the recovered procedure.
````

#### `work/19/repro/src/include/generated_witness.hpp`
```cpp
#pragma once
#include "vm.hpp"
namespace cmc {
using witness = witness_bytes<0xd4U, 0xb8U, 0x82U, 0xdbU, 0x1aU, 0xa7U, 0xe5U, 0xdeU, 0xd4U, 0x32U, 0xdfU, 0xdfU, 0x4cU, 0xdbU, 0x0cU, 0x41U, 0xcfU, 0x6dU, 0x0aU, 0xceU, 0x92U, 0xd4U, 0xe4U, 0x1aU, 0xccU, 0x68U, 0x89U, 0xfeU, 0x6fU, 0xffU, 0x78U, 0x68U, 0x12U, 0x14U, 0x9aU, 0xeaU, 0xd0U, 0x35U, 0xe4U, 0xabU, 0xa2U, 0x9cU, 0xffU, 0x4eU, 0xf3U, 0xf4U, 0x47U, 0x7fU, 0xf9U, 0x58U, 0x86U, 0x71U, 0x47U, 0x44U, 0x33U, 0x97U, 0x93U, 0x72U, 0x27U, 0x5dU, 0x65U, 0x85U, 0x90U, 0xa1U>;
} // namespace cmc
```

#### `work/19/repro/src/src/main.cpp`
```cpp
#include "vm.hpp"
#include "generated_witness.hpp"

extern "C" int putchar(int);

int main() {
    using bytes = typename cmc::program<cmc::witness>::bytes;

    for (cmc::usize index = 0; index < bytes::size; ++index) {
        putchar(bytes::at(index));
    }
    putchar('\n');

    return 0;
}
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

