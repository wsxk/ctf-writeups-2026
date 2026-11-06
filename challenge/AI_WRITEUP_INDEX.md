# AI 可读 Writeup 总索引

覆盖原目录的324道规范题目；另有2个重复入口和5个原始资料待补条目。原始 writeups、attachments、catalog.json 均保留。

所有文档为静态分析改写，**不是324题运行复现报告**。已有来源中的缺失、矛盾、局部验证或未完成 solver 已在各题标明。

- [阅读与字段说明](AI_WRITEUP_GUIDE.md)
- [结构化索引](AI_WRITEUP_INDEX.json)
- [资料问题与复现缺口](AI_WRITEUP_ISSUES.md)
- [覆盖及链接检查报告](sources/ai_writeup_validation_report.json)

## 规范题目

### 逆向（104）

| 比赛 | 题目 | 核心机制 |
|---|---|---|
| ASIS CTF Quals 2026 | [Atarude](%E9%80%86%E5%90%91/asis_2026-quals/Atarude/AI_WRITEUP.md) | 六个 lane 各提供两次160字节明文查询；对应176字节密文共11块。验证器只要求解码后首块为零，故可枚举两份密文的块拼接，而非破解AES。最终还有全局摘要选择互补掩码的方向。 |
| ASIS CTF Quals 2026 | [Beyond_the_fourth_wall](%E9%80%86%E5%90%91/asis_2026-quals/Beyond_the_fourth_wall/AI_WRITEUP.md) | 巨大C源码的空白和重复token编码字节：indent ／ ((n_w-1)<<3) ／ (x_code<<6)。解码后Wall A是以三元组执行减法的VM，B/C/D是加密区；28字符输入既驱动VM也参与解密。 |
| ASIS CTF Quals 2026 | [Collector](%E9%80%86%E5%90%91/asis_2026-quals/Collector/AI_WRITEUP.md) | 17个十六进制字符拆成路由nibble与64位P。路由控制GC可达集合，P进入SplitMix/S盒/位排列网络。15个诱饵路由值泄露缺失目标；固定路由后六个16位观测约束P。 |
| ASIS CTF Quals 2026 | [LeakMeAk](%E9%80%86%E5%90%91/asis_2026-quals/LeakMeAk/AI_WRITEUP.md) | 34字节输入的28字节主体分七组；先从循环rotate/add/xor方程解七个中间word，再反转奇数乘法。0x9e3779b9在模2^32下的逆为0x144cbc89，小状态表规则可用DFS过滤。 |
| ASIS CTF Quals 2026 | [Lesh](%E9%80%86%E5%90%91/asis_2026-quals/Lesh/AI_WRITEUP.md) | 32位Windows shellcode先睡眠、死循环再构造并改写栈字符串；最早看见的是诱饵，真flag仅在五次修改完成到后续覆盖之间存在。 |
| ASIS CTF Quals 2026 | [Mousa](%E9%80%86%E5%90%91/asis_2026-quals/Mousa/AI_WRITEUP.md) | 自定义MAC的四个32位lane互不混合，且旋转、加法和奇数乘法均可逆。每lane四个key字节拆2+2做中间相遇，MAC碰撞再用嵌入SHA-256筛选。 |
| ASIS CTF Quals 2026 | [NEON](%E9%80%86%E5%90%91/asis_2026-quals/NEON/AI_WRITEUP.md) | AArch64游戏将32动作回放绑定到三层HKDF/AES-GCM。前16动作的12轮可逆ARX与后16动作的10轮混合分别可反解；真实游戏状态仍参与最终密钥。 |
| b01lers CTF 2026 | [shakespeares-revenge](%E9%80%86%E5%90%91/b01lers_CTF_2026/shakespeares-revenge/AI_WRITEUP.md) | 自定义Shakespeare解释器的角色值64位、角色栈32位；截断允许构造计算器外的栈内容。revere从栈取syscall号，-1参数替换为reference指向角色栈的字符串。 |
| b01lers CTF 2026 | [tiles--ai](%E9%80%86%E5%90%91/b01lers_CTF_2026/tiles--ai/AI_WRITEUP.md) | solve_puzzle使用deque.popleft执行BFS，文件名虽叫dfs_solver但算法不是DFS。棋盘6×6，编号0..7水平移动，8..15垂直移动；0号车覆盖格17即胜利。 |
| BDSec CTF 2026 | [Easy_RE_Challenge](%E9%80%86%E5%90%91/bdsec_2026/Easy_RE_Challenge/AI_WRITEUP.md) | 四条输入长度路径中24/26/29均为诱饵，真实41字节路径逐字节XOR双key、循环左移、加项并置换输出。每步可逆，out[(13*i)%41]来自input[i]。 |
| BDSec CTF 2026 | [Night_Shift](%E9%80%86%E5%90%91/bdsec_2026/Night_Shift/AI_WRITEUP.md) | 输入为8个0..4 token，决定五线程对共享四个32位word及hash的更新顺序。互斥与条件变量使调度成为确定的离散状态机，搜索空间仅5^8。 |
| BearcatCTF 2026 - Setting Sail | [Captain_Morgan](%E9%80%86%E5%90%91/bearcat_2026/Captain_Morgan/AI_WRITEUP.md) | Python单行程序把29字节主体转为大端232位整数，约2100条布尔赋值构成组合电路；最终bfu==0即接受。 |
| BearcatCTF 2026 - Setting Sail | [Missing_One_Piece](%E9%80%86%E5%90%91/bearcat_2026/Missing_One_Piece/AI_WRITEUP.md) | 检查器的秘密是运行上下文：argv[0]必须./devilishFruit，PWD必须/tmp/gogear5，环境中须ONE_PIECE=IS_REAL。满足后程序自行变换并输出flag。 |
| BearcatCTF 2026 - Setting Sail | [Pollys_Key](%E9%80%86%E5%90%91/bearcat_2026/Pollys_Key/AI_WRITEUP.md) | Ruby/Perl多语言文件通过不同注释结束符执行不同约束。Ruby筛出模257原根字符；排除^后恰好50个字符，故只需求排列。Perl插入排序逆序数约束秩，额外先后规则消除同值对。 |
| bhackari CTF 2026 | [Dont_unpack_me](%E9%80%86%E5%90%91/bhackari_2026/Dont_unpack_me/AI_WRITEUP.md) | 外层PE不是普通壳：它向内层入口四个槽写入外层callback。两层数据异或得到GetHandlerProperty2；版本检查指向7z.dll 24.09。该导出机器码既提供28字节密文，也经CRC32生成RC4 key。 |
| bhackari CTF 2026 | [Mystery](%E9%80%86%E5%90%91/bhackari_2026/Mystery/AI_WRITEUP.md) | mystery.so在初始化时哈希自身：SHA-256与CRC32生成64字节表和四个stage值，再混合成AES-256-CTR key。所有关键材料均来自给定文件，可离线重算。 |
| boroCTF 2026 | [AlphaCode](%E9%80%86%E5%90%91/boroctf_2026/AlphaCode/AI_WRITEUP.md) | AlphaCode为六opcode的自定义DSL，关键约束是同一时刻只能打开一个zm函数，而非整段程序只能出现一次zm。闭合后可再次定义，在队列中累积字面量并拼出目标模板。 |
| BYUCTF 2026 | [angr_management](%E9%80%86%E5%90%91/BYUCTF_2026/angr_management/AI_WRITEUP.md) | GOTO迷宫可以转为main内部控制流图上的路径问题。若保留printf/puts/get_input节点，调用与返回边会造出虚假捷径；需先删去这些非迷宫节点。 |
| BYUCTF 2026 | [picklerick](%E9%80%86%E5%90%91/BYUCTF_2026/picklerick/AI_WRITEUP.md) | pickled.txt用单词承载二进制：pickle映射1，其他token映射0；每8bit转字节后再XOR 0x67，恢复ELF。 |
| BYUCTF 2026 | [rcaas](%E9%80%86%E5%90%91/BYUCTF_2026/rcaas/AI_WRITEUP.md) | 程序以服务身份读取系统文件并在run()检查46字节输入。solver将各字符设为8位BitVec，用字符乘积模256方程、前后缀和固定3字符共同约束。 |
| BYUCTF 2026 | [yara](%E9%80%86%E5%90%91/BYUCTF_2026/yara/AI_WRITEUP.md) | YARA规则本身就是接受条件：目标文件必须同时满足规则中的字符串、偏移和数值约束。可以手工还原，也可将条件整体变成SAT/SMT。 |
| COMPFEST CTF 2026 | [ITS_ME_BURHAN](%E9%80%86%E5%90%91/compfest_2026/ITS_ME_BURHAN/AI_WRITEUP.md) | Burhan管理员密码由普通账号能观察的9个值确定；三项任务顺序也由初始等级和金币派生。sigil依赖完成历史，18种可逆变换和排列共同编码密码及密封档案。 |
| Cryovault 2026 Quals | [rime_scrub](%E9%80%86%E5%90%91/cryovault_2026-quals/rime_scrub/AI_WRITEUP.md) | ECC纠错次数泄露物理cell是否被强制值改变。先用双错误纠正翻转control bit0开放保护区fault，再对两个不同ECC字的匹配bit同时施加fault；纠错次数奇偶消去每次刷新的掩码，得到真实key bit。 |
| CSS CTF 2026: Return of Nexus | [FLAPPY_BOARD](%E9%80%86%E5%90%91/css_2026/FLAPPY_BOARD/AI_WRITEUP.md) | Flappy客户端只提交flap tick，服务端按seed重放确定性物理。复刻xorshift32、整数重力与碰撞后可离线搜索三轮得分10/20/30的动作；flag仅由第4轮服务响应返回。 |
| DiceCTF 2026 Quals | [another-onion](%E9%80%86%E5%90%91/DiceCTF_2026_Quals/another-onion/AI_WRITEUP.md) | 多层自解密代码每层消耗2字节key，SHA-NI产生密钥流；正确key解出符合下一层模板的代码，因此每层只需搜索65536候选。 |
| DiceCTF 2026 Quals | [bedtime](%E9%80%86%E5%90%91/DiceCTF_2026_Quals/bedtime/AI_WRITEUP.md) | 384局bounded Nim的Grund值为pile%(k+1)，异或零的219局走PRNG分支。用户动作还反馈更新PRNG state[2]，因此各局不能独立模拟。 |
| DiceCTF 2026 Quals | [explorer](%E9%80%86%E5%90%91/DiceCTF_2026_Quals/explorer/AI_WRITEUP.md) | Rust内核模块通过/dev/challenge的ioctl暴露3D迷宫。墙位可直接查询，诱饵出口使状态变2并锁定移动，需跨reset记住坏格。 |
| Haruulzangi CTF 2026 Qualifier | [Ehlel](%E9%80%86%E5%90%91/haruulzangi_2026-quals/Ehlel/AI_WRITEUP.md) | 大端MIPS壳内实现uTP上的P2P文件协议；Ed25519转换Curve25519后导出共享key，两条独立RC4流加密完整记录。目标是下载内嵌module ID对应数据。 |
| Haruulzangi CTF 2026 Qualifier | [Furnace](%E9%80%86%E5%90%91/haruulzangi_2026-quals/Furnace/AI_WRITEUP.md) | Minecraft只是UI，JNI执行40条可逆双64位寄存器VM。输出低38位被掩去，枚举这些位并逆VM得到候选128位key，再用SHA-256前8字节pin筛选。 |
| Haruulzangi CTF 2026 Qualifier | [Trace](%E9%80%86%E5%90%91/haruulzangi_2026-quals/Trace/AI_WRITEUP.md) | SIGILL/FPE/SEGV是加载器正常控制流。当前明文stage的FNV-1a作为SplitMix64种子解下一段，最后16字节目标约束8轮可逆ARX及两个隐藏状态word。 |
| kBxAc CTF 2026 | [Patcher_1](%E9%80%86%E5%90%91/kbxac_2026/Patcher_1/AI_WRITEUP.md) | 四个程序已有WIN路径，任务是按1/2/3/6字节预算修改分支与比较，而非恢复密码。服务地址与文件偏移相差加载基址0x400000。 |
| kBxAc CTF 2026 | [Patcher_2](%E9%80%86%E5%90%91/kbxac_2026/Patcher_2/AI_WRITEUP.md) | 第二组预算2/4/3/3，跨C++、Go、Rust。首题利用连续输出helper布局，把尾跳转改call，使输出返回后顺序落入下一helper。 |
| kBxAc CTF 2026 | [Shherrr](%E9%80%86%E5%90%91/kbxac_2026/Shherrr/AI_WRITEUP.md) | Raku计算器的四则运算是干扰；隐藏分支有密文字数值数组及5数字循环key，输出为chr(cipher[i]^key[i%5])。 |
| kBxAc CTF 2026 | [simphell](%E9%80%86%E5%90%91/kbxac_2026/simphell/AI_WRITEUP.md) | GHC静态列表以closure链而非连续字节存储，并带指针tag。恢复37字节密文后用FA CE FE ED DE AD循环XOR。 |
| KubSTU CTF | [Ouroboros](%E9%80%86%E5%90%91/kubstu_2026/Ouroboros/AI_WRITEUP.md) | fat Mach-O每个架构各自用__text哈希派生ChaCha20 key。__d3由LCG解出VM并校验activation key，__d5才是真flag密文。 |
| KubSTU CTF | [RISC_V.](%E9%80%86%E5%90%91/kubstu_2026/RISC_V/AI_WRITEUP.md) | 原始RV32固件先哈希boot stub生成xorshift流解密二阶段；非法指令trap充当调用/返回ABI。后续RC4生成Feistel轮密钥，最终状态再次驱动RC4解flag。 |
| LA CTF 2026 | [flag-finder](%E9%80%86%E5%90%91/LA_CTF_2026/flag-finder/AI_WRITEUP.md) | 101×19复选框被大正则编码成行列nonogram约束，满足图案后以3×5像素字体显示flag。 |
| LA CTF 2026 | [lactf-1986](%E9%80%86%E5%90%91/LA_CTF_2026/lactf-1986/AI_WRITEUP.md) | DOS检查器以整串20位哈希作为LFSR种子，流异或结果必须匹配表。枚举的是2^20种子，不是所有flag字符串；候选还必须自洽地哈希回原种子。 |
| LA CTF 2026 | [ooo](%E9%80%86%E5%90%91/LA_CTF_2026/ooo/AI_WRITEUP.md) | 同形Unicode函数名遮蔽简单算术，实际相邻码点满足x[i]+x[i+1]=arr[i]。官方solver从'l'开始递推x[i+1]=arr[i]-x[i]。 |
| LA CTF 2026 | [starless-c](%E9%80%86%E5%90%91/LA_CTF_2026/starless-c/AI_WRITEUP.md) | 自修改迷宫状态包含当前位置和5个active token。移动到active格会消耗它并激活特定save target，f路径要求指定五格同时active。 |
| LA CTF 2026 | [the-fish](%E9%80%86%E5%90%91/LA_CTF_2026/the-fish/AI_WRITEUP.md) | Fish程序先将UTF-8输入大端拼整数，再用变体Collatz把奇偶路径编码进大整数。官方逆算法从acc=1遍历target低位：先倍增，若位为1则减1再除3。 |
| LA CTF 2026 | [the-three-sat-problem](%E9%80%86%E5%90%91/LA_CTF_2026/the-three-sat-problem/AI_WRITEUP.md) | 1279个0/1字符承载SAT赋值，main额外要求bit754=1；大验证函数组合OR子句及AND。关键工作是忠实抽取SSA依赖而非盲删矛盾条件。 |
| LYKNCTF | [Control_Freak_1](%E9%80%86%E5%90%91/lyknctf_2026/Control_Freak_1/AI_WRITEUP.md) | 33字节三轮变换：逐字节异或/旋转/加法→PERM[k]=(3+7k)%33散射→累积XOR。逆解按轮2、1、0，再按链、置换、字节变换的逆顺序。 |
| LYKNCTF | [Control_Freak_2](%E9%80%86%E5%90%91/lyknctf_2026/Control_Freak_2/AI_WRITEUP.md) | 平坦化状态机只有五个可达状态。四种反分析taint汇入最终比较；正常taint=0时，S盒与密钥流固定，可直接逆30字节滚动XOR。 |
| LYKNCTF | [Waguri2](%E9%80%86%E5%90%91/lyknctf_2026/Waguri2/AI_WRITEUP.md) | 七种角色token对应无输出Brainfuck。34次输入后没有打印flag，正确性由是否避开不会修改控制cell的无限循环决定。 |
| NCTF 2026 | [No My Bank!](%E9%80%86%E5%90%91/NCTF_2026/No%20My%20Bank%21/AI_WRITEUP.md) | Godot资源AES加密和DLL RC4仅是外层。DLL的TLS callback把看似TEA的函数hook到SMC解密代码，真实检查为换表/换位Base64再逐字符加密。 |
| NCTF 2026 | [Pay For 2048](%E9%80%86%E5%90%91/NCTF_2026/Pay%20For%202048/AI_WRITEUP.md) | Electron的license-service.js通过wasm-bridge调用key校验与flag解密。字串RUST/WASM/2048变leet后形成license，规范化digest必须等于0xFC97CA2F。 |
| NCTF 2026 | [鸡爪流高手](%E9%80%86%E5%90%91/NCTF_2026/%E9%B8%A1%E7%88%AA%E6%B5%81%E9%AB%98%E6%89%8B/AI_WRITEUP.md) | ELO低分保护仅检查更新前score<10，没有检查更新后结果。把当前分压到10再输给0分bot，扣分超过10可使无符号分数下溢。 |
| NepCTF 2026 | [compile_me_maybe](%E9%80%86%E5%90%91/NepCTF%202026/19_compile_me_maybe/AI_WRITEUP.md) | 检查逻辑在C++17 constexpr/模板链，正确witness使编译期断言通过，运行时只输出预计算字节。 |
| NepCTF 2026 | [【Game】共生（本地）](%E9%80%86%E5%90%91/NepCTF%202026/70_%E3%80%90Game%E3%80%91%E5%85%B1%E7%94%9F%EF%BC%88%E6%9C%AC%E5%9C%B0%EF%BC%89/AI_WRITEUP.md) | Unity IL2CPP的BuildCompletionCode哈希依赖自然发生的12事件序列；直接allcp传送/全checkpoint路径改变Mix轨迹，不能得到目标完成码。 |
| NepCTF 2026 | [【Game】共生（联机）](%E9%80%86%E5%90%91/NepCTF%202026/72_%E3%80%90Game%E3%80%91%E5%85%B1%E7%94%9F%EF%BC%88%E8%81%94%E6%9C%BA%EF%BC%89/AI_WRITEUP.md) | 联机完成流程同时依赖HTTP注册及UDP双端状态机。host/guest必须不同team_token，否则DupTeam使后续NotInGame；RunComplete还检查进度时机。 |
| PascalCTF 2026 | [Albo delle Eccellenze](%E9%80%86%E5%90%91/PascalCTF_2026/Albo%20delle%20Eccellenze/AI_WRITEUP.md) | 代码生成器的strcmp相等返回1，但main又xor eax,1导致分支反转：不匹配硬编码A11D612LPSCBLS37反而进入读flag路径。 |
| PwnSec CTF 2026 | [Operation_Split_Horizon](%E9%80%86%E5%90%91/pwnsec_2026/Operation_Split_Horizon/AI_WRITEUP.md) | PCAP含多阶段投递和分流外传。先AES-CBC/HMAC解dropper，再过XTEA类loader和SBVM4；C2用逐消息更新key的ChaCha20，最后数据拆在HTTP cookie与DNS并以截断HMAC标记。 |
| PwnSec CTF 2026 | [Two_Worlds_One_Heart](%E9%80%86%E5%90%91/pwnsec_2026/Two_Worlds_One_Heart/AI_WRITEUP.md) | 同一段机器码在x86与x64模式有不同含义，0x48分别是dec eax与REX.W。Heaven's Gate两次执行同地址，分别检查输入前20和后20字节。 |
| RITSEC CTF 2026 | [Buried_Treasure](%E9%80%86%E5%90%91/ritsec_2026/Buried_Treasure/AI_WRITEUP.md) | 多层内存解包之后核心只是线性表检查。原文文字简写公式不准确，末尾solver显示每轮r12从0x26加1，r13从13每轮加13。 |
| RITSEC CTF 2026 | [not_quite_optimal](%E9%80%86%E5%90%91/ritsec_2026/not_quite_optimal/AI_WRITEUP.md) | 延迟和GMP大整数隐藏模256幂塔计算；只需要每个条目的模结果，再经(value+1)>>1得到字符，不需要构造巨大整数。 |
| RITSEC CTF 2026 | [obfpyscated](%E9%80%86%E5%90%91/ritsec_2026/obfpyscated/AI_WRITEUP.md) | Python多层XOR、AES和marshal最终指向PNG；真正判定按固定坐标取像素，并以r^g^b还原字符。网络和解释器只是承载多阶段代码。 |
| RITSEC CTF 2026 | [T_reasure_Chest](%E9%80%86%E5%90%91/ritsec_2026/T_reasure_Chest/AI_WRITEUP.md) | 输入零填充到8字节块，key为tiny_encrypt_key。文章将轮函数称XTEA，但最终代码使用固定key[0..3]位置的TEA式公式，应以实际表达式为准。 |
| scriptCTF 2026 | [F_K](%E9%80%86%E5%90%91/scriptctf_2026/F_K/AI_WRITEUP.md) | Brainfuck长程序折叠后为重复线性检查，残差为input+C-(A*K+B)模256。末尾+[]使所有输入都最终挂起，区别在到达终止循环前的清零耗时。 |
| SCTF 2026 | [Alice](%E9%80%86%E5%90%91/SCTF_2026/Alice/AI_WRITEUP.md) | macOS动态解密链最终给QR Version5/M第一RS块的24字节parity与8字节固定padding。前35字节280bit未知，可通过RS在GF(2)上的线性性建立192方程，再叠加QR模式、长度与flag格式约束。 |
| SCTF 2026 | [ghost_projection](%E9%80%86%E5%90%91/SCTF_2026/ghost_projection/AI_WRITEUP.md) | 外壳修复后stage2的route projection有normally closed oracle；7字节补丁调整latch/gate参数开放隐藏字节泄漏，四epoch分别覆盖idx%4的一类。 |
| SCTF 2026 | [Zombie_progression](%E9%80%86%E5%90%91/SCTF_2026/Zombie_progression/AI_WRITEUP.md) | 6×6魔方可见状态只是表层；36步文本、IPC、fd、TLS、checkpoint等隐藏摘要共同派生ChaCha20 key。每三步有检查，能把117^36搜索拆成带前缀验证的小块。 |
| SekaiCTF 2026 | [Chibile](%E9%80%86%E5%90%91/sekaictf_2026/Chibile/AI_WRITEUP.md) | 游戏秘密门、UM和KM attestations、两阶段加密协议构成依赖链。KM可函数模拟，最终两个12字符秘密由BK及服务lh/c值经HMAC/rotate派生。 |
| SekaiCTF 2026 | [Untitled_Encore](%E9%80%86%E5%90%91/sekaictf_2026/Untitled_Encore/AI_WRITEUP.md) | Windows PE内嵌0xbb8字节eBPF ELF，rodata又藏388字节按PC异或编码的验证器。32个chart字节直接校验后，VM输出和parser聚合状态参与最终32字节自定义hash。 |
| squ1rrel CTF 2026 | [redactr](%E9%80%86%E5%90%91/squ1rrel_2026/redactr/AI_WRITEUP.md) | 模糊逆问题含tile shuffle、横/纵卷积、伪随机边界补值和量化。奇行/奇列反向遍历改变PRNG消耗顺序，错误正向模型会让恰好一半约束不可行。 |
| squ1rrel CTF 2026 | [squ1rrel_o_tron](%E9%80%86%E5%90%91/squ1rrel_2026/squ1rrel_o_tron/AI_WRITEUP.md) | PDF内嵌TinyEMU asm.js和RISC-V Linux，chall使用只在修改模拟器中实现的两条自定义指令。funct7=0x7e设置状态，0x7f用S盒和状态执行混合。 |
| Srdnlen CTF 2026 Quals | [Artistic warmup](%E9%80%86%E5%90%91/Srdnlen_CTF_2026_Quals/Artistic%20warmup/AI_WRITEUP.md) | API hash隐藏GDI调用；输入用Consolas绘到450×50 32bpp DIB，与静态参考像素逐字节XOR0xAA后比较。直接恢复参考图即可读flag。 |
| Srdnlen CTF 2026 Quals | [Rev Juice](%E9%80%86%E5%90%91/Srdnlen_CTF_2026_Quals/Rev%20Juice/AI_WRITEUP.md) | Verilog自动售货机解锁product8取决于COINS_INSERTED的历史值和周期。需恰好19枚可用硬币；cancel会退币，购买不会，时序决定可行操作。 |
| SUCTF 2026 | [SU_easygal](%E9%80%86%E5%90%91/SUCTF_2026/SU_easygal/AI_WRITEUP.md) | 60节点每步二选一，最终weight<=132且value=322。阶段背包DP同时保存最优值、路径计数和前驱，恢复唯一路径后拼marker做MD5。 |
| SUCTF 2026 | [SU_Protocol](%E9%80%86%E5%90%91/SUCTF_2026/SU_Protocol/AI_WRITEUP.md) | Themida保护的协议检查器在运行时修改TEA key/delta。payload嵌于121字节结构，要求反序列化首字节0x60与opcode0x55；最终flag是完整封包hex字符串的MD5。 |
| SUCTF 2026 | [SU_revird](%E9%80%86%E5%90%91/SUCTF_2026/SU_revird/AI_WRITEUP.md) | 表面main的XOR检查为假flag，真实入口解PE并进程镂空启动worker，再通过Revird驱动组合R3/R0两份AES轮密钥。实际密码还改了S盒、opcode组合并多一层ShiftRows。 |
| TAMUctf 2026 | [acidity](%E9%80%86%E5%90%91/TAMUctf_2026/acidity/AI_WRITEUP.md) | 游戏雨点PRNG可受输入字节控制：byte复制到64位两处后混入state，经移位和乘0xf337产生bit图。目标连续14次让第17列安全，动作按四帧节奏生效。 |
| TAMUctf 2026 | [challenge7](%E9%80%86%E5%90%91/TAMUctf_2026/challenge7/AI_WRITEUP.md) | 外层ELF用.text SHA与候选32字节常量形成bind，bind同时解碎片并参与SHA规则选择。恢复动作链得到内层，再逆37字节目标的逐字节add/XOR流。 |
| TAMUctf 2026 | [hyper-neighbor](%E9%80%86%E5%90%91/TAMUctf_2026/hyper-neighbor/AI_WRITEUP.md) | 接收器将共享musl文件64条cache line的时延模式解释成64位消息；慢线为1。消息低32位数据、中16位索引、高16位CRC32C缩并校验，开始/结束marker标帧。 |
| TAMUctf 2026 | [kitchen-sink](%E9%80%86%E5%90%91/TAMUctf_2026/kitchen-sink/AI_WRITEUP.md) | 64项target是Walsh-Hadamard变换后的整数向量；官方solver直接用sympy.ifwht恢复字节，而非逐字符搜索。 |
| TAMUctf 2026 | [nucleus](%E9%80%86%E5%90%91/TAMUctf_2026/nucleus/AI_WRITEUP.md) | nucleus21.exe资源type0xa/id0x65包着前一层PE，资源用单字节XOR加密，key就是一枚flag字符。自外向内得到字符顺序需反转。 |
| TAMUctf 2026 | [skretch](%E9%80%86%E5%90%91/TAMUctf_2026/skretch/AI_WRITEUP.md) | 图像字节先加i+1模256，再以循环三对角方程A[i]x[i-1]+B[i]x[i]+C[i]x[i+1]=R[i]编码。稀疏矩阵使大PNG系统可解。 |
| TAMUctf 2026 | [sun-temple](%E9%80%86%E5%90%91/TAMUctf_2026/sun-temple/AI_WRITEUP.md) | 2736字节blob按三字节指令解析，type/variant/operand决定成本，最多12个rite及其顺序提供折减和交互。目标分数<=3415150，是序列优化而非直接解密。 |
| TAMUctf 2026 | [war-hymn](%E9%80%86%E5%90%91/TAMUctf_2026/war-hymn/AI_WRITEUP.md) | ELF假节名藏解密代码、密文和key。首层ks从0x67起按key[i%len]+i累加后XOR；前8字节是长度头，后续zlib得到内层，内层用RC4解四个数据块。 |
| Thryve CTF 2026 | [black-blood](%E9%80%86%E5%90%91/Thryve_CTF_2026/black-blood/AI_WRITEUP.md) | 13轮各输入13字节，真实检查是加密VM中的104位奇偶线性方程；每阶段正确答案更新chain，解锁下一阶段指令。假license和题面问题文字无关。 |
| Thryve CTF 2026 | [hell](%E9%80%86%E5%90%91/Thryve_CTF_2026/hell/AI_WRITEUP.md) | 实际checker只检查12字节主体的环形三邻居MBA方程，前一复杂函数结果未流入判定。8位BitVec自然表达模256的XOR、加乘。 |
| Thryve CTF 2026 | [redline](%E9%80%86%E5%90%91/Thryve_CTF_2026/redline/AI_WRITEUP.md) | 36字符288bit以dual-rail对存储，2972个门形成布尔电路，320个输出匹配target。成对随机翻转相互抵消，可符号表示为共享同一布尔mask。 |
| TJCTF 2026 | [rotated](%E9%80%86%E5%90%91/tjctf_2026/rotated/AI_WRITEUP.md) | 每字节加0x1d掩盖ELF魔数；恢复ELF后它释放Bash脚本，脚本参数展开最终解base64+gzip，真正flag在解压命令注释中的第二层base64。 |
| TRX CTF 2026 | [faulty_road](%E9%80%86%E5%90%91/trx_2026/faulty_road/AI_WRITEUP.md) | 内核题真正输入是(page fault地址,保存的寄存器编号)。ioctl装载自定义IDT handler后，缺页处理器按当前mmio映射移动狼羊菜；地址必须只出现在一个候选寄存器。 |
| UIUCTF 2026 | [glyphs](%E9%80%86%E5%90%91/uiuctf_2026/glyphs/AI_WRITEUP.md) | bitmap解释器构造lambda项图，真正checker是Scott编码树/三值glyph。目标长度146由树拓扑确定；69个双字节body单元中只有56个参与检查。 |
| UIUCTF 2026 | [GODMODE_999](%E9%80%86%E5%90%91/uiuctf_2026/GODMODE_999/AI_WRITEUP.md) | RankedFS必须回放到已发布checkpoint28，忽略后续未提交transaction404。文件hash虽用SHA IV却是自定义压缩；直接模拟固件可准确恢复文件、可逆RAID9回放VM与最终AEAD。 |
| UIUCTF 2026 | [vector_cache](%E9%80%86%E5%90%91/uiuctf_2026/vector_cache/AI_WRITEUP.md) | ud2触发SIGILL handler解释VM；三模式分别约束24字节token的前8、16、24字节，父子进程分担。每式最多三个字节，可做CSP逐段恢复。 |
| UIUCTF 2026 | [Veil_of_Evernight](%E9%80%86%E5%90%91/uiuctf_2026/Veil_of_Evernight/AI_WRITEUP.md) | 213字节VM从双reflection解765碎片，碎片的rank构成0..764排列；输出总195816字节重组为PNG。图末两字符含歧义，需29字节输入的原checker裁决。 |
| UMassCTF 2026 | [Batcave_Bitflips](%E9%80%86%E5%90%91/umassctf_2026/Batcave_Bitflips/AI_WRITEUP.md) | 损坏license checker本来在hash==EXPECTED时以hash解flag；解密处OR疑为XOR损坏。因此静态FLAG xor EXPECTED即可恢复明文，无需求哈希原像。 |
| UMDCTF 2026 | [nuclear_codes](%E9%80%86%E5%90%91/umdctf_2026/nuclear_codes/AI_WRITEUP.md) | 最终高精度比较要求abs(left)<约2^-4096。原文将left化为-N/((a-c)(2a-b)(a+b-c))，对a>b>c>0分母为正，因此求整数N=0即可。 |
| UMDCTF 2026 | [rainbet](%E9%80%86%E5%90%91/umdctf_2026/rainbet/AI_WRITEUP.md) | 服务器与附件WASM相同，generate_game(session_id,round_idx)完全确定；sessioninfo还提供动作HMAC key。局面可提前计算，再按规范签名完成25次最大收益。 |
| UMDCTF 2026 | [the_akari](%E9%80%86%E5%90%91/umdctf_2026/the_akari/AI_WRITEUP.md) | 巨型Akari解的特定256格编码AES key，每组8bit反转再转字节，flag_enc前16字节为IV。规则传播可消掉约65%，但原作者剩余3.3M格未独立解出。 |
| UofTCTF 2026 | [Baby (Obfuscated) Flag Checker](%E9%80%86%E5%90%91/UofTCTF_2026/Baby%20%28Obfuscated%29%20Flag%20Checker/AI_WRITEUP.md) | solver用自定义输入对象替代字符串，__getitem__记录切片索引，__eq__记录比较常量并返回True，从而让混淆检查器继续暴露后续约束。 |
| UofTCTF 2026 | [ML Connoisseur](%E9%80%86%E5%90%91/UofTCTF_2026/ML%20Connoisseur/AI_WRITEUP.md) | 混淆神经网络实为可逆加性coupling串。每块先逆通道线性mix，再用x2=y2-G(y1)、x1=y1-F(x2)恢复；无需逆ReLU或训练模型。 |
| UofTCTF 2026 | [Symbol of Hope](%E9%80%86%E5%90%91/UofTCTF_2026/Symbol%20of%20Hope/AI_WRITEUP.md) | UPX解包后的checker可用angr符号执行，以stdout包含Yes作为成功状态。solver建44个8位符号输入并加uoftctf前缀与位置41的右花括号。 |
| UofTCTF 2026 | [Will u Accept Some Magic?](%E9%80%86%E5%90%91/UofTCTF_2026/Will%20u%20Accept%20Some%20Magic_/AI_WRITEUP.md) | Binaryen把所有i32.ne替换为同签名hook调用，Node日志记录不相等操作的两侧数值，但返回原比较结果，因此是观察器而非强制通过补丁。 |
| V1T CTF 2026 | [Ducks_Ping_Pong](%E9%80%86%E5%90%91/v1t_2026/Ducks_Ping_Pong/AI_WRITEUP.md) | KMDF驱动先以调用方.text的FNV-1a绑定用户程序；三IOCTL返回阶段reward，flag是三个已知FNV/reward对与用户/内核两段16字节blob的静态XOR组合。 |
| V1T CTF 2026 | [Tiny](%E9%80%86%E5%90%91/v1t_2026/Tiny/AI_WRITEUP.md) | 904字节ELF只累加所有非换行输入为key，再从0xe3个16位数减key解RLE图。图的结构约束确定sum=625，flag本身字节和也为625。 |
| VuwCTF 2026 | [dotsbedashing](%E9%80%86%E5%90%91/vuwctf_2026/dotsbedashing/AI_WRITEUP.md) | 36项Morse表以ROL8隐藏字符；target每个dword先更新key=ROR32(key,1)再XOR。解出完整(length,bits)映回字符得到预期主体。 |
| VuwCTF 2026 | [ilikewords](%E9%80%86%E5%90%91/vuwctf_2026/ilikewords/AI_WRITEUP.md) | 随机4位数经修复repdigit后执行Kaprekar迭代总到6174，故URL XOR key固定。最终flag的%s不是用户答案，而是解密URL的偏移28起6字节wordle。 |
| z0d1ak CTF Qualifiers | [Black_Tide_Survey](%E9%80%86%E5%90%91/z0d1ak_2026-quals/Black_Tide_Survey/AI_WRITEUP.md) | BTS2记录含12bit采样的zig-zag delta编码；PING存储顺序为偶后奇且port反向。真实标记以0xF00/0x100二值哨兵埋在starboard交替行。 |
| z0d1ak CTF Qualifiers | [pekpek_stadium_64](%E9%80%86%E5%90%91/z0d1ak_2026-quals/pekpek_stadium_64/AI_WRITEUP.md) | v64相邻字节交换后露出N64 ELF和SYMT。真实locker只依赖16字节key的32位CRC状态，因此可用已知zdk{前缀与尾部CRC求有效状态，不必恢复原key。 |
| z0d1ak CTF Qualifiers | [rival_battle](%E9%80%86%E5%90%91/z0d1ak_2026-quals/rival_battle/AI_WRITEUP.md) | trainer.sav把16位PRNG固定，但玩家动作也消耗随机数，故要模拟14步完整战斗。32位终态hash可能碰撞，flag流却依赖全部14个状态字段。 |
| 第十届“强网杯”全国网络安全挑战赛·线上赛 | [ELFStudy](%E9%80%86%E5%90%91/%E7%AC%AC%E5%8D%81%E5%B1%8A%E2%80%9C%E5%BC%BA%E7%BD%91%E6%9D%AF%E2%80%9D%E5%85%A8%E5%9B%BD%E7%BD%91%E7%BB%9C%E5%AE%89%E5%85%A8%E6%8C%91%E6%88%98%E8%B5%9B%C2%B7%E7%BA%BF%E4%B8%8A%E8%B5%9B/ELFStudy/AI_WRITEUP.md) | 节区外重叠重定位会改符号表并触发隐藏IFUNC resolver；resolver倒序滚动XOR解代码，真实验证是带白化的30轮64位Feistel。 |

### pwn（124）

| 比赛 | 题目 | 核心机制 |
|---|---|---|
| 0xFUN CTF 2026 | [67_revenge](pwn/0xFUN_CTF_2026/67_revenge/AI_WRITEUP.md) | 尾部NUL越界清除下一块size低字节，形成Einherjar堆重叠。 |
| 0xFUN CTF 2026 | [bit_flips](pwn/0xFUN_CTF_2026/bit_flips/AI_WRITEUP.md) | 三次任意位翻转可先修改有符号循环计数器，扩展为大量翻转。 |
| 0xFUN CTF 2026 | [Fridge](pwn/0xFUN_CTF_2026/Fridge/AI_WRITEUP.md) | 32位gets栈溢出，固定PLT地址组成ret2libc。 |
| 0xFUN CTF 2026 | [phantom](pwn/0xFUN_CTF_2026/phantom/AI_WRITEUP.md) | 驱动释放物理页却保留用户mmap，形成页级UAF；多份来源还记录了不同本地flag包装。 |
| 0xFUN CTF 2026 | [Warden](pwn/0xFUN_CTF_2026/Warden/AI_WRITEUP.md) | Python AST黑名单与openat路径前缀检查同时存在语义缺口。 |
| 0xFUN CTF 2026 | [What you have](pwn/0xFUN_CTF_2026/What%20you%20have/AI_WRITEUP.md) | 一次任意地址写覆盖可写GOT，随后必经puts触发win。 |
| ApoorvCTF 2026 | [House_of_Wade](pwn/apoorvctf_2026/House_of_Wade/AI_WRITEUP.md) | cancel_order未清指针造成UAF读写，投毒0x30 tcache取得计数对象。 |
| ASIS CTF Quals 2026 | [Arena_Snapshots](pwn/asis_2026-quals/Arena_Snapshots/AI_WRITEUP.md) | ROLLBACK恢复类型元数据却不恢复payload，造成跨快照类型混淆。 |
| ASIS CTF Quals 2026 | [Dead_Letter](pwn/asis_2026-quals/Dead_Letter/AI_WRITEUP.md) | 取消队列只扫描环形数组尾段，回绕后遗留指向已释放槽的有效队列项。 |
| ASIS CTF Quals 2026 | [QFilter](pwn/asis_2026-quals/QFilter/AI_WRITEUP.md) | QuickJS customFilter跨回调保存失效数组指针，且以首元素类型决定全部引用计数。 |
| ASIS CTF Quals 2026 | [Signal_Race](pwn/asis_2026-quals/Signal_Race/AI_WRITEUP.md) | bookmark只核对generation低8位，结合可逆seal及SIGALRM检查点实现受保护frame篡改。 |
| b01lers CTF 2026 | [micromicromicropython](pwn/b01lers_CTF_2026/micromicromicropython/AI_WRITEUP.md) | MicroPython __build_class__把恶意__new__返回的小整数误作cell，构造任意写。 |
| b01lers CTF 2026 | [multifiles](pwn/b01lers_CTF_2026/multifiles/AI_WRITEUP.md) | 内核multifiles解法通过对象越界与slab布局操纵取得页表重叠，再修改core_pattern。 |
| b01lers CTF 2026 | [priority-queue](pwn/b01lers_CTF_2026/priority-queue/AI_WRITEUP.md) | edit固定写32字节而最短字符串分配块仅32字节，覆盖邻块size后制造堆重叠。 |
| b01lers CTF 2026 | [spelling-bee](pwn/b01lers_CTF_2026/spelling-bee/AI_WRITEUP.md) | Forth forget释放word但其他已编译word仍保存指针，形成UAF函数指针调用。 |
| b01lers CTF 2026 | [throughthewall](pwn/b01lers_CTF_2026/throughthewall/AI_WRITEUP.md) | fw_del_rule存在UAF，可重占为pipe_buffer并改变合并标志。 |
| b01lers CTF 2026 | [transmutation](pwn/b01lers_CTF_2026/transmutation/AI_WRITEUP.md) | 代码段可写的一次字节修改先改ret为nop，转为可重复自修改。 |
| BDSec CTF 2026 | [Muktir_Shongket](pwn/bdsec_2026/Muktir_Shongket/AI_WRITEUP.md) | ROUTE的验证和JIT执行语义不一致，可跳入SIGNAL的8字节立即数执行原生指令。 |
| BDSec CTF 2026 | [Phantom_Device](pwn/bdsec_2026/Phantom_Device/AI_WRITEUP.md) | duplicate新增设备句柄却未增加引用计数，release使另一句柄悬空。 |
| BSidesSF CTF 2026 | [blockman-builder](pwn/BSidesSF_CTF_2026/blockman-builder/AI_WRITEUP.md) | 关卡负坐标导致栈上world数组下溢，可覆盖load_level返回地址。 |
| BSidesSF CTF 2026 | [if-it-leads](pwn/BSidesSF_CTF_2026/if-it-leads/AI_WRITEUP.md) | 官方Ruby solver利用输出文件中的单字节泄漏逐位恢复程序口令。 |
| BSidesSF CTF 2026 | [inheritance](pwn/BSidesSF_CTF_2026/inheritance/AI_WRITEUP.md) | memfd未设置CLOEXEC，system子进程继承含flag的文件描述符。 |
| BSidesSF CTF 2026 | [nameme](pwn/BSidesSF_CTF_2026/nameme/AI_WRITEUP.md) | DNS服务题，具体利用链以官方Ruby solver为证据。 |
| BSidesSF CTF 2026 | [readme](pwn/BSidesSF_CTF_2026/readme/AI_WRITEUP.md) | 只读原语题，官方solver通过读取进程内存恢复目标数据。 |
| BSidesSF CTF 2026 | [readwritecallme](pwn/BSidesSF_CTF_2026/readwritecallme/AI_WRITEUP.md) | 读写和调用原语题，目标是调用程序内的隐藏函数。 |
| BSidesSF CTF 2026 | [readwriteme](pwn/BSidesSF_CTF_2026/readwriteme/AI_WRITEUP.md) | 移除win后的任意读写题，需要通过运行时内存恢复flag。 |
| BSidesSF CTF 2026 | [rugdoctor](pwn/BSidesSF_CTF_2026/rugdoctor/AI_WRITEUP.md) | RugDoctor JIT的分支距离溢出让控制流落入ADD立即数字节，实现JIT喷射。 |
| BSidesSF CTF 2026 | [wromwarp](pwn/BSidesSF_CTF_2026/wromwarp/AI_WRITEUP.md) | 切换ROM不重置寄存器和PC，复用Life计数器例程越界读取WRAM。 |
| BYUCTF 2026 | [bytecoin](pwn/BYUCTF_2026/bytecoin/AI_WRITEUP.md) | 错误hex长度计数泄漏复用栈缓冲区内HMAC密钥；AEAD认证失败返回值又被忽略。 |
| BYUCTF 2026 | [heap2win](pwn/BYUCTF_2026/heap2win/AI_WRITEUP.md) | 无限长scanf堆覆盖C++对象vptr，换成WinnerButton虚表。 |
| BYUCTF 2026 | [hextoint](pwn/BYUCTF_2026/hextoint/AI_WRITEUP.md) | 转换表负索引写越过数组起点，覆盖exit GOT为win。 |
| BYUCTF 2026 | [incontinent](pwn/BYUCTF_2026/incontinent/AI_WRITEUP.md) | 非终止字符串输出泄漏相邻保存的flag。 |
| BYUCTF 2026 | [intro2](pwn/BYUCTF_2026/intro2/AI_WRITEUP.md) | 输入直接作为格式串，通过泄漏main/栈地址和三次半字写改保存返回地址至win。 |
| COMPFEST CTF 2026 | [menfess](pwn/compfest_2026/menfess/AI_WRITEUP.md) | AArch64设备CREATE按对象总长校验却写入64字节content，72字节输入覆盖send_func；VIEW缺索引边界。 |
| COMPFEST CTF 2026 | [redis_cli_0_day](pwn/compfest_2026/redis_cli_0_day/AI_WRITEUP.md) | CLUSTER NODES未限制slot索引，形成从node+0x54起向前写固定字节1；两次伪大块重叠最终伪造hiredis析构回调。 |
| CSS CTF 2026: Return of Nexus | [Dockside_Ticket_Office](pwn/css_2026/Dockside_Ticket_Office/AI_WRITEUP.md) | cancel不清active_ticket，edit可覆盖票据+0x20处回调。 |
| CSS CTF 2026: Return of Nexus | [Maintenance_Log](pwn/css_2026/Maintenance_Log/AI_WRITEUP.md) | operator的0x21字节读仅改保存RBP低字节，结合report栈泄漏迁移到可控缓冲区。 |
| DiceCTF 2026 Quals | [bytecrusher](pwn/DiceCTF_Quals_2026/bytecrusher/AI_WRITEUP.md) | crush_string按步长跨越NUL导致栈字节泄漏，gets反馈溢出负责控制流。 |
| DiceCTF 2026 Quals | [message-store](pwn/DiceCTF_Quals_2026/message-store/AI_WRITEUP.md) | 颜色索引越界把函数表调用转为memcpy，复制0x1000字节到栈。 |
| GPN CTF 2026 | [Food_Inspector_II](pwn/gpn_2026/Food_Inspector_II/AI_WRITEUP.md) | Frida inline hook安装/卸载成为可控代码写，LIFO trampoline复用决定rel32中的目标字节。 |
| GPN CTF 2026 | [Scanwich_Station](pwn/gpn_2026/Scanwich_Station/AI_WRITEUP.md) | Python大图长度与quirc 32位像素索引不一致，越界标记破坏mmap chunk size，使free连带解除libc元数据映射。 |
| Haruulzangi CTF 2026 Qualifier | [Cabinet](pwn/haruulzangi_2026-quals/Cabinet/AI_WRITEUP.md) | 踩怪一次删1加2，边界判断使第6次生成第12号越界实体覆盖帧hook。 |
| Haruulzangi CTF 2026 Qualifier | [Formality](pwn/haruulzangi_2026-quals/Formality/AI_WRITEUP.md) | WRITE只检查临时输入缓冲长度，堆越界可伪造top；REQUEST信任新malloc的未初始化字节。 |
| Haruulzangi CTF 2026 Qualifier | [Made_In_Mongolia](pwn/haruulzangi_2026-quals/Made_In_Mongolia/AI_WRITEUP.md) | SFEX JIT参数数目不一致泄漏ABI残留值，符号碰撞保留旧IR使下次编译接受伪对象指针。 |
| Haruulzangi CTF 2026 Qualifier | [Payphone](pwn/haruulzangi_2026-quals/Payphone/AI_WRITEUP.md) | 录音路径穿越读取临时拨号进程环境和映射，配合无canary消息栈溢出。 |
| Haruulzangi CTF 2026 Qualifier | [Tenure](pwn/haruulzangi_2026-quals/Tenure/AI_WRITEUP.md) | FREE不清present/data形成Rust封装下的glibc UAF，目标是启动时分配的回调表。 |
| kBxAc CTF 2026 | [lets_get_to_library](pwn/kbxac_2026/lets_get_to_library/AI_WRITEUP.md) | 缺少pop rdi时复用main的rbp-0x80读入片段，实现指定地址写和多次栈迁移。 |
| kBxAc CTF 2026 | [Most_Secure_Bank_Of_Endia](pwn/kbxac_2026/Most_Secure_Bank_Of_Endia/AI_WRITEUP.md) | Flask限制Unicode字符数，C端按UTF-8字节处理，导致校验字段被可控超长字节覆盖。 |
| kBxAc CTF 2026 | [Original_Unlimited_Codex_100_Free](pwn/kbxac_2026/Original_Unlimited_Codex_100_Free/AI_WRITEUP.md) | bind别名UAF读、额外32字节越界读与amend尾NUL组合成Einherjar和tcache投毒。 |
| L3akCTF 2026 | [Bosh](pwn/l3akctf_2026/Bosh/AI_WRITEUP.md) | 一次RWX模块字节写会自禁用；修改自禁用行为及store指令可把它扩展为重复dword写。 |
| L3akCTF 2026 | [Piet](pwn/l3akctf_2026/Piet/AI_WRITEUP.md) | Piet的up/down可使数据栈别名到stack_depth，把合法运算转为原生栈寻址。 |
| L3akCTF 2026 | [Piet_2](pwn/l3akctf_2026/Piet_2/AI_WRITEUP.md) | Piet 2的roll未要求d<=stack_depth，可轮转未初始化原生栈数据并破坏保存RBP。 |
| L3akCTF 2026 | [Rudimentary_Calculator](pwn/l3akctf_2026/Rudimentary_Calculator/AI_WRITEUP.md) | scanf溢出先修改product_bignum_len，让大整数打印器泄漏栈。 |
| L3akCTF 2026 | [Supervisor](pwn/l3akctf_2026/Supervisor/AI_WRITEUP.md) | seccomp通知监督器模拟I/O的offset+count无符号回绕，令沙箱子进程读写父进程内存。 |
| LA CTF 2026 | [adventure](pwn/LACTF_2026/adventure/AI_WRITEUP.md) | 地图物品位置编码main指针；密码溢出结合history数组实现BSS栈迁移。 |
| LA CTF 2026 | [ourukla](pwn/LACTF_2026/ourukla/AI_WRITEUP.md) | 不初始化sinfo指针使重分配student引用旧数据，结合伪chunk形成重叠与tcache投毒。 |
| LA CTF 2026 | [refraction](pwn/LACTF_2026/refraction/AI_WRITEUP.md) | 构造异常展开的EH_FRAME/CIE/FDE与LSDA，利用DWARF表达式改恢复寄存器。 |
| LA CTF 2026 | [scrabasm](pwn/LACTF_2026/scrabasm/AI_WRITEUP.md) | 时间种子的rand决定字节手牌，可通过可预测换牌拼成14字节read shellcode。 |
| LA CTF 2026 | [tcademy](pwn/LACTF_2026/tcademy/AI_WRITEUP.md) | 超量note数据覆盖邻块size，伪大块释放泄漏libc，再投毒libc内部strlen槽。 |
| LA CTF 2026 | [this-is-how-you-pwn-the-time-war](pwn/LACTF_2026/this-is-how-you-pwn-the-time-war/AI_WRITEUP.md) | 官方solver通过半字写重入和随机输出恢复运行时指针，再写one_gadget。 |
| LA CTF 2026 | [tic-tac-no](pwn/LACTF_2026/tic-tac-no/AI_WRITEUP.md) | 官方解答只给两行坐标，第一行含负索引。 |
| LYKNCTF | [Ez_Pwn](pwn/lyknctf_2026/Ez_Pwn/AI_WRITEUP.md) | signed长度-1通过<=0x50校验，截断为byte后变255，导致栈溢出。 |
| LYKNCTF | [H34P_D3V1L](pwn/lyknctf_2026/H34P_D3V1L/AI_WRITEUP.md) | note管理off-by-one/UAF与safe-linking组合取得全局表任意读写。 |
| LYKNCTF | [Return_to_Lose](pwn/lyknctf_2026/Return_to_Lose/AI_WRITEUP.md) | 64字节栈缓冲接受256字节，无canary且无PIE，可直接ret2win。 |
| MntcrlCTF 2026 | [RepusPing](pwn/mntcrlctf_2026/RepusPing/AI_WRITEUP.md) | 3次任意读和1次任意写配合ld泄漏，覆盖经过指针加密的exit handler。 |
| NepCTF 2026 | [different_ROP](pwn/NepCTF%202026/47_different_ROP/AI_WRITEUP.md) | Hexagon静态ELF使用BSS分阶段ROP，避免不稳定的栈上syscall帧。 |
| NepCTF 2026 | [onlyone](pwn/NepCTF%202026/48_onlyone/AI_WRITEUP.md) | freelist与FSOP组合控制stdout/文件描述符，通过父进程管道取flag。 |
| NepCTF 2026 | [shadow_signal](pwn/NepCTF%202026/51_shadow_signal/AI_WRITEUP.md) | SIGSEGV handler的大读覆盖ucontext，以rt_sigreturn恢复攻击者寄存器。 |
| PascalCTF 2026 | [AHC - Average Heap Challenge](pwn/PascalCTF_2026/AHC%20-%20Average%20Heap%20Challenge/AI_WRITEUP.md) | 官方solver通过相邻对象溢出伪造0x71大小并重分配，写入胜利魔数。 |
| PascalCTF 2026 | [Grande Inutile Tool](pwn/PascalCTF_2026/Grande%20Inutile%20Tool/AI_WRITEUP.md) | 自制git checkout信任分支/提交中的路径，允许多级目录穿越复制/flag。 |
| PascalCTF 2026 | [Malta Nightlife](pwn/PascalCTF_2026/Malta%20Nightlife/AI_WRITEUP.md) | quantity*price的32位有符号计算回绕，绕过余额检查并增加余额。 |
| PascalCTF 2026 | [Packet Tracer 2](pwn/PascalCTF_2026/Packet%20Tracer%202/AI_WRITEUP.md) | 32字节无终止名称泄漏win_host；日志把1024字节消息strcpy到512字节字段。 |
| PascalCTF 2026 | [YetAnotherNoteTaker](pwn/PascalCTF_2026/YetAnotherNoteTaker/AI_WRITEUP.md) | note输出格式串先泄漏printf，再以%hn覆盖__malloc_hook为one_gadget。 |
| PwnSec CTF 2026 | [Freal_World_Manipulation](pwn/pwnsec_2026/Freal_World_Manipulation/AI_WRITEUP.md) | 浮点乘法溢出到infinity扩大索引上界，指针数组越界形成任意读写。 |
| PwnSec CTF 2026 | [JavaScript_After_Core](pwn/pwnsec_2026/JavaScript_After_Core/AI_WRITEUP.md) | JSC bailout重建数组时对象类型和Butterfly布局不一致，破坏相邻数组length。 |
| PwnSec CTF 2026 | [PHP_Sandbox_Escape](pwn/pwnsec_2026/PHP_Sandbox_Escape/AI_WRITEUP.md) | disable_functions不覆盖Pdo\Sqlite方法，允许上传后加载原生SQLite扩展。 |
| RITSEC CTF 2026 | [doMonkeysSwim](pwn/ritsec_2026/doMonkeysSwim/AI_WRITEUP.md) | 最终版本是无PIE静态程序，可用游戏输入溢出搭直接syscall ROP。 |
| SAS CTF 2026 Quals | [Snaking_Revenge](pwn/sas_2026-quals/Snaking_Revenge/AI_WRITEUP.md) | pyjnius对PythonJavaClass转Java参数缺类型核验，攻击者JAR可用FakeProxy访问真实Proxy内部字段。 |
| SekaiCTF 2026 | [echo_chamber](pwn/sekaictf_2026/echo_chamber/AI_WRITEUP.md) | Content-Length=-1转size_t后+1回绕，malloc(0)却继续大长度读取，造成跨线程堆溢出。 |
| SekaiCTF 2026 | [ppp](pwn/sekaictf_2026/ppp/AI_WRITEUP.md) | afc_receive_data的this_length超过entire_length造成堆溢出，复用释放list vector并覆盖可写puts GOT。 |
| squ1rrel CTF 2026 | [gaem](pwn/squ1rrel_2026/gaem/AI_WRITEUP.md) | rename溢出宠物回调到printf，再用格式串字节写改返回地址实现两级栈迁移。 |
| Srdnlen CTF 2026 Quals | [Common offset](pwn/Srdnlen_CTF_2026/Common%20offset/AI_WRITEUP.md) | uint16累加offset影响邻近文件索引，第二次写把索引越界到栈指针。 |
| Srdnlen CTF 2026 Quals | [Echo](pwn/Srdnlen_CTF_2026/Echo/AI_WRITEUP.md) | 输入off-by-one先改相邻8位长度，再用扩展写泄漏canary和libc。 |
| Srdnlen CTF 2026 Quals | [Linx](pwn/Srdnlen_CTF_2026/Linx/AI_WRITEUP.md) | 正则无限长捕获复制到固定0x40大小类chunk，形成堆越界；两轮safe-linking tcache投毒泄漏environ并覆盖栈返回地址。 |
| Srdnlen CTF 2026 Quals | [Registered Stack](pwn/Srdnlen_CTF_2026/Registered%20Stack/AI_WRITEUP.md) | 仅允许寄存器push/pop的汇编检查仍允许把代码当数据，借RSP变化构造自修改。 |
| SUCTF 2026 | [SU_Box](pwn/SUCTF_2026/SU_Box/AI_WRITEUP.md) | J2V8捆绑V8 9.3.345.11且未指针压缩，旧hole leak漏洞可造成Map混淆。 |
| SUCTF 2026 | [SU_Chronos_Ring](pwn/SUCTF_2026/SU_Chronos_Ring/AI_WRITEUP.md) | DETACH_FILE切换为LOCAL但不清sync_view，COMMIT_SYNC仍写原只读文件page cache。 |
| SUCTF 2026 | [SU_Chronos_Ring1](pwn/SUCTF_2026/SU_Chronos_Ring1/AI_WRITEUP.md) | 同Chronos Ring生命周期错配，Ring1目录另提供可审阅的exp.c。 |
| SUCTF 2026 | [SU_evbuffer](pwn/SUCTF_2026/SU_evbuffer/AI_WRITEUP.md) | gethostname未初始化栈泄漏与inet_pton遇NUL截断组合，溢出user_buf覆盖bev。 |
| SUCTF 2026 | [SU_minivfs](pwn/SUCTF_2026/SU_minivfs/AI_WRITEUP.md) | 未初始化VFS块泄漏地址，off-by-null合并重叠后largebin修改tcache配置，再FSOP。 |
| SunshineCTF 2026 | [Cache_Money](pwn/sunshinectf_2026/Cache_Money/AI_WRITEUP.md) | Transfer释放源ledger后把悬空指针交给目标，Withdraw/Deposit提供UAF读写。 |
| SunshineCTF 2026 | [Code_Breaker](pwn/sunshinectf_2026/Code_Breaker/AI_WRITEUP.md) | 协议密钥由公开R和自选C派生，LINK/DELETE错误引用计数造成UAF。 |
| SunshineCTF 2026 | [Homemaker](pwn/sunshinectf_2026/Homemaker/AI_WRITEUP.md) | 命令2复制count+1字节，把CRC写入capacity低字节，升级为栈泄漏和大溢出。 |
| SunshineCTF 2026 | [Print_Print_Revolution](pwn/sunshinectf_2026/Print_Print_Revolution/AI_WRITEUP.md) | 自制printf的%w不是%n，而是将下一参数qword直接写到本参数指针。 |
| SunshineCTF 2026 | [Safe_House](pwn/sunshinectf_2026/Safe_House/AI_WRITEUP.md) | 父进程SUBMIT栈控制与子记录服务负句柄组合，跨socketpair读取受保护system记录。 |
| SunshineCTF 2026 | [Total_Recall](pwn/sunshinectf_2026/Total_Recall/AI_WRITEUP.md) | 静态小程序栈溢出配read返回值15触发sigreturn，无需libc或可执行栈。 |
| TAMUctf 2026 | [goodbye-libc](pwn/TAMUctf_2026/goodbye-libc/AI_WRITEUP.md) | 数字数组接受负索引，读取栈/PIE并写返回控制，复用自制libc函数片段构造任意写。 |
| TAMUctf 2026 | [meep](pwn/TAMUctf_2026/meep/AI_WRITEUP.md) | MIPS大端先格式串泄漏，再命令栈溢出控制s0/ra调用libc gadget。 |
| TAMUctf 2026 | [military-system](pwn/TAMUctf_2026/military-system/AI_WRITEUP.md) | ARM64 channel关闭后draft指针悬空，编辑截断使tcache链可投毒至auth块。 |
| TAMUctf 2026 | [task-manager](pwn/TAMUctf_2026/task-manager/AI_WRITEUP.md) | 任务链表指针覆盖结合释放复用，逐步泄漏堆/栈/canary/libc并将分配导向栈。 |
| TAMUctf 2026 | [zagjail](pwn/TAMUctf_2026/zagjail/AI_WRITEUP.md) | Zag指针偏移检查不完整，且数组栈空间按初始化项数而非声明长度分配。 |
| Thryve CTF 2026 | [abyss-oracle](pwn/Thryve_CTF_2026/abyss-oracle/AI_WRITEUP.md) | 别名保活、retire状态升级和merge权限组合绕过能力系统，oracle帮助解码指针后可任意内核读写。 |
| Thryve CTF 2026 | [secret-door](pwn/Thryve_CTF_2026/secret-door/AI_WRITEUP.md) | vector<void*>混放raw config和AnimeStream，URL更新与play缺类型核验。 |
| TraceBash CTF 2026 | [Banned_Bytes](pwn/tracebash_2026/Banned_Bytes/AI_WRITEUP.md) | 栈溢出受坏字符过滤且服务使用PTY，需同时编码文件名与转义传输控制字节。 |
| TraceBash CTF 2026 | [Legacy_Ledger](pwn/tracebash_2026/Legacy_Ledger/AI_WRITEUP.md) | 启动泄漏buf与balance，deposit/withdraw格式串可%hn写saved RIP，栈可执行。 |
| TRX CTF 2026 | [down_the_line](pwn/trx_2026/down_the_line/AI_WRITEUP.md) | 实模式分配器把size表放到不可写硬件映射区，使尺寸记录错误并导致越界。 |
| TRX CTF 2026 | [house_of_fishing](pwn/trx_2026/house_of_fishing/AI_WRITEUP.md) | 无输出的UAF/copy堆题用smallbin stashing unlink避开safe-linking泄漏要求。 |
| TRX CTF 2026 | [krwd](pwn/trx_2026/krwd/AI_WRITEUP.md) | workqueue延迟copy_to_user未绑定请求者地址空间，可能借用特权进程mm写入其内存。 |
| TRX CTF 2026 | [triforce](pwn/trx_2026/triforce/AI_WRITEUP.md) | 修改后的Maglev类型检查缺陷用于建立V8沙箱内读写，再改变同一String通过三轮比较。 |
| UIUCTF 2026 | [Firefly_Complete_Combustion](pwn/uiuctf_2026/Firefly_Complete_Combustion/AI_WRITEUP.md) | Lua FORLOOP未检验tag，仅改payload的chgivalue造成字符串/表/C函数类型混淆。 |
| UIUCTF 2026 | [Sparxie_Vanishing_Encore](pwn/uiuctf_2026/Sparxie_Vanishing_Encore/AI_WRITEUP.md) | Spotlight Pass的BLAKE2s未覆盖route，结合重复clip迁移留下的旧studio页引用取得draft池视图。 |
| UMassCTF 2026 | [Brick_City_Office_Space](pwn/umassctf_2026/Brick_City_Office_Space/AI_WRITEUP.md) | 32位printf(user_input)结合可写GOT，可先读libc再把printf改system。 |
| UMDCTF 2026 | [bookmaker](pwn/umdctf_2026/bookmaker/AI_WRITEUP.md) | Ledger.view暴露native buf，recycle释放后旧ArrayBuffer仍可访问，复用为Wire。 |
| UMDCTF 2026 | [vkexchange](pwn/umdctf_2026/vkexchange/AI_WRITEUP.md) | Vulkan descriptor索引未校验，在mesa22.3固定host_arena布局下越界覆盖clearing SSBO描述符。 |
| UofTCTF 2026 | [aes-aead](pwn/UofTCTF_2026/aes-aead/AI_WRITEUP.md) | 自制AEAD标签更新可伪造加长密文，引发长度越界与堆重叠，再走FSOP。 |
| UofTCTF 2026 | [babybof](pwn/UofTCTF_2026/babybof/AI_WRITEUP.md) | 最短solver以24字节前缀覆盖保存返回地址至0x4011fb。 |
| UofTCTF 2026 | [calculator](pwn/UofTCTF_2026/calculator/AI_WRITEUP.md) | 计算表达式和reset序列造成堆元数据重用泄漏，投毒stdin后扩大输入范围覆盖stdout。 |
| UofTCTF 2026 | [eebpf](pwn/UofTCTF_2026/eebpf/AI_WRITEUP.md) | eBPF ARSH范围分析与实际执行不一致，验证器认为偏移0而运行得到1。 |
| UofTCTF 2026 | [uprobe](pwn/UofTCTF_2026/uprobe/AI_WRITEUP.md) | uprobe允许在指令中间插入0xcc，修改libc读取passwd的lea位移。 |
| WRECKCTF 2026 | [vellum](pwn/wreckctf_2026/vellum/AI_WRITEUP.md) | 已下载文件是未完成starter skeleton，只接收动态ELF和显示符号，尚无完整利用。 |
| z0d1ak CTF Qualifiers | [paperweight](pwn/z0d1ak_2026-quals/paperweight/AI_WRITEUP.md) | Poppler tile位图按目标几何分配、按源图尺寸写入，CTM失配产生大幅堆越界。 |
| z0d1ak CTF Qualifiers | [rapture](pwn/z0d1ak_2026-quals/rapture/AI_WRITEUP.md) | snapshot浅复制data及读写票据，释放一份后另一份继续UAF并刷新操作次数。 |
| 第十届“强网杯”全国网络安全挑战赛·线上赛 | [Easytl](pwn/%E7%AC%AC%E5%8D%81%E5%B1%8A%E2%80%9C%E5%BC%BA%E7%BD%91%E6%9D%AF%E2%80%9D%E5%85%A8%E5%9B%BD%E7%BD%91%E7%BB%9C%E5%AE%89%E5%85%A8%E6%8C%91%E6%88%98%E8%B5%9B%C2%B7%E7%BA%BF%E4%B8%8A%E8%B5%9B/Easytl/AI_WRITEUP.md) | OpenSSL三个回调共用指针/长度，PSK数据指针与SNI长度混搭导致日志栈溢出。 |
| 第十届“强网杯”全国网络安全挑战赛·线上赛 | [Oldsvr](pwn/%E7%AC%AC%E5%8D%81%E5%B1%8A%E2%80%9C%E5%BC%BA%E7%BD%91%E6%9D%AF%E2%80%9D%E5%85%A8%E5%9B%BD%E7%BD%91%E7%BB%9C%E5%AE%89%E5%85%A8%E6%8C%91%E6%88%98%E8%B5%9B%C2%B7%E7%BA%BF%E4%B8%8A%E8%B5%9B/Oldsvr/AI_WRITEUP.md) | MIPS64大端MQTT的长度截断、news UAF和16位广播分配溢出组合，劫持entry表取得任意写。 |

### 虚拟化（49）

| 比赛 | 题目 | 核心机制 |
|---|---|---|
| ApoorvCTF 2026 | [Draw_Me](%E8%99%9A%E6%8B%9F%E5%8C%96/apoorvctf_2026/Draw_Me/AI_WRITEUP.md) | 关键是重建顺序执行的 VM：GPU 每帧只保留最后一次写入，导致自修改代码及显存输出丢失；空画面不能说明字节码没有有效结果。 |
| ASIS CTF Quals 2026 | [ASIS_Arch](%E8%99%9A%E6%8B%9F%E5%8C%96/asis_2026-quals/ASIS_Arch/AI_WRITEUP.md) | PC 相关指令混淆还原后，校验等价于 22 个 16 位字的十轮可逆变换；可选取每个输出字等于目标的充分条件，逐轮逆运算。 |
| ASIS CTF Quals 2026 | [Revenant_buddy](%E8%99%9A%E6%8B%9F%E5%8C%96/asis_2026-quals/Revenant_buddy/AI_WRITEUP.md) | 0xD9 的执行器可复制受保护值，但 verifier 将结果标为 ordinary，造成抽象类型与运行时值不一致。两次类型洗白即可同时提供 capability 和 mix(capability)。 |
| b01lers CTF 2026 | [piano](%E8%99%9A%E6%8B%9F%E5%8C%96/b01lers_2026/piano/AI_WRITEUP.md) | 36 条链表的长度表示输入字节；INSERT/DELETE 表示加减，93 种 BULK 函数是仿射变换。完整建模后可用线性方程求解，避免逐节点执行大量信号。 |
| b01lers CTF 2026 | [favorite_potato](%E8%99%9A%E6%8B%9F%E5%8C%96/b01lers_CTF_2026/favorite_potato/AI_WRITEUP.md) | 程序将10000轮可逆ARX完全展开；识别PHP/PLP包围的栈原语后，可提取常量并从尾到头求逆，无须枚举24位状态。 |
| b01lers CTF 2026 | [indirect-memory-access](%E8%99%9A%E6%8B%9F%E5%8C%96/b01lers_CTF_2026/indirect-memory-access/AI_WRITEUP.md) | 官方sol.py把DMA源地址对应的重叠数据窗口还原为13种二输入逻辑门，再将整段检查转为Z3布尔约束。 |
| b01lers CTF 2026 | [kyotoprotocol](%E8%99%9A%E6%8B%9F%E5%8C%96/b01lers_CTF_2026/kyotoprotocol/AI_WRITEUP.md) | 二进制不断改写运行中的Bash脚本形成VM；JUMP/NEXT/EXPORT传递参数和环境变量。去虚拟化后是9×9扫雷与每行、列、宫各3颗雷的组合约束。 |
| BDSec CTF 2026 | [Borrowed_Memory](%E8%99%9A%E6%8B%9F%E5%8C%96/bdsec_2026/Borrowed_Memory/AI_WRITEUP.md) | 输入实际是0x4000加表内偏移。2048字节伪随机表经过补丁成为指令带；逐步校验和可作为模拟器正确性的检查点。 |
| BYUCTF 2026 | [mixed_signals](%E8%99%9A%E6%8B%9F%E5%8C%96/BYUCTF_2026/mixed_signals/AI_WRITEUP.md) | mixed_signals保存输入状态，program发送信号作为VM操作码；两个进程共同完成恒定时间校验，单独启动其中一个不足以验证。 |
| Cryovault 2026 Quals | [Kelpie](%E8%99%9A%E6%8B%9F%E5%8C%96/cryovault_2026-quals/Kelpie/AI_WRITEUP.md) | 两层可逆VM之间由HMAC-SHA256派生AES-256-GCM密钥；有效解法依赖官方hint提供派生密钥。没有hint时，第一层可逆性本身无法约束输入。 |
| Cryovault 2026 Quals | [thaw_ladder](%E8%99%9A%E6%8B%9F%E5%8C%96/cryovault_2026-quals/thaw_ladder/AI_WRITEUP.md) | SEAL有int16有符号边界缺陷；工作量计数可经余数对齐变成前缀匹配oracle；比较地址又经过洗牌，必须分别恢复字节与地址。 |
| CSS CTF 2026: Return of Nexus | [prince_walk](%E8%99%9A%E6%8B%9F%E5%8C%96/css_2026/prince_walk/AI_WRITEUP.md) | 目标坐标999999,999999为16寄存器VM的密钥种子，8320条加密指令重建128字节输出；最终长度和FNV-1a给出独立校验。 |
| DiceCTF 2026 Quals | [locked_in](%E8%99%9A%E6%8B%9F%E5%8C%96/dicectf_2026-quals/locked_in/AI_WRITEUP.md) | 并发逻辑可归约为逐字符变换及有限状态搜索；关键在逆序字节、EPERM返回值和障碍判定方向，不能按表面汇编常量直接建模。 |
| DiceCTF 2026 Quals | [garden](%E8%99%9A%E6%8B%9F%E5%8C%96/DiceCTF_Quals_2026/garden/AI_WRITEUP.md) | GC将空引用误当作4字节对象参与压缩，破坏只向低地址移动的假设；逐对象memmove覆盖相邻对象头，可在普通数组和off-heap数组之间制造类型混淆。 |
| Haruulzangi CTF 2026 Qualifier | [Automaton](%E8%99%9A%E6%8B%9F%E5%8C%96/haruulzangi_2026-quals/Automaton/AI_WRITEUP.md) | 211字节数据段包括42字节目标、9字节密钥生成程序、160字节加密主程序；RC4仅用于KSA生成S-box，主变换可逐步求逆。 |
| L3akCTF 2026 | [LattiaVM](%E8%99%9A%E6%8B%9F%E5%8C%96/l3akctf_2026/LattiaVM/AI_WRITEUP.md) | push无上界，DUP在sp=256时第二次push写到别名sp字段，使可控值变成原生栈索引；SWAP可据此读写保存返回地址。 |
| L3akCTF 2026 | [LattiaVM_2](%E8%99%9A%E6%8B%9F%E5%8C%96/l3akctf_2026/LattiaVM_2/AI_WRITEUP.md) | push无上界，DUP在sp=256时第二次push写到别名sp字段，使可控值变成原生栈索引；SWAP可据此读写保存返回地址。 |
| LA CTF 2026 | [helm-hell](%E8%99%9A%E6%8B%9F%E5%8C%96/LA_CTF_2026/helm-hell/AI_WRITEUP.md) | 652KB辅助模板把Brainfuck的纸带、指针与递归循环映射为Go模板操作；字符期望值隐藏在计数与循环中。 |
| LA CTF 2026 | [reflection](%E8%99%9A%E6%8B%9F%E5%8C%96/LA_CTF_2026/reflection/AI_WRITEUP.md) | 主程序只panic，真正的检查在.eh_frame的DW_CFA_val_expression中；115字节预检查决定是否进入12888字节表达式VM。 |
| NCTF 2026 | [VM Encryptor](%E8%99%9A%E6%8B%9F%E5%8C%96/NCTF_2026/VM%20Encryptor/AI_WRITEUP.md) | 官方PDF第76–79页给出VM结构、指令枚举和逆算法；校验是24位循环移位/XOR后的Base64，再逐字节异或0x63。 |
| NepCTF 2026 | [ColorfulArray](%E8%99%9A%E6%8B%9F%E5%8C%96/NepCTF%202026/36_ColorfulArray/AI_WRITEUP.md) | 原文短叙述称图游走/PRNG，实际附带脚本是带掩码的16位状态约束DFS：必须以代码数据流解释，而不是照抄模糊叙述。 |
| NepCTF 2026 | [T.A.S P.W.N](%E8%99%9A%E6%8B%9F%E5%8C%96/NepCTF%202026/42_T.A.S%20P.W.N/AI_WRITEUP.md) | 原文复用bluescreen影片的guest链及XOR keystream，将184字节HIMITSU宿主body的调用目标改为WinExec(calc)，flag由主办验收签发。 |
| PascalCTF 2026 | [StrangeVM](%E8%99%9A%E6%8B%9F%E5%8C%96/PascalCTF_2026/StrangeVM/AI_WRITEUP.md) | 可确认的思路是按奇偶索引撤销加减，但原文本身存在多处矛盾：奇数位正向文字写input-1，逆代码却写target+i，且展示flag长度并非40。 |
| PwnSec CTF 2026 | [ICX_Confusion](%E8%99%9A%E6%8B%9F%E5%8C%96/pwnsec_2026/ICX_Confusion/AI_WRITEUP.md) | pack将Note变为Job但保留旧View，导致类型混淆；认证值是可重算的23位算法，攻击者可修改token和manifest并重新封装。 |
| PwnSec CTF 2026 | [ICX_Regulate](%E8%99%9A%E6%8B%9F%E5%8C%96/pwnsec_2026/ICX_Regulate/AI_WRITEUP.md) | GMI检查器跳过低字节为ff/00的某些分支目标，可将禁用OCTPACK藏在LDI立即数再跳入执行；该指令能传播来源mark而不改变请求数值。 |
| PwnSec CTF 2026 | [PwnSec_Support](%E8%99%9A%E6%8B%9F%E5%8C%96/pwnsec_2026/PwnSec_Support/AI_WRITEUP.md) | 工单ID拼接SQL允许堆叠语句创建管理员session，admin Lua的note_save提供guest任意32位写；修补ticks返回类型将写原语转为字符串读。 |
| PwnSec CTF 2026 | [Zigerions](%E8%99%9A%E6%8B%9F%E5%8C%96/pwnsec_2026/Zigerions/AI_WRITEUP.md) | ELF→PyInstaller PE→VMProtect PE→落地文件；GameBoy ROM中的巨型VM是不可达诱饵，真实结果来自畸形ELF中的AES密钥与48字节密文。 |
| SCTF 2026 | [babel_furnace](%E8%99%9A%E6%8B%9F%E5%8C%96/SCTF_2026/babel_furnace/AI_WRITEUP.md) | Host、Python code object、bridge.pyd、Rust engine各持有部分share；单独分析engine会得到不完整opcode/立即数。组合后640条micro-op归约为6个uint64的14轮可逆变换。 |
| SCTF 2026 | [BrainfOok](%E8%99%9A%E6%8B%9F%E5%8C%96/SCTF_2026/BrainfOok/AI_WRITEUP.md) | Python负索引、独立跳转栈、原地修改和数十亿次低层操作使直接迁移/全量trace容易失真；应保存状态分段推进，保留跳转覆盖区后去冗余。 |
| SekaiCTF 2026 | [3in1](%E8%99%9A%E6%8B%9F%E5%8C%96/SekaiCTF_2026/3in1/AI_WRITEUP.md) | 可读JS利用Set.intersection回调中clear/GC引发悬空元素，再伪造对象和ArrayBuffer数据指针获得进程读写；后续两个QEMU阶段以Base64 ELF嵌入，原作者文章缓存仅有简介。 |
| SekaiCTF 2026 | [MTE](%E8%99%9A%E6%8B%9F%E5%8C%96/SekaiCTF_2026/MTE/AI_WRITEUP.md) | 核心原语不是任意写，而是在保留24字节canary的kmalloc-96对象+0x40写固定值2；以unix_vertex.scc_index为目标诱发AF_UNIX GC和悬空oob_skb，升级为任意地址单字节读取。 |
| squ1rrel CTF 2026 | [squ1rrel_o_tron_2](%E8%99%9A%E6%8B%9F%E5%8C%96/squ1rrel_2026/squ1rrel_o_tron_2/AI_WRITEUP.md) | PDF JavaScript的VM又运行组合子解释器，逐层模拟太慢；抽取等价16位轮函数可将大量解释步骤化简为每输入12轮。 |
| Srdnlen CTF 2026 Quals | [Dantes_Trial](%E8%99%9A%E6%8B%9F%E5%8C%96/srdnlen_2026-quals/Dantes_Trial/AI_WRITEUP.md) | 169字节字节码封装读字符和散列循环，真正难点是正确模拟ARM移位加法链后再穷举短输入。 |
| Srdnlen CTF 2026 Quals | [Cornflake v3.5](%E8%99%9A%E6%8B%9F%E5%8C%96/Srdnlen_CTF_2026_Quals/Cornflake%20v3.5/AI_WRITEUP.md) | RC4用户名门槛只是第一层；第二层栈VM以CMP结果自修改下一条失败opcode，所有成功路径可表达为输入算式约束。 |
| SUCTF 2026 | [SU_Lock](%E8%99%9A%E6%8B%9F%E5%8C%96/SUCTF_2026/SU_Lock/AI_WRITEUP.md) | Rust安装载荷用RC4(SUCTF2026)解出用户态PE与驱动；IOCTL0x222004返回XXTEA变体参数，0x222008检查密文，驱动VM仅包装常量写出和相等判断。 |
| SUCTF 2026 | [SU_MvsicPlayer](%E8%99%9A%E6%8B%9F%E5%8C%96/SUCTF_2026/SU_MvsicPlayer/AI_WRITEUP.md) | 真正路径在Electron native vm_encryptor.node；SVM4头后是64字节块的四轮Feistel/Speck混合，每块密钥由前一密文两半异或派生，非CBC。 |
| SUCTF 2026 | [SU_West](%E8%99%9A%E6%8B%9F%E5%8C%96/SUCTF_2026/SU_West/AI_WRITEUP.md) | NOR VM是模板化的ARX约束载体，每轮64位输入经Feistel和组合器映射到该层target；层间s0和flag解密状态相连，不能把81层独立乱序求解。 |
| SunshineCTF 2026 | [IntMod](%E8%99%9A%E6%8B%9F%E5%8C%96/sunshinectf_2026/IntMod/AI_WRITEUP.md) | SIGTRAP/SIGILL/SIGFPE通过ucontext改真实寄存器；90条可逆混合后用40个模65521的多项式约束检查40字节状态。 |
| Thryve CTF 2026 | [chimera-mirrors](%E8%99%9A%E6%8B%9F%E5%8C%96/Thryve_CTF_2026/chimera-mirrors/AI_WRITEUP.md) | 外层228条指令调度88个真检查器，前48个分别只依赖一个输入字节，所以每个检查尝试256值即可；其余40个联合检查用于验证。 |
| Thryve CTF 2026 | [parallax](%E8%99%9A%E6%8B%9F%E5%8C%96/Thryve_CTF_2026/parallax/AI_WRITEUP.md) | phase在每条指令后随状态变化，错误占位符会使后续字节被错误解码；逐条满足三字符断言并从头重放比一次性反汇编可靠。 |
| Thryve CTF 2026 | [soul](%E8%99%9A%E6%8B%9F%E5%8C%96/Thryve_CTF_2026/soul/AI_WRITEUP.md) | 复杂八轮key检查最终仅压缩为一个字节，ACCESS GRANTED不保证解密正确。真正可利用的信息是51字节密文的16字节重复密钥XOR及已知格式。 |
| TRX CTF 2026 | [1+1](%E8%99%9A%E6%8B%9F%E5%8C%96/trx_2026/1%2B1/AI_WRITEUP.md) | 官方C程序对相邻哈希状态枚举4字节原像，Python脚本以固定seed重建S/P盒并逆SPN，再用可打印性筛选候选。 |
| TRX CTF 2026 | [wandering](%E8%99%9A%E6%8B%9F%E5%8C%96/trx_2026/wandering/AI_WRITEUP.md) | 收录的官方替代solver采用随机最小冲突交换搜索，保证行列唯一，只迭代修复对角线；它没有解释题目为何归为VM，因此不补造虚拟机漏洞。 |
| UMDCTF 2026 | [gnalekcip](%E8%99%9A%E6%8B%9F%E5%8C%96/umdctf_2026/gnalekcip/AI_WRITEUP.md) | BINPERSID递归解析嵌套pickle且共享memo，形成寄存器文件和子程序；原文最终答案依赖题名/部分转录猜测，未提供可独立重做的完整hash逆解。 |
| UMDCTF 2026 | [roulette](%E8%99%9A%E6%8B%9F%E5%8C%96/umdctf_2026/roulette/AI_WRITEUP.md) | CRT与VM输出只依赖已知索引、查表和前轮状态，每轮input_word=VM_output XOR target，因此无需逆散列。 |
| UofTCTF 2026 | [Bring Your Own Program](%E8%99%9A%E6%8B%9F%E5%8C%96/UofTCTF_2026/Bring%20Your%20Own%20Program/AI_WRITEUP.md) | GETMETH缓存对象槽位，OPTIMIZE按keyId重排存储却未更新缓存版本；第二次经过同一取方法位置，旧槽位被解释为另一方法，形成能力检查绕过。 |
| z0d1ak CTF Qualifiers | [House_XIII](%E8%99%9A%E6%8B%9F%E5%8C%96/z0d1ak_2026-quals/House_XIII/AI_WRITEUP.md) | 两类对象同为0x180大小，转换释放重分配却保留旧槽；VM可向后读头部，旧类型写入口可修改新类型callback字段。随机secret又被<比较暴露。 |
| z0d1ak CTF Qualifiers | [Salvage_Protocol](%E8%99%9A%E6%8B%9F%E5%8C%96/z0d1ak_2026-quals/Salvage_Protocol/AI_WRITEUP.md) | reclaimd分离保存真实body长度与声明长度，vaultd按声明长度解析多个请求；AUTH在校验token前更新connection_clearance且失败不回滚。 |
| z0d1ak CTF Qualifiers | [stars_below](%E8%99%9A%E6%8B%9F%E5%8C%96/z0d1ak_2026-quals/stars_below/AI_WRITEUP.md) | 导入重定位被洗牌并配合LD_BIND_NOT使PLT标签误导；真实算法为8!路线搜索、BLAKE2s派生、两个可逆ARX VM及短MAC。 |

### 车联网（18）

| 比赛 | 题目 | 核心机制 |
|---|---|---|
| NDIAS Automotive/IoT CTF | [AGL 1](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%201/AI_WRITEUP.md) | 目标是从 Automotive Grade Linux 镜像找出第一个 flag。线索来自串口登录画面的 5900/tcp 提示；启动脚本的 `-vnc :0` 表明 GUI 已通过 VNC 导出。flag 位于仪表盘图标本身，不需要破解系统口令。 |
| NDIAS Automotive/IoT CTF | [AGL 2](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%202/AI_WRITEUP.md) | 目标是恢复同一AGL镜像里的第二个flag。Camera页面只是线索展示，实际信息在JPEG的EXIF User Comment字段中，以Base64编码。 |
| NDIAS Automotive/IoT CTF | [AGL 3](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%203/AI_WRITEUP.md) | 目标是从AGL媒体资源恢复第三个flag。播放器中有音频，但QEMU默认启动未转发声音；提示藏在MP3末尾的人声及NATO字母拼读中。 |
| NDIAS Automotive/IoT CTF | [AGL 4](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%204/AI_WRITEUP.md) | 目标是拼接分散在三个非主分区的flag片段。`/root/.hint.txt`提示可疑分区；各分区文件系统不同，单次strings或只看根分区会遗漏。 |
| NDIAS Automotive/IoT CTF | [AGL 5](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%205/AI_WRITEUP.md) | 目标是读取KUKSA Data Broker中的41个字符。VSS JSON仅定义信号名称，值由启动服务动态写入，因此grep配置文件无法直接拿到完整flag。 |
| NDIAS Automotive/IoT CTF | [Classic KeeLoq Garage - Find the Key](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Classic%20KeeLoq%20Garage%20-%20Find%20the%20Key/AI_WRITEUP.md) | 目标是由RF固定字段和安装备注恢复64位DeviceKey。备注直接给出Legacy派生式，不能将此题描述成攻击完整64位KeeLoq密钥空间。 |
| NDIAS Automotive/IoT CTF | [Classic KeeLoq Garage - Next HOP](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Classic%20KeeLoq%20Garage%20-%20Next%20HOP/AI_WRITEUP.md) | 目标是用已恢复的DeviceKey解密并递增Hop计数器，再重新加密生成下一OPEN帧。 |
| NDIAS Automotive/IoT CTF | [Gateway Gremlins](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Gateway%20Gremlins/AI_WRITEUP.md) | 目标是串联遗留Web漏洞和CAN鉴权。Web链泄露算法，CAN nonce使密钥具有时效；仅拿到配置不等于完成解锁。 |
| NDIAS Automotive/IoT CTF | [I Saw Our Time Pass](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/I%20Saw%20Our%20Time%20Pass/AI_WRITEUP.md) | 目标是从CAN日志中重组ISO-TP ZIP，并从协议控制字段提取四层压缩包密码。负载中有大量假flag，真正内容在0x702的四重ZIP里。 |
| NDIAS Automotive/IoT CTF | [Next Counter](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Next%20Counter/AI_WRITEUP.md) | 目标是预测另一Falcon X1设备下一次Unlock帧。重复发射不代表计数器每帧递增，计数器按按钮操作递增。 |
| NDIAS Automotive/IoT CTF | [Parking Lot Whisper](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Parking%20Lot%20Whisper/AI_WRITEUP.md) | 目标是识别Falcon X1遥控器的中心频率、调制方式和最短符号周期。采样为433.92MHz中心、2Msps、复数float32小端，文件交替存I/Q。 |
| NDIAS Automotive/IoT CTF | [Predict Next UNLOCK](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Predict%20Next%20UNLOCK/AI_WRITEUP.md) | 目标是同时预测16位计数器和附加滚动字段。后者是可观察的模2^16等差序列，并非需要破解的强密码。 |
| NDIAS Automotive/IoT CTF | [RAMN ECU D](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/RAMN%20ECU%20D/AI_WRITEUP.md) | 目标是通过UDS 0x29证书认证读取DID4E44。给定证书过期但验证逻辑正确；漏洞在嵌入的两个RSA根证书模数共用素因子，可以恢复根CA私钥并重签有效证书。 |
| NDIAS Automotive/IoT CTF | [Read the simple fob](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Read%20the%20simple%20fob/AI_WRITEUP.md) | 目标是恢复Manchester帧中同步字D5后的3字节Device ID，输入与Parking Lot Whisper相同。 |
| NDIAS Automotive/IoT CTF | [Real KeeLoq Garage - Next HOP](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Real%20KeeLoq%20Garage%20-%20Next%20HOP/AI_WRITEUP.md) | 目标是生成下次OPEN的逻辑帧。需要区分射频34bit固定字段和判题期待的32bit button+serial表示。 |
| NDIAS Automotive/IoT CTF | [Real KeeLoq Garage - Normal Learn](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Real%20KeeLoq%20Garage%20-%20Normal%20Learn/AI_WRITEUP.md) | 目标是从HCS301兼容固定字段及制造商代码派生DeviceKey。与Classic题不同，本题是Normal Learn，且34位固定部不可简单按整字节截断。 |
| NDIAS Automotive/IoT CTF | [Seed-Key Leak](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Seed-Key%20Leak/AI_WRITEUP.md) | 目标是逆向dealer_unlock.pyc中的UDS SecurityAccess算法，通过0x27解锁后读取DID1337。核心是32位旋转、加法与异或；这不是暴力猜测seed。 |
| NDIAS Automotive/IoT CTF | [VIN Hunter](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/VIN%20Hunter/AI_WRITEUP.md) | 目标是通过CAN上的UDS读取VIN数据标识符F190，题目把flag放在该DID中。关键是先发现请求/响应CAN ID，再通过ISO-TP承载UDS。 |

### iot（16）

| 比赛 | 题目 | 核心机制 |
|---|---|---|
| 0xFUN CTF 2026 | [UART](iot/0xFUN_2026/UART/AI_WRITEUP.md) | 目标是从Sigrok逻辑采样还原UART字节并解出flag。`.sr`本来就是ZIP容器，不应将ZIP结构本身误判为题目伪装。 |
| ASIS CTF Quals 2026 | [OutOfPhase](iot/asis_2026-quals/OutOfPhase/AI_WRITEUP.md) | 目标是从相位编码的OFDM类WAV中恢复消息。编码器oopenc定义了载波置换、QPSK旋转、分块顺序及差分相位；呼号是所有伪随机变换的种子。 |
| ASIS CTF Quals 2026 | [Silent_Carrier](iot/asis_2026-quals/Silent_Carrier/AI_WRITEUP.md) | 目标是联合USB配置抓包与DMR IQ信号恢复隐藏莫尔斯音频。关键是TYT Enhanced Privacy对49bit AMBE数据施加固定异或掩码，而非直接对PCM做AES解密。 |
| NDIAS Automotive/IoT CTF | [D's Signpost](iot/NDIAS_2026/D%27s%20Signpost/AI_WRITEUP.md) | 目标是从五路混合RF信号恢复加密ZIP与密码。输入SigMF为cf32_le、500ksps、中心915MHz，关键信息分属+115kHz的APRS和+170kHz的DQPSK。 |
| NDIAS Automotive/IoT CTF | [Suspicious device 1](iot/NDIAS_2026/Suspicious%20device%201/AI_WRITEUP.md) | 目标是从SD卡中的ARM iot-agent恢复通信协议，发现残留DEBUG_EXEC命令。入口不是题面给出的云地址，而是固件中的连接逻辑与provision.bin配置。 |
| NDIAS Automotive/IoT CTF | [Suspicious device 2](iot/NDIAS_2026/Suspicious%20device%202/AI_WRITEUP.md) | 目标是利用上一题已有的命令执行能力，找到内部数据库中的第二阶段flag。需要先读拓扑与现成查询工具，不能假设公网可以直接访问DB。 |
| NDIAS Automotive/IoT CTF | [Suspicious device 3](iot/NDIAS_2026/Suspicious%20device%203/AI_WRITEUP.md) | 目标是在内部DB主机读取受flagreader组保护的stage3文件。链路为数据库泄露维护账户→内部SSH→SGID工具的TOCTOU，权限提升目标是组读取能力。 |
| NDIAS Automotive/IoT CTF | [Tiny crackme](iot/NDIAS_2026/Tiny%20crackme/AI_WRITEUP.md) | 目标是恢复FLAG{30字符}输入。CTF任务的ECC相关哈希看似很强，但UART任务在每5字符处检查CRC32，泄露6个短块的约束，提供更小的搜索空间。 |
| NepCTF 2026 | [虚验室制取稀硫酸](iot/NepCTF%202026/23_%E8%99%9A%E9%AA%8C%E5%AE%A4%E5%88%B6%E5%8F%96%E7%A8%80%E7%A1%AB%E9%85%B8/AI_WRITEUP.md) | 目标仅限题目软PLC仿真：让真实模拟反应釜温度>90、液位>100，同时SIEM不报警，flag出现在TUI公告板。直接篡改过程显示值不能满足物理过程判定。 |
| NepCTF 2026 | [赛博心情电梯](iot/NepCTF%202026/24_%E8%B5%9B%E5%8D%9A%E5%BF%83%E6%83%85%E7%94%B5%E6%A2%AF/AI_WRITEUP.md) | 目标仅限CEIBA软PLC电梯仿真：在门实际开启时完成跨层运动并满足题目判定。关键是形成真实行程后再影响门联锁，单独伪造关门位不会让READY状态的轿厢移动。 |
| NepCTF 2026 | [UnknownFirmware](iot/NepCTF%202026/37_UnknownFirmware/AI_WRITEUP.md) | 目标是把Telink/KNLT固件中的显示缓冲恢复为二维码。已有solver是启发式位图扫描，而非完整Telink指令集反编译。 |
| NepCTF 2026 | [谁引闪了我的灯](iot/NepCTF%202026/46_%E8%B0%81%E5%BC%95%E9%97%AA%E4%BA%86%E6%88%91%E7%9A%84%E7%81%AF/AI_WRITEUP.md) | 目标是根据ESP32/Godox引闪协议信息组16字节帧，再对指定十六进制文本做MD5。必须区分原始字节与HEX字符串、以及大小写。 |
| SUCTF 2026 | [SU_EzRouter](iot/SUCTF_2026/SU_EzRouter/AI_WRITEUP.md) | 现有材料只有exp.py。它的静态行为是先借auth参数取得session，再安排WiFi/黑名单状态，最后提交含amd64 shellcode的VPN配置；漏洞根因需要结合CGI二进制进一步确认。 |
| SUCTF 2026 | [SU_老年固件](iot/SUCTF_2026/SU_%E8%80%81%E5%B9%B4%E5%9B%BA%E4%BB%B6/AI_WRITEUP.md) | 现有writeup是分层固件提取分析记录，不是完整flag解答。可确认old.bin经单字节XOR7F后包含U-Boot风格头、XZ流与SMALLFW容器。 |
| UMassCTF 2026 | [Brick_by_Brick](iot/umassctf_2026/Brick_by_Brick/AI_WRITEUP.md) | 目标是把时间戳/逻辑电平CSV解为UART，再从伪Linux启动日志取HEX编码flag。核心参数约30us/bit、33333baud、8N1、LSB-first。 |
| UMassCTF 2026 | [Smart_Brick_v2](iot/umassctf_2026/Smart_Brick_v2/AI_WRITEUP.md) | 目标是从KiCad PCB网表模拟组合逻辑。7个输入位、19个LED，每个LED仅对一个ASCII值亮起，按D1—D19的触发字符拼flag。 |

### android（13）

| 比赛 | 题目 | 核心机制 |
|---|---|---|
| BKISC CTF 2026 | [Boring_APK](android/bkisc_2026/Boring_APK/AI_WRITEUP.md) | 目标是解开APK资源后反演native的27步图路径状态机，得到27字符输入。Java层主要负责AES-GCM资产解密，实际校验位于arm64 libnative.so。 |
| BSidesSF CTF 2026 | [doremi](android/BSidesSF%20CTF%202026/doremi/AI_WRITEUP.md) | 目标是读取藏在VectorDrawable中的紫色文字。默认紫色背景让flag与背景重合，绿色文字是干扰；正确音高仅改变背景颜色，不产生解密密钥。 |
| BSidesSF CTF 2026 | [vinyl-drop](android/BSidesSF%20CTF%202026/vinyl-drop/AI_WRITEUP.md) | 目标是构造被Firebase Cloud Function接受的收据QR。校验字段只有当前UID、购买金额和时间，客户端输入缺少不可伪造的购买凭据绑定。 |
| BYUCTF 2026 | [back_and_forth](android/BYUCTF%202026/back_and_forth/AI_WRITEUP.md) | 目标是拼合Java、SQLite、JNI和Rust/Wasm各层的局部校验。不同check约束不同输入片段，应先建立索引表，再按容易的局部约束求解。 |
| D^3CTF 2026 | [d3llvm](android/D%5E3CTF%202026/d3llvm/AI_WRITEUP.md) | 目标是恢复64个十六进制字符组成的token，并重建手写模型生成的隐藏secret来解flag。通过nativeVerifyInput或把游戏分数改为100本身不足以得到正确AES密钥。 |
| LYKNCTF | [I_HATE_THIS_APP](android/lyknctf_2026/I_HATE_THIS_APP/AI_WRITEUP.md) | 目录归类为Android，但本地writeup明确描述Windows x64 Tauri/Rust PE。本题目标是识别防截图所调用的Windows API名称，非Android FLAG_SECURE。 |
| LYKNCTF | [I_HATE_THIS_APP_REVENGE](android/lyknctf_2026/I_HATE_THIS_APP_REVENGE/AI_WRITEUP.md) | 实际平台是Windows Tauri/Rust PE。目标是恢复AES-256-CTR加密图片中的角色名；关键是嵌入默认key与非连续的IV布局。 |
| NCTF 2026 | [Hook My Secret](android/NCTF_2026/Hook%20My%20Secret/AI_WRITEUP.md) | 目标是从NativeBridge的前缀相关输出恢复16字符stage2 key，再用数据库IV解stage3 AES。stage1图案解锁只影响界面流程，不参与最终密钥推导。 |
| SCTF 2026 | [GuardMaster](android/SCTF_2026/GuardMaster/AI_WRITEUP.md) | 目标是从GMX容器恢复hidden DEX，再逆native终态编码和Java的77次64字节状态变换，恢复规范化后的输入。代码混淆不改变每层可逆数据流，但漏一层会产生自洽假解。 |
| Securinets CTF Quals 2026 | [Backdrop](android/Securinets%20CTF%20Quals%202026/Backdrop/AI_WRITEUP.md) | 目标是让Flutter flag页面正常显示，或离线解密签名绑定的资产。题目诱导文件声称6位PIN和strings可解，但真实障碍是计时器及故意选择的Impeller GLES崩溃路径。 |
| SekaiCTF 2026 | [SekaiID](android/SekaiCTF_2026/SekaiID/AI_WRITEUP.md) | 目标是读取Verifier管理界面使用的/system/flag.txt。原文实际成功路径利用android:debuggable=true通过ADB run-as获得Verifier UID，无需完成文中猜测的复杂IPC链。 |
| SekaiCTF 2026 | [ufo](android/SekaiCTF_2026/ufo/AI_WRITEUP.md) | 目标是激活五种功能留下的ambient_trace bitmask，显露隐藏二维码并恢复缺失的QR结构。修改会员状态与本题数据流无关。 |
| SUCTF 2026 | [SU_flumel](android/SUCTF_2026/SU_flumel/AI_WRITEUP.md) | 目标是逆Dart RC4 Warp→native AES-CBC校验链。Hermes bundle虽然执行了大量代码，但作者明确说明其自定义16字节算法未接入最终验证；bundle字节仍参与AES key/IV派生。 |

## 重复与待补入口

| 状态 | 题目目录 |
|---|---|
| 原文待补 | [逆向/volgactf_2026-quals/Vision](%E9%80%86%E5%90%91/volgactf_2026-quals/Vision/AI_WRITEUP.md) |
| 重复副本 | [pwn/sekaictf_2026/MTE](pwn/sekaictf_2026/MTE/AI_WRITEUP.md) |
| 原文待补 | [pwn/SUCTF_2026/SU_fullchian](pwn/SUCTF_2026/SU_fullchian/AI_WRITEUP.md) |
| 原文待补 | [pwn/trx_2026/slop_allocator](pwn/trx_2026/slop_allocator/AI_WRITEUP.md) |
| 原文待补 | [pwn/Undutmaning_2026/Flytväst](pwn/Undutmaning_2026/Flytv%C3%A4st/AI_WRITEUP.md) |
| 原文待补 | [pwn/Undutmaning_2026/GIF Splitter](pwn/Undutmaning_2026/GIF%20Splitter/AI_WRITEUP.md) |
| 重复副本 | [虚拟化/dicectf_2026-quals/garden](%E8%99%9A%E6%8B%9F%E5%8C%96/dicectf_2026-quals/garden/AI_WRITEUP.md) |
