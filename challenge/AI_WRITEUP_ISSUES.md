# 资料问题与复现缺口

以下记录来自逐题分析，包含版本依赖、未收录脚本、原文缺漏及待核验结论。出现条目不代表该题无解；应按具体说明补材料或验证。所有题目均未在本次运行。

| 分类 | 题目 | 限制与核验要求 |
|---|---|---|
| 逆向 | [Atarude](%E9%80%86%E5%90%91/asis_2026-quals/Atarude/AI_WRITEUP.md) | 调试补丁只用于采集输入，不构成最终验证通过；互补掩码局部通过仍可能最终失败。 |
| 逆向 | [Beyond_the_fourth_wall](%E9%80%86%E5%90%91/asis_2026-quals/Beyond_the_fourth_wall/AI_WRITEUP.md) | 原文最终从主题直接给键，缺少完整自动求解推导；不要把主题猜测当成可复现算法。RISC-V符号扩展不能按无符号32位处理。 |
| 逆向 | [Collector](%E9%80%86%E5%90%91/asis_2026-quals/Collector/AI_WRITEUP.md) | 输入按四个16位字小端打包，不能简单反转整串十六进制；flag.enc在原文中是干扰项。 |
| 逆向 | [LeakMeAk](%E9%80%86%E5%90%91/asis_2026-quals/LeakMeAk/AI_WRITEUP.md) | 四字节按大端打包，所有中间运算截断32位；不能独立解组后忽略跨组表状态。 |
| 逆向 | [Lesh](%E9%80%86%E5%90%91/asis_2026-quals/Lesh/AI_WRITEUP.md) | 需32位Windows兼容环境；补丁只用于原文指定路径，断点过早或过晚均得到伪值。 |
| 逆向 | [Mousa](%E9%80%86%E5%90%91/asis_2026-quals/Mousa/AI_WRITEUP.md) | Go元数据损坏导致启动失败不阻止静态求解；MAC通过本身不足以唯一确定key。 |
| 逆向 | [NEON](%E9%80%86%E5%90%91/asis_2026-quals/NEON/AI_WRITEUP.md) | 不能概括为所有ARX哈希可逆；这里是特定可逆轮函数。第7动作rewind改变VM执行顺序，UI顺序不能直接当状态顺序。 |
| 逆向 | [shakespeares-revenge](%E9%80%86%E5%90%91/b01lers_CTF_2026/shakespeares-revenge/AI_WRITEUP.md) | 这是解释器语义中的整数截断与系统调用接口组合，不能仅根据题目分类写成普通字符串校验。 |
| 逆向 | [tiles--ai](%E9%80%86%E5%90%91/b01lers_CTF_2026/tiles--ai/AI_WRITEUP.md) | 脚本读取src/puzzles.txt，应调整为真实附件位置；不能把静态参考答案套到不同棋盘。 |
| 逆向 | [Easy_RE_Challenge](%E9%80%86%E5%90%91/bdsec_2026/Easy_RE_Challenge/AI_WRITEUP.md) | 博客含另外两题，AFLAG/BFLAG/CFLAG不是本题真实结果；旋转必须限制8位。 |
| 逆向 | [Night_Shift](%E9%80%86%E5%90%91/bdsec_2026/Night_Shift/AI_WRITEUP.md) | 不能依靠操作系统随机线程调度；输入明确指定执行顺序。博客中Borrowed Memory属于其他题。 |
| 逆向 | [Captain_Morgan](%E9%80%86%E5%90%91/bearcat_2026/Captain_Morgan/AI_WRITEUP.md) | 按位取反必须明确位宽；不要把混淆变量的赋值顺序改变。 |
| 逆向 | [Missing_One_Piece](%E9%80%86%E5%90%91/bearcat_2026/Missing_One_Piece/AI_WRITEUP.md) | 绝对路径启动会改变argv[0]；只改文件名不足以同时满足PWD和环境变量。 |
| 逆向 | [Pollys_Key](%E9%80%86%E5%90%91/bearcat_2026/Pollys_Key/AI_WRITEUP.md) | 只通过Ruby或只通过Perl均不足够；key本身不是最终flag。 |
| 逆向 | [Dont_unpack_me](%E9%80%86%E5%90%91/bhackari_2026/Dont_unpack_me/AI_WRITEUP.md) | 第三方DLL具体版本与架构决定字节；文章标题称4-byte patches，但正文明确四个8字节槽，应以反汇编核验。 |
| 逆向 | [Mystery](%E9%80%86%E5%90%91/bhackari_2026/Mystery/AI_WRITEUP.md) | 修改so会改变自身哈希；easy_access的BhackariCTF是诱饵，不能当作结果。 |
| 逆向 | [AlphaCode](%E9%80%86%E5%90%91/boroctf_2026/AlphaCode/AI_WRITEUP.md) | 该解答依赖服务DSL行为；仅有全文博客时，六opcode的确切语法应继续查阅本题章节，不能照搬相邻五道题的输入。 |
| 逆向 | [angr_management](%E9%80%86%E5%90%91/BYUCTF_2026/angr_management/AI_WRITEUP.md) | 最短CFG路径不自动等于可行输入，必须使用原文的边筛选规则。 |
| 逆向 | [picklerick](%E9%80%86%E5%90%91/BYUCTF_2026/picklerick/AI_WRITEUP.md) | 本题与Python pickle反序列化无关；未知token一律0是原solver假设，应核对题目字典。 |
| 逆向 | [rcaas](%E9%80%86%E5%90%91/BYUCTF_2026/rcaas/AI_WRITEUP.md) | 原solver补充了多处字符3与下界，需区分来自程序的条件和人工猜测；本轮未安装服务。 |
| 逆向 | [yara](%E9%80%86%E5%90%91/BYUCTF_2026/yara/AI_WRITEUP.md) | 现有README只有求解方向和结果，未附完整约束推导；详细约束必须来自附件rule.yar。 |
| 逆向 | [ITS_ME_BURHAN](%E9%80%86%E5%90%91/compfest_2026/ITS_ME_BURHAN/AI_WRITEUP.md) | 连接随机种子变化会改变路线和密码；不可把示例状态当常量。所引Solve.java若未收录需按原文实现。 |
| 逆向 | [rime_scrub](%E9%80%86%E5%90%91/cryovault_2026-quals/rime_scrub/AI_WRITEUP.md) | 每连接key不同且掩码每scrub刷新；不能逐个读两份share。150次预算包括解锁步骤。 |
| 逆向 | [FLAPPY_BOARD](%E9%80%86%E5%90%91/css_2026/FLAPPY_BOARD/AI_WRITEUP.md) | 服务地址已脱敏且可能失效；表单不是JSON，尾部多一个换行也会导致回放拒绝。 |
| 逆向 | [another-onion](%E9%80%86%E5%90%91/DiceCTF_2026_Quals/another-onion/AI_WRITEUP.md) | 示例8层与正式256层的转移指令和BSS范围不同；模板匹配后还需执行最终验证。 |
| 逆向 | [bedtime](%E9%80%86%E5%90%91/DiceCTF_2026_Quals/bedtime/AI_WRITEUP.md) | Python加法与按位与优先级要显式括号；PRNG状态跨局延续，不能每局重置。 |
| 逆向 | [explorer](%E9%80%86%E5%90%91/DiceCTF_2026_Quals/explorer/AI_WRITEUP.md) | 需要对应内核及initramfs；状态2不是成功，不能直接读flag。 |
| 逆向 | [Ehlel](%E9%80%86%E5%90%91/haruulzangi_2026-quals/Ehlel/AI_WRITEUP.md) | STATE不消费流序号，首DATA应ACK服务STATE序号减1；离线附件不包含远端文件。 |
| 逆向 | [Furnace](%E9%80%86%E5%90%91/haruulzangi_2026-quals/Furnace/AI_WRITEUP.md) | 2^38不适合直接Python暴力；端序、奇数乘法逆与xor-shift逆必须保持64位。 |
| 逆向 | [Trace](%E9%80%86%E5%90%91/haruulzangi_2026-quals/Trace/AI_WRITEUP.md) | 软件断点修改代码字节会改变下一段密钥；不要把信号异常当程序损坏。 |
| 逆向 | [Patcher_1](%E9%80%86%E5%90%91/kbxac_2026/Patcher_1/AI_WRITEUP.md) | 每文件预算和允许地址范围独立，必须对原始文件逐字节比较；不能以patch条目数代替变更字节数。 |
| 逆向 | [Patcher_2](%E9%80%86%E5%90%91/kbxac_2026/Patcher_2/AI_WRITEUP.md) | call与jmp栈行为不同，首题成立依赖特定布局；其他程序不能无条件套用同一补丁。 |
| 逆向 | [Shherrr](%E9%80%86%E5%90%91/kbxac_2026/Shherrr/AI_WRITEUP.md) | 不必求隐藏分支触发输入；直接解数据仅证明明文恢复，不等价于已复现交互入口。 |
| 逆向 | [simphell](%E9%80%86%E5%90%91/kbxac_2026/simphell/AI_WRITEUP.md) | 漏去tag会读错字段；key首字节不在短列表中而由调用方传入。 |
| 逆向 | [Ouroboros](%E9%80%86%E5%90%91/kubstu_2026/Ouroboros/AI_WRITEUP.md) | activation key为16字节，KDF拼接长度16+32+1+8=57；不能混用两slice代码哈希和密文。 |
| 逆向 | [RISC_V.](%E9%80%86%E5%90%91/kubstu_2026/RISC_V/AI_WRITEUP.md) | 反汇编器将自定义word标invalid不代表无用数据；它们改变实际控制流。 |
| 逆向 | [flag-finder](%E9%80%86%E5%90%91/LA_CTF_2026/flag-finder/AI_WRITEUP.md) | 像素字形存在leet歧义，必须同时保留解出的网格作为证据。 |
| 逆向 | [lactf-1986](%E9%80%86%E5%90%91/LA_CTF_2026/lactf-1986/AI_WRITEUP.md) | 单凭可打印明文不能接受；自引用哈希条件是必要检查。 |
| 逆向 | [ooo](%E9%80%86%E5%90%91/LA_CTF_2026/ooo/AI_WRITEUP.md) | 社区文档比赛年份与目录不同，且对最后一对约束存在讨论；不要手工替换看似相同的o字符。 |
| 逆向 | [starless-c](%E9%80%86%E5%90%91/LA_CTF_2026/starless-c/AI_WRITEUP.md) | 静态存在跳转不等于目标页已映射；忽略缺页会产生不可执行解。 |
| 逆向 | [the-fish](%E9%80%86%E5%90%91/LA_CTF_2026/the-fish/AI_WRITEUP.md) | 对这个有限输入验证不需要证明Collatz猜想；不能把社区泛化描述当数学定理。 |
| 逆向 | [the-three-sat-problem](%E9%80%86%E5%90%91/LA_CTF_2026/the-three-sat-problem/AI_WRITEUP.md) | 社区称2848子句并删除其中一条的做法未构成正确性证明，应以原检查器或修正提取器验证。 |
| 逆向 | [Control_Freak_1](%E9%80%86%E5%90%91/lyknctf_2026/Control_Freak_1/AI_WRITEUP.md) | 必须保留+3r和旋转中的+r；错误正反函数彼此抵消的round-trip不能证明符合原程序。 |
| 逆向 | [Control_Freak_2](%E9%80%86%E5%90%91/lyknctf_2026/Control_Freak_2/AI_WRITEUP.md) | 原文混合公式的括号与所称FNV常量存在表述疑点；实现必须对照反汇编，不能按无括号文字猜优先级。 |
| 逆向 | [Waguri2](%E9%80%86%E5%90%91/lyknctf_2026/Waguri2/AI_WRITEUP.md) | 解释器应保持8位cell语义；不能用是否有输出判断成功。 |
| 逆向 | [No My Bank!](%E9%80%86%E5%90%91/NCTF_2026/No%20My%20Bank%21/AI_WRITEUP.md) | 直接逆静态TEA是诱饵；动态加载器参数涉及std::string/SSO ABI。原PDF图像含额外定位信息。 |
| 逆向 | [Pay For 2048](%E9%80%86%E5%90%91/NCTF_2026/Pay%20For%202048/AI_WRITEUP.md) | 游戏上下文和会话token是额外条件；本地源码require路径应相对解包根目录。 |
| 逆向 | [鸡爪流高手](%E9%80%86%E5%90%91/NCTF_2026/%E9%B8%A1%E7%88%AA%E6%B5%81%E9%AB%98%E6%89%8B/AI_WRITEUP.md) | 空棋盘直接认输不扣分，不能用它执行真正败局；DEFAULT_FLAG是本地演示占位值。 |
| 逆向 | [compile_me_maybe](%E9%80%86%E5%90%91/NepCTF%202026/19_compile_me_maybe/AI_WRITEUP.md) | 原文给header与main，但完整约束推导较简略；不能把改main直接打印flag当解原题。 |
| 逆向 | [【Game】共生（本地）](%E9%80%86%E5%90%91/NepCTF%202026/70_%E3%80%90Game%E3%80%91%E5%85%B1%E7%94%9F%EF%BC%88%E6%9C%AC%E5%9C%B0%EF%BC%89/AI_WRITEUP.md) | 完成场景本身不等于拥有正确事件历史；本文未运行游戏验证自然路径。 |
| 逆向 | [【Game】共生（联机）](%E9%80%86%E5%90%91/NepCTF%202026/72_%E3%80%90Game%E3%80%91%E5%85%B1%E7%94%9F%EF%BC%88%E8%81%94%E6%9C%BA%EF%BC%89/AI_WRITEUP.md) | 服务地址是历史实例；TooEarly需检查状态，不应无限重试同一不合法完成包。 |
| 逆向 | [Albo delle Eccellenze](%E9%80%86%E5%90%91/PascalCTF_2026/Albo%20delle%20Eccellenze/AI_WRITEUP.md) | 不能笼统称所有输入都接受，仍需通过字段解析；本地Could not open flag已说明到达读文件路径。 |
| 逆向 | [Operation_Split_Horizon](%E9%80%86%E5%90%91/pwnsec_2026/Operation_Split_Horizon/AI_WRITEUP.md) | 不得只读一个通道或乱序解C2；缺PCAP/中间数据时无法复算。本文仅离线分析捕获材料。 |
| 逆向 | [Two_Worlds_One_Heart](%E9%80%86%E5%90%91/pwnsec_2026/Two_Worlds_One_Heart/AI_WRITEUP.md) | 仅按PE的32位架构反编译会漏掉后一半；真实执行需要WOW64。 |
| 逆向 | [Buried_Treasure](%E9%80%86%E5%90%91/ritsec_2026/Buried_Treasure/AI_WRITEUP.md) | 不能照文字中的(table[i]-i)/13实现；准确公式以汇编和最终solver为证据。 |
| 逆向 | [not_quite_optimal](%E9%80%86%E5%90%91/ritsec_2026/not_quite_optimal/AI_WRITEUP.md) | 任意幂塔都把指数直接模256并不普遍正确；原文稳定迭代技巧必须针对本题参数验证。 |
| 逆向 | [obfpyscated](%E9%80%86%E5%90%91/ritsec_2026/obfpyscated/AI_WRITEUP.md) | 图片若缺失或被压缩/改尺寸，坐标解码失效；不要直接exec不明中间层来代替分析。 |
| 逆向 | [T_reasure_Chest](%E9%80%86%E5%90%91/ritsec_2026/T_reasure_Chest/AI_WRITEUP.md) | 原文关于34字节/8字节对齐也有表述冲突；应读完整密文长度与程序memcmp参数，不能只处理非整块34字节。 |
| 逆向 | [F_K](%E9%80%86%E5%90%91/scriptctf_2026/F_K/AI_WRITEUP.md) | 最终挂起不是失败判据；本题与同博客的Misdirection密码题无关。 |
| 逆向 | [Alice](%E9%80%86%E5%90%91/SCTF_2026/Alice/AI_WRITEUP.md) | 欠定系统求出的一个不可打印模型不等于该长度无任何可打印解；唯一性应结合全部约束排除第二模型。 |
| 逆向 | [ghost_projection](%E9%80%86%E5%90%91/SCTF_2026/ghost_projection/AI_WRITEUP.md) | 补丁开放oracle不是把验证强改成功；logger需保留寄存器与调用约定，单纯dump可能保留错误地址。 |
| 逆向 | [Zombie_progression](%E9%80%86%E5%90%91/SCTF_2026/Zombie_progression/AI_WRITEUP.md) | 等效魔方动作写法会产生不同parser digest；多进程爆破要限制资源并正确回收子进程。 |
| 逆向 | [Chibile](%E9%80%86%E5%90%91/sekaictf_2026/Chibile/AI_WRITEUP.md) | 阶段nonce、sid和attestation必须对应同连接；本轮未加载驱动或连接历史服务。 |
| 逆向 | [Untitled_Encore](%E9%80%86%E5%90%91/sekaictf_2026/Untitled_Encore/AI_WRITEUP.md) | 同博客含11题，勿把其他题flag或区块链利用混入；hash为自定义，不能换成标准SHA。 |
| 逆向 | [redactr](%E9%80%86%E5%90%91/squ1rrel_2026/redactr/AI_WRITEUP.md) | 量化可能多解，不能宣称精确唯一原图；license分支数学恒假且不改变blur。 |
| 逆向 | [squ1rrel_o_tron](%E9%80%86%E5%90%91/squ1rrel_2026/squ1rrel_o_tron/AI_WRITEUP.md) | 标准QEMU不支持这两条指令；不可将SIGILL归因于普通加载错误。远程每轮时限5秒。 |
| 逆向 | [Artistic warmup](%E9%80%86%E5%90%91/Srdnlen_CTF_2026_Quals/Artistic%20warmup/AI_WRITEUP.md) | DIB可能自底向上；字体渲染环境差异可能影响逐像素验证，读图后仍需保持确切字符。 |
| 逆向 | [Rev Juice](%E9%80%86%E5%90%91/Srdnlen_CTF_2026_Quals/Rev%20Juice/AI_WRITEUP.md) | 本题并非唯一解；不要把history数组直接当正向投币序列，也不要把累计投币次数等同持有硬币数。 |
| 逆向 | [SU_easygal](%E9%80%86%E5%90%91/SUCTF_2026/SU_easygal/AI_WRITEUP.md) | 不能沿用旧14节点穷举；原文绝对E盘路径是作者环境，需改为本地附件路径。 |
| 逆向 | [SU_Protocol](%E9%80%86%E5%90%91/SUCTF_2026/SU_Protocol/AI_WRITEUP.md) | 父进程explorer.exe/cmd.exe可将delta改为0x9E3779B0；静态值未必是运行值，hash对象层级不能错。 |
| 逆向 | [SU_revird](%E9%80%86%E5%90%91/SUCTF_2026/SU_revird/AI_WRITEUP.md) | 标准AES库不能直接替代魔改轮函数；CheckRemoteDebuggerPresent会污染后续API hash。 |
| 逆向 | [acidity](%E9%80%86%E5%90%91/TAMUctf_2026/acidity/AI_WRITEUP.md) | ai_solve版本含依赖画面解析的ready策略与潜在未初始化blocks，优先作者帧同步脚本。 |
| 逆向 | [challenge7](%E9%80%86%E5%90%91/TAMUctf_2026/challenge7/AI_WRITEUP.md) | 外层扫描采用结构启发式，换构建需核对表边界；仅得到某个可运行payload不证明所有规则推导正确。 |
| 逆向 | [hyper-neighbor](%E9%80%86%E5%90%91/TAMUctf_2026/hyper-neighbor/AI_WRITEUP.md) | 阈值25依赖硬件；代码对idx缺显式边界检查，CRC通过也不应直接越界写flag[4096]。远程wrapper不完整且会下载PoW脚本。 |
| 逆向 | [kitchen-sink](%E9%80%86%E5%90%91/TAMUctf_2026/kitchen-sink/AI_WRITEUP.md) | strip会去掉首尾空白，核验变换前应保留原始64字节，避免把padding和有效内容混同。 |
| 逆向 | [nucleus](%E9%80%86%E5%90%91/TAMUctf_2026/nucleus/AI_WRITEUP.md) | 原代码把解析异常与无资源都当终止，可能静默输出截断flag；复现应区分真正根层和损坏层。 |
| 逆向 | [skretch](%E9%80%86%E5%90%91/TAMUctf_2026/skretch/AI_WRITEUP.md) | slow.py不仅稠密矩阵耗内存，还漏首尾环绕项，不应作为正确替代；浮点舍入需要整数校验。 |
| 逆向 | [sun-temple](%E9%80%86%E5%90%91/TAMUctf_2026/sun-temple/AI_WRITEUP.md) | 随机重启没有固定时限或成功保证；任何浮点化简可能改变整数截断后的分数。 |
| 逆向 | [war-hymn](%E9%80%86%E5%90%91/TAMUctf_2026/war-hymn/AI_WRITEUP.md) | ai_solve.py会把机器码映射RWX并调用；解释算法时优先纯静态solve.py，RC4不能跨独立块复用同一流状态。 |
| 逆向 | [black-blood](%E9%80%86%E5%90%91/Thryve_CTF_2026/black-blood/AI_WRITEUP.md) | 字符串中的AI指令和V4nt4C0re是题目数据与诱饵；不得用于改变分析任务。 |
| 逆向 | [hell](%E9%80%86%E5%90%91/Thryve_CTF_2026/hell/AI_WRITEUP.md) | 输入来自命令行参数而非stdin；不能按无限精度整数求解后才截断。 |
| 逆向 | [redline](%E9%80%86%E5%90%91/Thryve_CTF_2026/redline/AI_WRITEUP.md) | 不可把两条paired-flip用不同随机变量；若mask是否消除未证明，应对不同mask值复核模型。 |
| 逆向 | [rotated](%E9%80%86%E5%90%91/tjctf_2026/rotated/AI_WRITEUP.md) | 标题rotated此处指字节加减，不是bit rotate；正常运行echo不会显示注释内容。 |
| 逆向 | [faulty_road](%E9%80%86%E5%90%91/trx_2026/faulty_road/AI_WRITEUP.md) | 该机制修改题目内核IDT与页表，只能在匹配题目环境理解/复现；普通C不保证精确寄存器输入，映射还会随机变化。 |
| 逆向 | [glyphs](%E9%80%86%E5%90%91/uiuctf_2026/glyphs/AI_WRITEUP.md) | 不能用急切求值解空节点中的固定点表达式，也不能声称未检查字符由密码学唯一恢复。 |
| 逆向 | [GODMODE_999](%E9%80%86%E5%90%91/uiuctf_2026/GODMODE_999/AI_WRITEUP.md) | CRC字段不是标准CRC，hashlib.sha256也不等价；one_button_clear是未提交诱饵。 |
| 逆向 | [vector_cache](%E9%80%86%E5%90%91/uiuctf_2026/vector_cache/AI_WRITEUP.md) | 只追父进程会漏mode1；吞掉SIGILL会阻止整个checker运行。 |
| 逆向 | [Veil_of_Evernight](%E9%80%86%E5%90%91/uiuctf_2026/Veil_of_Evernight/AI_WRITEUP.md) | patch只用于临时副本采集数据；如果采用优化ARX checker，先与原输出四word交叉验证。 |
| 逆向 | [Batcave_Bitflips](%E9%80%86%E5%90%91/umassctf_2026/Batcave_Bitflips/AI_WRITEUP.md) | 原文声称0x43与0x44只差1bit不正确，其XOR为0x07有3bit；不影响两已知数组XOR的直接恢复。 |
| 逆向 | [nuclear_codes](%E9%80%86%E5%90%91/umdctf_2026/nuclear_codes/AI_WRITEUP.md) | 原文没有完整解释如何求得大整数三元组，只提供验证证书；近似exp/log描述不能替代最终严格推导。 |
| 逆向 | [rainbet](%E9%80%86%E5%90%91/umdctf_2026/rainbet/AI_WRITEUP.md) | 签名覆盖的是准确规范化状态串，不能任意JSON序列化；新会话和回合号变化需重新预测。 |
| 逆向 | [the_akari](%E9%80%86%E5%90%91/umdctf_2026/the_akari/AI_WRITEUP.md) | 现有writeup不是完整独立解谜算法；PCLMULQDQ只是原文对预期解的推测，不能当已证明步骤。 |
| 逆向 | [Baby (Obfuscated) Flag Checker](%E9%80%86%E5%90%91/UofTCTF_2026/Baby%20%28Obfuscated%29%20Flag%20Checker/AI_WRITEUP.md) | 原solver exec加载未知Python，未在本轮运行；若其他字符串方法或隐式转换存在，代理语义需补全。 |
| 逆向 | [ML Connoisseur](%E9%80%86%E5%90%91/UofTCTF_2026/ML%20Connoisseur/AI_WRITEUP.md) | 通道mix须可逆；浮点与uint8取整会引入误差，应在保存前后分别报告forward误差，不能仅看图形似flag。 |
| 逆向 | [Symbol of Hope](%E9%80%86%E5%90%91/UofTCTF_2026/Symbol%20of%20Hope/AI_WRITEUP.md) | flag_len=44但右花括号在flag_len-3，需要核对后两字节用途；has_end=False可能允许额外符号输入，不能忽略实际消费字节。 |
| 逆向 | [Will u Accept Some Magic?](%E9%80%86%E5%90%91/UofTCTF_2026/Will%20u%20Accept%20Some%20Magic_/AI_WRITEUP.md) | initialize不会保证执行所有检查器入口；必须找清实际导出调用。对文本做正则替换也需验证只改真实指令。 |
| 逆向 | [Ducks_Ping_Pong](%E9%80%86%E5%90%91/v1t_2026/Ducks_Ping_Pong/AI_WRITEUP.md) | 若修改用户代码会改变绑定hash；静态求解必须使用原始.text及精确字节范围。 |
| 逆向 | [Tiny](%E9%80%86%E5%90%91/v1t_2026/Tiny/AI_WRITEUP.md) | 很多不同输入拥有同一字节和会解同图，不应声称检查器唯一接受该字符串。 |
| 逆向 | [Vision](%E9%80%86%E5%90%91/volgactf_2026-quals/Vision/AI_WRITEUP.md) | 缺少足以支持完整改写的原始解答。 |
| 逆向 | [dotsbedashing](%E9%80%86%E5%90%91/vuwctf_2026/dotsbedashing/AI_WRITEUP.md) | 比较helper实际只区分Morse长度，故运行接受集合更大；应从密文完整Morse模式恢复意图答案。 |
| 逆向 | [ilikewords](%E9%80%86%E5%90%91/vuwctf_2026/ilikewords/AI_WRITEUP.md) | 不需要查询当天Wordle；时间检查只影响动态运行，不能把日期当flag的一部分。 |
| 逆向 | [Black_Tide_Survey](%E9%80%86%E5%90%91/z0d1ak_2026-quals/Black_Tide_Survey/AI_WRITEUP.md) | 字模易混淆，必须保留像素对照，不可按英语常识自行改字符。 |
| 逆向 | [pekpek_stadium_64](%E9%80%86%E5%90%91/z0d1ak_2026-quals/pekpek_stadium_64/AI_WRITEUP.md) | 嵌入MIO0/GBA程序的明文flag是诱饵；结果URL是字面答案无需访问。 |
| 逆向 | [rival_battle](%E9%80%86%E5%90%91/z0d1ak_2026-quals/rival_battle/AI_WRITEUP.md) | 提示That route was perfect仍可能是hash碰撞；无法仅靠接受消息确认正确flag，GPU搜索需准确模拟失败命令跳过敌回合。 |
| 逆向 | [ELFStudy](%E9%80%86%E5%90%91/%E7%AC%AC%E5%8D%81%E5%B1%8A%E2%80%9C%E5%BC%BA%E7%BD%91%E6%9D%AF%E2%80%9D%E5%85%A8%E5%9B%BD%E7%BD%91%E7%BB%9C%E5%AE%89%E5%85%A8%E6%8C%91%E6%88%98%E8%B5%9B%C2%B7%E7%BA%BF%E4%B8%8A%E8%B5%9B/ELFStudy/AI_WRITEUP.md) | 不能只按节表加载可见代码或忽略重定位顺序；脚本设计为静态恢复，不应直接运行未知ELF。 |
| pwn | [67_revenge](pwn/0xFUN_CTF_2026/67_revenge/AI_WRITEUP.md) | 依赖glibc 2.42及UNSORTED_BK_OFF、RET_FROM_ENVIRON等构建相关偏移。 |
| pwn | [bit_flips](pwn/0xFUN_CTF_2026/bit_flips/AI_WRITEUP.md) | f=sbrk-0x20cf0、全局f=PIE+0x4050依赖原构建；cmd+1用于跳过push rbp。 |
| pwn | [Fridge](pwn/0xFUN_CTF_2026/Fridge/AI_WRITEUP.md) | 仅适用于原32位非PIE二进制；NX使栈shellcode方案不适用。 |
| pwn | [phantom](pwn/0xFUN_CTF_2026/phantom/AI_WRITEUP.md) | 来源对initramfs是否含真实flag有冲突，静态解包路径不能替代远端利用证明；页复用和cred喷射存在不稳定性，日志含成功后内核崩溃。 |
| pwn | [Warden](pwn/0xFUN_CTF_2026/Warden/AI_WRITEUP.md) | 原作者只验证jail.py逃逸，未完整验证原生warden；不得写成已完成全部沙箱逃逸。 |
| pwn | [What you have](pwn/0xFUN_CTF_2026/What%20you%20have/AI_WRITEUP.md) | 地址对应原附件；原本地验证使用虚拟flag。 |
| pwn | [House_of_Wade](pwn/apoorvctf_2026/House_of_Wade/AI_WRITEUP.md) | glibc 2.35；目标和订单必须同为malloc(0x28)。 |
| pwn | [Arena_Snapshots](pwn/asis_2026-quals/Arena_Snapshots/AI_WRITEUP.md) | 旧句柄epoch失效；必须同时重算作业校验与新句柄，不能直接RUN旧handle。 |
| pwn | [Dead_Letter](pwn/asis_2026-quals/Dead_Letter/AI_WRITEUP.md) | 全部步骤须在同一连接；CRC32帧校验、票据generation与worker队列槽号是不同概念。 |
| pwn | [QFilter](pwn/asis_2026-quals/QFilter/AI_WRITEUP.md) | JSValue为16字节，tag和引用计数必须匹配；block:true避免辅助程序输出前GC破坏伪造对象。 |
| pwn | [Signal_Race](pwn/asis_2026-quals/Signal_Race/AI_WRITEUP.md) | 512命令配额及信号时间窗口是硬约束；必须先形成checkpoint。 |
| pwn | [micromicromicropython](pwn/b01lers_CTF_2026/micromicromicropython/AI_WRITEUP.md) | 偶数地址写入通过addr-1和值左移8实现；SYSTEM+2、type布局均为题目版本专用。 |
| pwn | [multifiles](pwn/b01lers_CTF_2026/multifiles/AI_WRITEUP.md) | 这是基于官方C solver的静态重建，需同版内核；上传脚本不是漏洞本体，NUM_TRIES/喷射次数影响稳定性。 |
| pwn | [priority-queue](pwn/b01lers_CTF_2026/priority-queue/AI_WRITEUP.md) | 该libc 2.31未启用safe-linking；原文称2.31首次引入tcache不准确，不作为推理前提。 |
| pwn | [spelling-bee](pwn/b01lers_CTF_2026/spelling-bee/AI_WRITEUP.md) | 要跟踪名称、word、param、dict四类分配，不能仅把forget当独立删除。 |
| pwn | [throughthewall](pwn/b01lers_CTF_2026/throughthewall/AI_WRITEUP.md) | Dirty Pipe式路径依赖文件页缓存和精确pipe_buffer布局；仅适用于题目内核环境。 |
| pwn | [transmutation](pwn/b01lers_CTF_2026/transmutation/AI_WRITEUP.md) | 索引仍为unsigned byte，只能覆盖向前256字节；写入阶段不能破坏每轮必经指令。 |
| pwn | [Muktir_Shongket](pwn/bdsec_2026/Muktir_Shongket/AI_WRITEUP.md) | 12字节payload及0x401bb0针对本题非PIE构建；应分别验证字节码边界与机器码跳转落点，原作者报告BDSEC{mukt1r_5h0ngk3t_r34ch3d_th3_f13ld}。 |
| pwn | [Phantom_Device](pwn/bdsec_2026/Phantom_Device/AI_WRITEUP.md) | 这是用户态设备模拟器，不是Linux内核驱动；必须保持session结构及校验一致。 |
| pwn | [blockman-builder](pwn/BSidesSF_CTF_2026/blockman-builder/AI_WRITEUP.md) | clear会清空关卡，patch用于选择性写；地址随会话变化，需重新读开发者泄漏。 |
| pwn | [if-it-leads](pwn/BSidesSF_CTF_2026/if-it-leads/AI_WRITEUP.md) | 来自solve.rb静态行为；长度/整数变化如何越界仍需结合附件源码确认，不能把猜测当已证根因。 |
| pwn | [inheritance](pwn/BSidesSF_CTF_2026/inheritance/AI_WRITEUP.md) | 不需要内存破坏；必须使用实际继承FD，不能固定假设4。 |
| pwn | [nameme](pwn/BSidesSF_CTF_2026/nameme/AI_WRITEUP.md) | 暂不凭题名猜漏洞；需要阅读完整Ruby实现后补齐精确原语。 |
| pwn | [readme](pwn/BSidesSF_CTF_2026/readme/AI_WRITEUP.md) | 根README只有模板，技术依据必须来自Ruby代码；具体地址依赖附件libc。 |
| pwn | [readwritecallme](pwn/BSidesSF_CTF_2026/readwritecallme/AI_WRITEUP.md) | 根README为模板，不能视作完整writeup；精确参数见官方solver。 |
| pwn | [readwriteme](pwn/BSidesSF_CTF_2026/readwriteme/AI_WRITEUP.md) | 不能沿用readwritecallme的隐藏函数；后续需精读Ruby目标选择。 |
| pwn | [rugdoctor](pwn/BSidesSF_CTF_2026/rugdoctor/AI_WRITEUP.md) | 立即数每段只有4字节可控；写入循环用inc al依赖页对齐且shellcode小于256字节。 |
| pwn | [wromwarp](pwn/BSidesSF_CTF_2026/wromwarp/AI_WRITEUP.md) | reset/INIT会重建内存；部分游戏初始化会覆盖flag，切换顺序须按原文。 |
| pwn | [bytecoin](pwn/BYUCTF_2026/bytecoin/AI_WRITEUP.md) | 不是破解ChaCha或HMAC；依赖本题WolfSSL错误时仍产生明文及程序忽略返回码。 |
| pwn | [heap2win](pwn/BYUCTF_2026/heap2win/AI_WRITEUP.md) | 对象布局、vector临时分配和虚表地址均需原二进制；不是覆盖普通函数返回地址。 |
| pwn | [hextoint](pwn/BYUCTF_2026/hextoint/AI_WRITEUP.md) | 依赖可写GOT及固定目标布局，索引按元素而非字节计算。 |
| pwn | [incontinent](pwn/BYUCTF_2026/incontinent/AI_WRITEUP.md) | 原解答仅一句操作说明，具体终止符/缓冲区布局未给出；不扩写为未经证实的任意读。 |
| pwn | [intro2](pwn/BYUCTF_2026/intro2/AI_WRITEUP.md) | 这是保存RIP覆盖，不是GOT覆盖；参数序号和-288偏移依赖目标环境，脚本含旧的-40注释，不能混用。来源末尾给出byuctf{%p_yourself}，本次未运行。 |
| pwn | [menfess](pwn/compfest_2026/menfess/AI_WRITEUP.md) | 内核与模块分别随机化；/flag.txt指向/dev/vda，不能按普通可读文件假设处理。 |
| pwn | [redis_cli_0_day](pwn/compfest_2026/redis_cli_0_day/AI_WRITEUP.md) | 远端MALLOC=libc且glibc2.43，偏移不同；stdout/stderr重定向使本地日志泄漏链不可直接远用，远端改从DBSIZE获得数据并频率投票找arena。不可把Partial/Full RELRO混淆，本题Full RELRO下不覆盖GOT。 |
| pwn | [Dockside_Ticket_Office](pwn/css_2026/Dockside_Ticket_Office/AI_WRITEUP.md) | scanf与read混用会提前缓存流水输入；必须等待菜单提示；目标是函数入口不是0x401271。 |
| pwn | [Maintenance_Log](pwn/css_2026/Maintenance_Log/AI_WRITEUP.md) | 不触碰canary；若目标不在相同256字节窗口需重选落点；附件flag为诱饵。 |
| pwn | [bytecrusher](pwn/DiceCTF_Quals_2026/bytecrusher/AI_WRITEUP.md) | CET标志是否实际启用须运行环境确认；泄漏次数受16轮限制。 |
| pwn | [message-store](pwn/DiceCTF_Quals_2026/message-store/AI_WRITEUP.md) | 任何非法UTF-8会进入Cow::Owned转换并破坏payload；必须检查整块而非仅ROP区域。 |
| pwn | [Food_Inspector_II](pwn/gpn_2026/Food_Inspector_II/AI_WRITEUP.md) | 相邻NOP残留限制连续补丁；原文14次字节写及池分配公式须保持同版Frida。 |
| pwn | [Scanwich_Station](pwn/gpn_2026/Scanwich_Station/AI_WRITEUP.md) | 触发像素必须0x01，0xff被当已标记区域跳过；必须Partial RELRO、puts尚未解析且使用精确libc/映射布局。原文缺独立solve.py，不能仅从图像尺寸保证利用可重现。 |
| pwn | [Cabinet](pwn/haruulzangi_2026-quals/Cabinet/AI_WRITEUP.md) | 每次踩踏后需零输入帧产生新上升沿；本地stub只证明函数到达。 |
| pwn | [Formality](pwn/haruulzangi_2026-quals/Formality/AI_WRITEUP.md) | glibc 2.31日志分配会插入0x20 chunk；换系统libc会改变布局。 |
| pwn | [Made_In_Mongolia](pwn/haruulzangi_2026-quals/Made_In_Mongolia/AI_WRITEUP.md) | 重复定义报错是预期步骤；输入需低于12KiB，符号/IR生命周期与Rust布局都依赖指定版本。 |
| pwn | [Payphone](pwn/haruulzangi_2026-quals/Payphone/AI_WRITEUP.md) | 首连接发送ACK后关闭，必须监听第二连接；不能把旧socket用作输出。 |
| pwn | [Tenure](pwn/haruulzangi_2026-quals/Tenure/AI_WRITEUP.md) | glibc 2.31无safe-linking；本地/托管堆距离0x4070/0x42e0不同，先验证[noop,0,noop,noop]。 |
| pwn | [lets_get_to_library](pwn/kbxac_2026/lets_get_to_library/AI_WRITEUP.md) | 调用栈需留足可写空间，不能直接贴近GOT向下耗栈；精确libc可能未下载。 |
| pwn | [Most_Secure_Bank_Of_Endia](pwn/kbxac_2026/Most_Secure_Bank_Of_Endia/AI_WRITEUP.md) | 目标frame是80字节，Python字符数和UTF-8字节数必须分别验证；不是SQL注入。 |
| pwn | [Original_Unlimited_Codex_100_Free](pwn/kbxac_2026/Original_Unlimited_Codex_100_Free/AI_WRITEUP.md) | 依赖glibc 2.43；execve不在允许列表，不能以system替代ORW。 |
| pwn | [Bosh](pwn/l3akctf_2026/Bosh/AI_WRITEUP.md) | 原附件缺部分私有模块，须保留oracle依赖；分字节写正在使用的回调可能提前崩溃。 |
| pwn | [Piet](pwn/l3akctf_2026/Piet/AI_WRITEUP.md) | 32位有符号运算回绕参与地址合成；终止形状需保证八个出口均失败，避免继续执行垃圾。 |
| pwn | [Piet_2](pwn/l3akctf_2026/Piet_2/AI_WRITEUP.md) | 该版本已修补Piet 1的up/down直接写，不能复用旧set_depth路径；数据来自未初始化栈。 |
| pwn | [Rudimentary_Calculator](pwn/l3akctf_2026/Rudimentary_Calculator/AI_WRITEUP.md) | buf大小0x1000；字符串终止、scanf空白终止和大整数实际长度需分别处理。 |
| pwn | [Supervisor](pwn/l3akctf_2026/Supervisor/AI_WRITEUP.md) | 攻击目标是监督器而非子进程；需要精确模拟协议和Partial RELRO。 |
| pwn | [adventure](pwn/LACTF_2026/adventure/AI_WRITEUP.md) | 移动预算300，地址每项仅发送低6字节；libc偏移与one_gadget约束依赖原包。 |
| pwn | [ourukla](pwn/LACTF_2026/ourukla/AI_WRITEUP.md) | 伪FILE须保留有效lock及字段约束；使用solve.py主路径，attempt_hob为尝试稿。 |
| pwn | [refraction](pwn/LACTF_2026/refraction/AI_WRITEUP.md) | 只有solver，无独立文字解释；偏移0x6a/0xdaa与编码字节是该ELF特定，需原始异常路径核验。 |
| pwn | [scrabasm](pwn/LACTF_2026/scrabasm/AI_WRITEUP.md) | 需同libc PRNG；第一阶段恰好14字节，第二阶段不能被前一轮读取提前吞掉。 |
| pwn | [tcademy](pwn/LACTF_2026/tcademy/AI_WRITEUP.md) | 必须保留top size及下块PREV_INUSE；libc内部GOT地址并非主程序GOT。 |
| pwn | [this-is-how-you-pwn-the-time-war](pwn/LACTF_2026/this-is-how-you-pwn-the-time-war/AI_WRITEUP.md) | 依赖外部bf程序，solver自述未精确确定栈偏移；不能宣称无重试或完整解释PRNG算法。 |
| pwn | [tic-tac-no](pwn/LACTF_2026/tic-tac-no/AI_WRITEUP.md) | 仅10字节solve.txt，缺根因及内存布局证明；不凭两行输入推断具体返回地址劫持。 |
| pwn | [Ez_Pwn](pwn/lyknctf_2026/Ez_Pwn/AI_WRITEUP.md) | 原缓冲区0xa0；需要匹配libc和栈对齐，附件flag是诱饵。 |
| pwn | [H34P_D3V1L](pwn/lyknctf_2026/H34P_D3V1L/AI_WRITEUP.md) | glibc2.39；fgets遇编码指针中的换行会截断，原文使用新布局重试。 |
| pwn | [Return_to_Lose](pwn/lyknctf_2026/Return_to_Lose/AI_WRITEUP.md) | 本地flag为诱饵；固定地址仅对应原ELF。 |
| pwn | [RepusPing](pwn/mntcrlctf_2026/RepusPing/AI_WRITEUP.md) | Full RELRO不可改GOT；exit_funcs偏移0x1e8fe0及_dl_fini偏移23552须匹配原加载器。 |
| pwn | [different_ROP](pwn/NepCTF%202026/47_different_ROP/AI_WRITEUP.md) | 少见Hexagon架构不能套amd64寄存器；源码主路径为BSS方案，早期G_SYSCALL栈帧不稳定。 |
| pwn | [onlyone](pwn/NepCTF%202026/48_onlyone/AI_WRITEUP.md) | seccomp无open，不能直接用常规ORW打开flag；原脚本分本地/SSL远端环境。 |
| pwn | [shadow_signal](pwn/NepCTF%202026/51_shadow_signal/AI_WRITEUP.md) | 信号帧布局及__restore_rt来自同版libc；仅覆盖RIP而不构造ucontext不足以完成链。 |
| pwn | [AHC - Average Heap Challenge](pwn/PascalCTF_2026/AHC%20-%20Average%20Heap%20Challenge/AI_WRITEUP.md) | README仅TODO，依据checker与solve.py；精确对象边界需原程序验证。 |
| pwn | [Grande Inutile Tool](pwn/PascalCTF_2026/Grande%20Inutile%20Tool/AI_WRITEUP.md) | checker使用已知admin SSH凭据，仅证明该认证前提下的路径遍历，不代表得到凭据的方法。 |
| pwn | [Malta Nightlife](pwn/PascalCTF_2026/Malta%20Nightlife/AI_WRITEUP.md) | 索引9对应菜单第10项；按二进制32位行为解释，不能概括为所有C有符号溢出都保证回绕。 |
| pwn | [Packet Tracer 2](pwn/PascalCTF_2026/Packet%20Tracer%202/AI_WRITEUP.md) | 跨线程分配与同步是关键；heap overflow不允许内嵌NUL，须保持字符串复制约束。 |
| pwn | [YetAnotherNoteTaker](pwn/PascalCTF_2026/YetAnotherNoteTaker/AI_WRITEUP.md) | 旧libc需存在__malloc_hook；one_gadget执行条件需同环境检查。 |
| pwn | [Freal_World_Manipulation](pwn/pwnsec_2026/Freal_World_Manipulation/AI_WRITEUP.md) | 两输入有限不保证结果有限；总量是虚拟分配而非必须写满物理内存，flag文件随机命名。 |
| pwn | [JavaScript_After_Core](pwn/pwnsec_2026/JavaScript_After_Core/AI_WRITEUP.md) | win保存同一JSString，不能简单换传参变量；固定WebKit revision及GC布局影响成功。 |
| pwn | [PHP_Sandbox_Escape](pwn/pwnsec_2026/PHP_Sandbox_Escape/AI_WRITEUP.md) | 无需PHP内存破坏；要求该PDO驱动和loadExtension可用，上传文件须在请求结束清理前加载。 |
| pwn | [doMonkeysSwim](pwn/ritsec_2026/doMonkeysSwim/AI_WRITEUP.md) | 早期动态libc利用不适用于更新后的二进制；静态版本中没有现成/bin/sh字符串。 |
| pwn | [Snaking_Revenge](pwn/sas_2026-quals/Snaking_Revenge/AI_WRITEUP.md) | Revenge需更宽堆扫描和额外buffer标签；原文同时有snaking初版，不能混用旧sandbox接口。 |
| pwn | [echo_chamber](pwn/sekaictf_2026/echo_chamber/AI_WRITEUP.md) | 初始tcache关闭且guard_region随机PROT_NONE；此链依赖时序并需要重试，不应报告确定一次成功。 |
| pwn | [ppp](pwn/sekaictf_2026/ppp/AI_WRITEUP.md) | AFC头40字节且长度截到32位；此来源方案依赖固定libc，无须假设safe-linking泄漏。后续第二项执行或free可能崩溃，应以此前完整flag输出验证；作者报告SEKAI{du_bist_gut_genuggggggggggggg}。 |
| pwn | [gaem](pwn/squ1rrel_2026/gaem/AI_WRITEUP.md) | 间接调用目标需endbr64满足IBT；返回链与真正SHSTK启用状态需区分。 |
| pwn | [Common offset](pwn/Srdnlen_CTF_2026/Common%20offset/AI_WRITEUP.md) | 只能第二写触发进位且栈链仅约16字节；不能假设ret2main或leave gadget存在。 |
| pwn | [Echo](pwn/Srdnlen_CTF_2026/Echo/AI_WRITEUP.md) | 原文libc候选最终为Ubuntu2.39；仅低12位返回地址不足以唯一确认版本。 |
| pwn | [Linx](pwn/Srdnlen_CTF_2026/Linx/AI_WRITEUP.md) | glibc2.42；必须保留精确链接/删除次序，目标16字节对齐且输入不能含NUL，solver裁去高零字节。源码展示的是栈返回路线，不是作者提及但未展开的printf表/FSOP分支。 |
| pwn | [Registered Stack](pwn/Srdnlen_CTF_2026/Registered%20Stack/AI_WRITEUP.md) | 初始普通寄存器清零，RSP指向RWX起点；不能把FS/GS可作为字节材料等同于随意执行pop段寄存器。 |
| pwn | [SU_Box](pwn/SUCTF_2026/SU_Box/AI_WRITEUP.md) | V8 sandbox尚未引入，不能套新版本间接指针布局；poc.js是本地关键证据。 |
| pwn | [SU_Chronos_Ring](pwn/SUCTF_2026/SU_Chronos_Ring/AI_WRITEUP.md) | cookie=rol64((kfree>>21) XOR 0x9e3779b97f4a7c15,17) XOR session_idx；时序候选不是直接_text地址。 |
| pwn | [SU_Chronos_Ring1](pwn/SUCTF_2026/SU_Chronos_Ring1/AI_WRITEUP.md) | 两目录正文相同但本目录有C利用与上传器，实际环境偏移仍需对照各自附件。 |
| pwn | [SU_evbuffer](pwn/SUCTF_2026/SU_evbuffer/AI_WRITEUP.md) | inet_pton接受的字符串长度与后续拷贝长度不同；伪造对象需通过各层check。 |
| pwn | [SU_fullchian](pwn/SUCTF_2026/SU_fullchian/AI_WRITEUP.md) | 缺少足以支持完整改写的原始解答。 |
| pwn | [SU_minivfs](pwn/SUCTF_2026/SU_minivfs/AI_WRITEUP.md) | 写命令需文件名hash；不是固定/flag，libc偏移0x210f50等依赖原版本。 |
| pwn | [Cache_Money](pwn/sunshinectf_2026/Cache_Money/AI_WRITEUP.md) | A/B需同页才能共用key；calloc struct与ledger分配分开跟踪。 |
| pwn | [Code_Breaker](pwn/sunshinectf_2026/Code_Breaker/AI_WRITEUP.md) | 两字节大端帧长与加密计数必须同步；回调跳转需考虑IBT目标。 |
| pwn | [Homemaker](pwn/sunshinectf_2026/Homemaker/AI_WRITEUP.md) | 255个A加0x49对应原CRC多项式0x2f；二进制包不能当行文本发送。 |
| pwn | [Print_Print_Revolution](pwn/sunshinectf_2026/Print_Print_Revolution/AI_WRITEUP.md) | 格式串首16字节与arg位置相关；普通fmtstr工具不理解自定义%w。 |
| pwn | [Safe_House](pwn/sunshinectf_2026/Safe_House/AI_WRITEUP.md) | 目标句柄-4；空格/换行受NOTE限制，须从已有字符串取字节，子stdout被丢弃。 |
| pwn | [Total_Recall](pwn/sunshinectf_2026/Total_Recall/AI_WRITEUP.md) | 664字节主payload与15字节必须分开读；合包会破坏rax。 |
| pwn | [goodbye-libc](pwn/TAMUctf_2026/goodbye-libc/AI_WRITEUP.md) | 不是系统glibc；solver含交互input暂停，自动复现前应处理。 |
| pwn | [meep](pwn/TAMUctf_2026/meep/AI_WRITEUP.md) | 大端p32；生产版fork与本地版不同，gadget为原MIPS libc专用。 |
| pwn | [military-system](pwn/TAMUctf_2026/military-system/AI_WRITEUP.md) | 本机非ARM时QEMU路径与原生seccomp不同；需对应ARM64对象布局。 |
| pwn | [task-manager](pwn/TAMUctf_2026/task-manager/AI_WRITEUP.md) | 原solver含input暂停；不是仅double-free即可绕过全部检查，须按顺序保持布局。 |
| pwn | [zagjail](pwn/TAMUctf_2026/zagjail/AI_WRITEUP.md) | 必须用题目Zag编译器和server.py；现代语言语法不提供额外内存安全。 |
| pwn | [abyss-oracle](pwn/Thryve_CTF_2026/abyss-oracle/AI_WRITEUP.md) | 本地bzImage与模块ABI不匹配，patch-local.py只是测试适配；不能把补丁算漏洞利用步骤。 |
| pwn | [secret-door](pwn/Thryve_CTF_2026/secret-door/AI_WRITEUP.md) | 不需libc基址；vtable+0x18关系须该构建，raw对象大小需容纳URL字段。 |
| pwn | [Banned_Bytes](pwn/tracebash_2026/Banned_Bytes/AI_WRITEUP.md) | 禁字节x/g/a/点作用于整payload；终端转义与程序过滤是两层不同约束。 |
| pwn | [Legacy_Ledger](pwn/tracebash_2026/Legacy_Ledger/AI_WRITEUP.md) | NX关闭由-z execstack决定；ASLR地址必须每连接重新解析。 |
| pwn | [down_the_line](pwn/trx_2026/down_the_line/AI_WRITEUP.md) | 段地址乘0x10；该路径依赖x86实模式/A20和只读硬件区，不能用常规用户态堆模型解释。 |
| pwn | [house_of_fishing](pwn/trx_2026/house_of_fishing/AI_WRITEUP.md) | copy至少16字节会连带改key；空admin没有有效bk，不能省略原文构造可解引用指针的准备步骤。 |
| pwn | [krwd](pwn/trx_2026/krwd/AI_WRITEUP.md) | 这是地址空间/时序混淆，非无锁竞态；静态busybox的vtable检查特性和调度决定成功率。 |
| pwn | [slop_allocator](pwn/trx_2026/slop_allocator/AI_WRITEUP.md) | 缺少足以支持完整改写的原始解答。 |
| pwn | [triforce](pwn/trx_2026/triforce/AI_WRITEUP.md) | 本题目标只到V8 sandbox内部；外部代理对象不能冒充真实String，不要混入第二部分sbx逃逸。 |
| pwn | [Firefly_Complete_Combustion](pwn/uiuctf_2026/Firefly_Complete_Combustion/AI_WRITEUP.md) | 必须Lua5.5.0二进制字节码；不是Lua源码层可直接执行loadfile。 |
| pwn | [Sparxie_Vanishing_Encore](pwn/uiuctf_2026/Sparxie_Vanishing_Encore/AI_WRITEUP.md) | 输入为SPX2包中的Lua源码，目标是WASM宿主接口，不能套原生Lua GOT链。 |
| pwn | [Brick_City_Office_Space](pwn/umassctf_2026/Brick_City_Office_Space/AI_WRITEUP.md) | 按32位参数栈布局处理；No RELRO是写GOT前提，输出长度需计入地址前缀。 |
| pwn | [bookmaker](pwn/umdctf_2026/bookmaker/AI_WRITEUP.md) | 来源含ipv4等其他题，本文只采用bookmaker段；CET显示不等于所有路径运行时都受保护。 |
| pwn | [vkexchange](pwn/umdctf_2026/vkexchange/AI_WRITEUP.md) | 依赖Mesa22.3.6及关闭validation layer；不是跨GPU通用偏移。 |
| pwn | [Flytväst](pwn/Undutmaning_2026/Flytv%C3%A4st/AI_WRITEUP.md) | 缺少足以支持完整改写的原始解答。 |
| pwn | [GIF Splitter](pwn/Undutmaning_2026/GIF%20Splitter/AI_WRITEUP.md) | 缺少足以支持完整改写的原始解答。 |
| pwn | [aes-aead](pwn/UofTCTF_2026/aes-aead/AI_WRITEUP.md) | 算法是题目自制GHASH流程，不能泛称标准AES-GCM可如此伪造；需匹配libc与密文约束。 |
| pwn | [babybof](pwn/UofTCTF_2026/babybof/AI_WRITEUP.md) | 仅114字节solver，未记录架构保护与函数名；不能未经附件证明将目标命名为win。 |
| pwn | [calculator](pwn/UofTCTF_2026/calculator/AI_WRITEUP.md) | 只有solver；包含人工input暂停，表达式具体根因需原解析器核验，不能直接称任意整数溢出。 |
| pwn | [eebpf](pwn/UofTCTF_2026/eebpf/AI_WRITEUP.md) | exp.c明确验证器/运行时差异；内核静态地址需由泄漏重定位，原型函数调用约束不能省略。 |
| pwn | [uprobe](pwn/UofTCTF_2026/uprobe/AI_WRITEUP.md) | 0xcc是被利用的指令字节变化，不是正常插桩边界；偏移只适用于题目libc。 |
| pwn | [vellum](pwn/wreckctf_2026/vellum/AI_WRITEUP.md) | 资料不足：无payload、格式参数偏移、sigil提取实现或成功记录；不把catalog的has_writeup等同于可复现解答。 |
| pwn | [paperweight](pwn/z0d1ak_2026-quals/paperweight/AI_WRITEUP.md) | ASCIIHexDecode允许NUL；每dive一次覆盖一次读，必须保留各轮目标偏移与原文第三阶段细节。 |
| pwn | [rapture](pwn/z0d1ak_2026-quals/rapture/AI_WRITEUP.md) | tcache计数与fd链分开维护，单节点投毒不足；malloc取伪块清key会临时清零RIP。 |
| pwn | [Easytl](pwn/%E7%AC%AC%E5%8D%81%E5%B1%8A%E2%80%9C%E5%BC%BA%E7%BD%91%E6%9D%AF%E2%80%9D%E5%85%A8%E5%9B%BD%E7%BD%91%E7%BB%9C%E5%AE%89%E5%85%A8%E6%8C%91%E6%88%98%E8%B5%9B%C2%B7%E7%BA%BF%E4%B8%8A%E8%B5%9B/Easytl/AI_WRITEUP.md) | SNI最大255且不能含NUL；PSK strlen只约束前33字节，不等于identity_len；fork父进程重启会改变canary。 |
| pwn | [Oldsvr](pwn/%E7%AC%AC%E5%8D%81%E5%B1%8A%E2%80%9C%E5%BC%BA%E7%BD%91%E6%9D%AF%E2%80%9D%E5%85%A8%E5%9B%BD%E7%BD%91%E7%BB%9C%E5%AE%89%E5%85%A8%E6%8C%91%E6%88%98%E8%B5%9B%C2%B7%E7%BA%BF%E4%B8%8A%E8%B5%9B/Oldsvr/AI_WRITEUP.md) | 大端与uClibc1.0.32 dlmalloc，不使用glibc safe-linking；远程堆较模拟器偏0x70，栈大read路径受分段限制被弃用。 |
| 虚拟化 | [Draw_Me](%E8%99%9A%E6%8B%9F%E5%8C%96/apoorvctf_2026/Draw_Me/AI_WRITEUP.md) | 本地原文引用 solve.py，但 writeups 目录未随文附该脚本；不能把示意注释当作可运行实现。需要从实际着色器补齐十类指令精确定义。像素字体中的 O/0 需结合题目格式确认。 |
| 虚拟化 | [ASIS_Arch](%E8%99%9A%E6%8B%9F%E5%8C%96/asis_2026-quals/ASIS_Arch/AI_WRITEUP.md) | 原文提及 solve.py/recover.py，但本地 writeups 仅有 README。需补齐完整 ISA 与扩散逆函数；不能凭十轮描述直接宣称脚本齐全。地址和校验常量只对应收录构建。 |
| 虚拟化 | [Revenant_buddy](%E8%99%9A%E6%8B%9F%E5%8C%96/asis_2026-quals/Revenant_buddy/AI_WRITEUP.md) | 混淆表偏移和编码串依赖 worker 构建；新进程的随机秘密无须猜测，因为程序直接引用它。原文 solve.py 未作为单独文件收录，网络结果仅为作者报告。 |
| 虚拟化 | [piano](%E8%99%9A%E6%8B%9F%E5%8C%96/b01lers_2026/piano/AI_WRITEUP.md) | 本地只有README，parse.py、emulate_bulk.py、bulk_coeffs.json等未随文收录。原文明确未用最终候选跑原二进制；需要重新提取全体约束并做正向验证。 |
| 虚拟化 | [favorite_potato](%E8%99%9A%E6%8B%9F%E5%8C%96/b01lers_CTF_2026/favorite_potato/AI_WRITEUP.md) | 作者称 Motorola 6502，但架构名称本身不影响指令语义；必须以实际6502实现为准。code.bin.gz 位于解答目录且仅18字节，不能未经检查就把它当5820001字节真题程序。环境与完整输入文件须按附件核对。 |
| 虚拟化 | [indirect-memory-access](%E8%99%9A%E6%8B%9F%E5%8C%96/b01lers_CTF_2026/indirect-memory-access/AI_WRITEUP.md) | 仅有solver说明，布尔位与游戏事件的完整映射背景需要结合附件。代码以str(m[dat[i]])判True，未赋值变量会落到F；复现时应检查模型完整性，并确认每段长度小于10。 |
| 虚拟化 | [kyotoprotocol](%E8%99%9A%E6%8B%9F%E5%8C%96/b01lers_CTF_2026/kyotoprotocol/AI_WRITEUP.md) | 原文说明初始化变量中有一处模7恰为3的题目错误；应以实际VM行为为准。图像clues.png/solved.png仅作辅助，约束应从代码提取。Bash会修改脚本，复现需使用副本。 |
| 虚拟化 | [Borrowed_Memory](%E8%99%9A%E6%8B%9F%E5%8C%96/bdsec_2026/Borrowed_Memory/AI_WRITEUP.md) | 原文没有完整列出所有表补丁及4个opcode公式，必须从附件补齐；solve.py引用未单独收录。地址是所述构建的静态定位信息，PIE运行时地址另加加载基址。 |
| 虚拟化 | [mixed_signals](%E8%99%9A%E6%8B%9F%E5%8C%96/BYUCTF_2026/mixed_signals/AI_WRITEUP.md) | 原始README很短，并明确没有solve脚本；因此本文只能确定整体机制和验证入口，不能补造具体算法或宣称独立推导出flag。恒定时间不支持直接套用逐字节时序猜测。 |
| 虚拟化 | [Kelpie](%E8%99%9A%E6%8B%9F%E5%8C%96/cryovault_2026-quals/Kelpie/AI_WRITEUP.md) | README引用的独立solve.py未收录；完整hint应从原文读取而非猜测。文件偏移=VA-0x400000只是作者针对该ELF布局的结论，通用实现应查PT_LOAD映射，non-PIE并不普遍保证该公式。 |
| 虚拟化 | [thaw_ladder](%E8%99%9A%E6%8B%9F%E5%8C%96/cryovault_2026-quals/thaw_ladder/AI_WRITEUP.md) | 本地7.2参考模型与原文7.3远端不同；新连接会重置随机状态，不能复用旧profile。三份引用solver未单独收录，文中片段不足以无修改运行；远程可用性本次未验证。 |
| 虚拟化 | [prince_walk](%E8%99%9A%E6%8B%9F%E5%8C%96/css_2026/prince_walk/AI_WRITEUP.md) | 本地只有README，未收录引用的solve.py；种子初始化和8类opcode完整公式仍需从附件/原文代码补全。目的地坐标是计算参数，不应仅patch坐标后忽略事件状态。 |
| 虚拟化 | [locked_in](%E8%99%9A%E6%8B%9F%E5%8C%96/dicectf_2026-quals/locked_in/AI_WRITEUP.md) | solve11.py未收录；原文bitmangle为经验公式，需用全部256输入或相应字节码核实。给出的flag为30字节，与长度条件一致。 |
| 虚拟化 | [garden](%E8%99%9A%E6%8B%9F%E5%8C%96/DiceCTF_Quals_2026/garden/AI_WRITEUP.md) | 官方README部分措辞是条件性描述“if mark_reachable is changed”，需核对实际源码而非直接认定所有构建可用。libc和栈偏移是环境相关值。目录的另一garden副本应链接到本条，不重复算题。 |
| 虚拟化 | [Automaton](%E8%99%9A%E6%8B%9F%E5%8C%96/haruulzangi_2026-quals/Automaton/AI_WRITEUP.md) | 本地README引用solve.py但未收录该脚本，需补全14类opcode的操作数宽度与语义。给出的候选为42字节，与目标长度一致。 |
| 虚拟化 | [LattiaVM](%E8%99%9A%E6%8B%9F%E5%8C%96/l3akctf_2026/LattiaVM/AI_WRITEUP.md) | 第一版解码输入限128字节，执行限512条。 合集包含7题，需只读本题章节。libc/loader及栈布局依赖附件；独立solver未随该博客单独收录。 |
| 虚拟化 | [LattiaVM_2](%E8%99%9A%E6%8B%9F%E5%8C%96/l3akctf_2026/LattiaVM_2/AI_WRITEUP.md) | 第二版程序缓冲移到malloc且输入增至256字节，但VM状态仍在宿主栈；sp未显式初始化，作者报告本环境起始为0，应先核验。 合集包含7题，需只读本题章节。libc/loader及栈布局依赖附件；独立solver未随该博客单独收录。 |
| 虚拟化 | [helm-hell](%E8%99%9A%E6%8B%9F%E5%8C%96/LA_CTF_2026/helm-hell/AI_WRITEUP.md) | 这是社区材料的年份/长度疑点，须优先按附件模板和solver实际常量校正。不要部署Kubernetes，题目验证仅需模板渲染。 |
| 虚拟化 | [reflection](%E8%99%9A%E6%8B%9F%E5%8C%96/LA_CTF_2026/reflection/AI_WRITEUP.md) | 只有HTML，脚本内嵌于页面且有语法高亮/行号；需从pre/code提取后复核。libgcc内部符号和结构布局依赖运行库，原文关于全部表达式执行两次是该观察路径而非所有unwind的普遍保证。 |
| 虚拟化 | [VM Encryptor](%E8%99%9A%E6%8B%9F%E5%8C%96/NCTF_2026/VM%20Encryptor/AI_WRITEUP.md) | PDF提取文本有分页行号、控制字符和断行，不能整段直接复制运行。题目目标数据和官方脚本在PDF中完整给出，本次仅静态转写；不要把邻题的Java脚本误关联本题。 |
| 虚拟化 | [ColorfulArray](%E8%99%9A%E6%8B%9F%E5%8C%96/NepCTF%202026/36_ColorfulArray/AI_WRITEUP.md) | 脚本中的work/36路径不是本地现有目录，需替换为本题附件；部分已知字符被直接写入脚本而原文没解释推导，需把它们列为作者提供的先验。本次未运行。 |
| 虚拟化 | [T.A.S P.W.N](%E8%99%9A%E6%8B%9F%E5%8C%96/NepCTF%202026/42_T.A.S%20P.W.N/AI_WRITEUP.md) | 强依赖原影片、ROM版本、模拟器和keystream；不保证换版本可复现。原文完整代码含历史蓝屏payload作为恢复keystream的数据，应明确其用途而非运行它。 |
| 虚拟化 | [StrangeVM](%E8%99%9A%E6%8B%9F%E5%8C%96/PascalCTF_2026/StrangeVM/AI_WRITEUP.md) | 仅HTML短文，无独立反汇编器和solver文件；原文脚本可以抽取但不是已验证可用解法。不要擅自修正一处文字后宣称所有矛盾解决。 |
| 虚拟化 | [ICX_Confusion](%E8%99%9A%E6%8B%9F%E5%8C%96/pwnsec_2026/ICX_Confusion/AI_WRITEUP.md) | 本地仅README，引用的job_auth、完整能力token及工具需从原文代码块/附件恢复，不能替换为24位算术。对象地址0x110461/0x110481等属于特定guest布局。 |
| 虚拟化 | [ICX_Regulate](%E8%99%9A%E6%8B%9F%E5%8C%96/pwnsec_2026/ICX_Regulate/AI_WRITEUP.md) | README提到exploit.gmi、/tmp/sandbox_text.u32及多份工具，但本地writeups仅README，不能假定已具备最终镜像。ABI、guest例程地址与标记传播均须对应同一构建。 |
| 虚拟化 | [PwnSec_Support](%E8%99%9A%E6%8B%9F%E5%8C%96/pwnsec_2026/PwnSec_Support/AI_WRITEUP.md) | 本地只有README，独立solve.py未收录；完整SQL语法与指令布局以原文代码块和附件为准。改变本地监听8081是作者环境调整，不是利用必需条件。 |
| 虚拟化 | [Zigerions](%E8%99%9A%E6%8B%9F%E5%8C%96/pwnsec_2026/Zigerions/AI_WRITEUP.md) | 没有IV只能提示ECB，不能普遍证明ECB；应以解密代码和完整明文确认。引用extract_layers.py/watch.c/solve.py未单独收录，且所需中间落地文件须先核对附件。 |
| 虚拟化 | [babel_furnace](%E8%99%9A%E6%8B%9F%E5%8C%96/SCTF_2026/babel_furnace/AI_WRITEUP.md) | 不能遗漏Host share或把最多192次resume当192个VM块。脚本依赖的文件路径与模块提取必须先核对；原WP未直接写出最终flag，本次不从其他文本猜测。 |
| 虚拟化 | [BrainfOok](%E8%99%9A%E6%8B%9F%E5%8C%96/SCTF_2026/BrainfOok/AI_WRITEUP.md) | 本地提供完整长文与代码，但非单一开箱即用自动恢复脚本。原文称无法一步恢复是针对其分析路径，不是数学上的不可能性证明；本次仅静态重构其方法。 |
| 虚拟化 | [3in1](%E8%99%9A%E6%8B%9F%E5%8C%96/SekaiCTF_2026/3in1/AI_WRITEUP.md) | 作者writeup.txt仅620字节，HTML离线副本未含完整三个组件说明；代码含编译后ELF但无对应C源码。所有LibJS/libc偏移和对象布局针对题目构建，随机堆布局可能使重试失败。 |
| 虚拟化 | [MTE](%E8%99%9A%E6%8B%9F%E5%8C%96/SekaiCTF_2026/MTE/AI_WRITEUP.md) | 原文引用solve.c/qemu_pauth.patch，但本题writeups仅社区说明和二进制solver，完整源码需从附件核对。QEMU补丁、内核布局、slab回收策略和kmsg泄露可用性都是必要前提，不能推广到默认MTE/PAC环境。 |
| 虚拟化 | [squ1rrel_o_tron_2](%E8%99%9A%E6%8B%9F%E5%8C%96/squ1rrel_2026/squ1rrel_o_tron_2/AI_WRITEUP.md) | 原文一处写每次5.7ms，后又写5700ms，速度倍数矛盾，本文不沿用。独立mix_fast.c/solve.py未收录，README有核心函数但网络端需核对server.py实际计时方式。 |
| 虚拟化 | [Dantes_Trial](%E8%99%9A%E6%8B%9F%E5%8C%96/srdnlen_2026-quals/Dantes_Trial/AI_WRITEUP.md) | 原文引用brute2.c、solve_correct.py和vm_emu2.py但本地仅README。缺失S-box/具体混合公式需从ROM补齐；不要对错误hash实现进行无界暴力。 |
| 虚拟化 | [Cornflake v3.5](%E8%99%9A%E6%8B%9F%E5%8C%96/Srdnlen_CTF_2026_Quals/Cornflake%20v3.5/AI_WRITEUP.md) | 本地短文未列全量字节码或求解器；正文个别伪码的寄存器注释与opcode表不同，精确语义需以DLL为准。原站载荷是否仍可下载不在本次验证范围。 |
| 虚拟化 | [SU_Lock](%E8%99%9A%E6%8B%9F%E5%8C%96/SUCTF_2026/SU_Lock/AI_WRITEUP.md) | 源码提取常量完整，但原文截图里的地址仍需匹配具体构建。不能仅看到解密字节可打印便认定成功；禁止把模拟VM读取常量的脚本描述为已完整模拟驱动。 |
| 虚拟化 | [SU_MvsicPlayer](%E8%99%9A%E6%8B%9F%E5%8C%96/SUCTF_2026/SU_MvsicPlayer/AI_WRITEUP.md) | exp以当前目录读取ddd.su_mv_enc并写ddd.wav，使用前需明确目录。播放器关闭会归档并删原文件，文档分析无需启动它。本文未计算MD5，也未声称已恢复音频。 |
| 虚拟化 | [SU_West](%E8%99%9A%E6%8B%9F%E5%8C%96/SUCTF_2026/SU_West/AI_WRITEUP.md) | 原文exp内EMBEDDED_TABLES等常量需要与constants.txt配套，不要把省略/外部表当默认空值。s0、seed flag buffer和输入范围均为题目参数，本次未运行Z3。 |
| 虚拟化 | [IntMod](%E8%99%9A%E6%8B%9F%E5%8C%96/sunshinectf_2026/IntMod/AI_WRITEUP.md) | 本地仅README，hook*.c/analyze.py/solve.py等未收录。原文称GDB无用属于作者经验，不能当一般限制；可用受控信号调试但需避免改变程序语义。 |
| 虚拟化 | [chimera-mirrors](%E8%99%9A%E6%8B%9F%E5%8C%96/Thryve_CTF_2026/chimera-mirrors/AI_WRITEUP.md) | 本地有solve.py，但在导入时就读取当前目录chimera_mirror，需调整附件路径。原作者说每字节有解并不自动保证唯一，复现时应记录候选数。 |
| 虚拟化 | [parallax](%E8%99%9A%E6%8B%9F%E5%8C%96/Thryve_CTF_2026/parallax/AI_WRITEUP.md) | 本地完整solve.py读取当前目录parallax；修改路径即可定位附件，但本次未运行。若某三元组多解应回溯，不能无条件取第一个后仍声称唯一。 |
| 虚拟化 | [soul](%E8%99%9A%E6%8B%9F%E5%8C%96/Thryve_CTF_2026/soul/AI_WRITEUP.md) | 已收录solve.py实际上主要解密并反汇编字节码，并非自动恢复key的完整solver；原文通过语义选择剩余候选，不能宣称字符集约束保证唯一。固定soul_dist路径需调整。 |
| 虚拟化 | [1+1](%E8%99%9A%E6%8B%9F%E5%8C%96/trx_2026/1%2B1/AI_WRITEUP.md) | 原文无完整文字WP；枚举2^32每块代价很高。Python按可打印性选择首个候选是启发式，需全局回代确认；C存在数组越界，不能原样当可靠验证器运行。 |
| 虚拟化 | [wandering](%E8%99%9A%E6%8B%9F%E5%8C%96/trx_2026/wandering/AI_WRITEUP.md) | 原文件HOST = 127.0.0.1缺引号，是Python语法错误；还存在无上限网络重试和未使用args。需先改为字符串并配置授权靶场，不能把当前文件宣称可直接运行；缺少VM机制说明。 |
| 虚拟化 | [gnalekcip](%E8%99%9A%E6%8B%9F%E5%8C%96/umdctf_2026/gnalekcip/AI_WRITEUP.md) | 原文从“无法逆hash”跳到语义拼接答案，缺少关键求解证据；不能把猜谜叙述改写成已证明算法。共享memo大小也应按具体opcode核对，Python pickle并非天然只支持256槽。 |
| 虚拟化 | [roulette](%E8%99%9A%E6%8B%9F%E5%8C%96/umdctf_2026/roulette/AI_WRITEUP.md) | 本地仅README，完整四表和循环公式需从代码块/附件提取；原文把某些常量笼统叫MurmurHash，应保留实际VM而非替换为标准库hash。106/108字节边界也不能凭假设补零。 |
| 虚拟化 | [Bring Your Own Program](%E8%99%9A%E6%8B%9F%E5%8C%96/UofTCTF_2026/Bring%20Your%20Own%20Program/AI_WRITEUP.md) | “重排未bump”依据solver注释及利用路径静态推断；需与题目VM源码核对后才能确定完整根因。HOST/PORT为本地默认，运行期服务并未验证。 |
| 虚拟化 | [House_XIII](%E8%99%9A%E6%8B%9F%E5%8C%96/z0d1ak_2026-quals/House_XIII/AI_WRITEUP.md) | 完整credential算式见原文代码，独立solve.py未收录。fd13依赖launcher预打开；对象偏移与glibc同尺寸复用须匹配本构建，secret跨进程不可复用。 |
| 虚拟化 | [Salvage_Protocol](%E8%99%9A%E6%8B%9F%E5%8C%96/z0d1ak_2026-quals/Salvage_Protocol/AI_WRITEUP.md) | 0x20单次替换body限255字节，完整0x400 AUTH不能简单塞一个指令，原代码采用逐字节构造。独立solve.py未收录；二进制硬化弱不是本题利用根因。 |
| 虚拟化 | [stars_below](%E8%99%9A%E6%8B%9F%E5%8C%96/z0d1ak_2026-quals/stars_below/AI_WRITEUP.md) | 本地只有README，引用solve_invariant.py/vm.py及分析blob未单独收录；需核对附件可提取情况。末字节Base32填充位和domain NUL容易出错，所有盐和调度常量必须从同一版本提取。 |
| 车联网 | [AGL 1](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%201/AI_WRITEUP.md) | 原文提到镜像允许 root 空密码登录，这是本题镜像的配置，不能推广到任意 AGL。挂载分析宜使用只读副本。 |
| 车联网 | [AGL 2](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%202/AI_WRITEUP.md) | 磁盘偏移属于该附件版本；不要对所有raw镜像硬套1048576。EXIF比像素内容更关键。 |
| 车联网 | [AGL 3](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%203/AI_WRITEUP.md) | 本次未播放附件音频，结果来自官方逐字转录。无需把整段音乐进行频谱隐写分析。 |
| 车联网 | [AGL 4](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%204/AI_WRITEUP.md) | 片段来自PDF截图，应以原始GIF/文本复核易混淆的0/O与1/l；本次没有实际挂载镜像。 |
| 车联网 | [AGL 5](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/AGL%205/AI_WRITEUP.md) | 运行中的值与schema定义分离；截图显示的flag字符可能与槽位总数不同，需保留完整值和服务返回作核对，不自行补字符。 |
| 车联网 | [Classic KeeLoq Garage - Find the Key](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Classic%20KeeLoq%20Garage%20-%20Find%20the%20Key/AI_WRITEUP.md) | 静态资料改写；未运行复现。 |
| 车联网 | [Classic KeeLoq Garage - Next HOP](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Classic%20KeeLoq%20Garage%20-%20Next%20HOP/AI_WRITEUP.md) | 静态资料改写；未运行复现。 |
| 车联网 | [Gateway Gremlins](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Gateway%20Gremlins/AI_WRITEUP.md) | 端点及常量仅适用于比赛环境。必须保持nonce与提交时刻一致；原文省略了通用UDS收发函数，可参考相邻Seed-Key Leak的结构。 |
| 车联网 | [I Saw Our Time Pass](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/I%20Saw%20Our%20Time%20Pass/AI_WRITEUP.md) | CAN ID在幻灯片中按十六进制书写；Block Size示例输出则是十进制。不能混用打印进制。 |
| 车联网 | [Next Counter](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Next%20Counter/AI_WRITEUP.md) | 静态资料改写；未运行复现。 |
| 车联网 | [Parking Lot Whisper](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Parking%20Lot%20Whisper/AI_WRITEUP.md) | 静态资料改写；未运行复现。 |
| 车联网 | [Predict Next UNLOCK](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Predict%20Next%20UNLOCK/AI_WRITEUP.md) | 静态资料改写；未运行复现。 |
| 车联网 | [RAMN ECU D](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/RAMN%20ECU%20D/AI_WRITEUP.md) | 完整认证报文实现仅以外部gist链接给出，本文没有下载或执行它；本地PDF提供算法与成功日志，不能据此宣称已完成服务复现。 |
| 车联网 | [Read the simple fob](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Read%20the%20simple%20fob/AI_WRITEUP.md) | 静态资料改写；未运行复现。 |
| 车联网 | [Real KeeLoq Garage - Next HOP](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Real%20KeeLoq%20Garage%20-%20Next%20HOP/AI_WRITEUP.md) | 静态资料改写；未运行复现。 |
| 车联网 | [Real KeeLoq Garage - Normal Learn](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Real%20KeeLoq%20Garage%20-%20Normal%20Learn/AI_WRITEUP.md) | 静态资料改写；未运行复现。 |
| 车联网 | [Seed-Key Leak](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/Seed-Key%20Leak/AI_WRITEUP.md) | 原文PDF复制出的代码含缩进/反斜线排版问题，复现时应重建语法。种子来自当前会话，不应硬编码历史seed。 |
| 车联网 | [VIN Hunter](%E8%BD%A6%E8%81%94%E7%BD%91/NDIAS_2026/VIN%20Hunter/AI_WRITEUP.md) | 静态资料改写；未运行复现。 |
| iot | [UART](iot/0xFUN_2026/UART/AI_WRITEUP.md) | 原文用截图展示采样细节，正文已给关键参数；本次未运行Sigrok，不将其输出当现场验证。 |
| iot | [OutOfPhase](iot/asis_2026-quals/OutOfPhase/AI_WRITEUP.md) | 本地writeup仅存README，文中decode_data.py等辅助脚本是否包含在附件需另核；不能把原文列出的脚本名视为本地已存在。不可混入EP2DES等其他呼号分片。 |
| iot | [Silent_Carrier](iot/asis_2026-quals/Silent_Carrier/AI_WRITEUP.md) | 本地README引用的direct_best.py及codec工具未在writeups目录中提供；复现还需相应实现。固定掩码不意味着真实DMR所有隐私模式都相同。 |
| iot | [D's Signpost](iot/NDIAS_2026/D%27s%20Signpost/AI_WRITEUP.md) | 最终solver依赖aprs_decode、clean_extract等未在本题writeups目录提供的模块，不能直接复制末尾代码就宣称可运行；正文给出算法片段，但仍需补齐辅助函数。 |
| iot | [Suspicious device 1](iot/NDIAS_2026/Suspicious%20device%201/AI_WRITEUP.md) | 整数大小端须从build_packet汇编确认，幻灯片表格未完整规定；单靠该表不能声称完整可运行。远程地址为历史赛事端点，本次未连接。 |
| iot | [Suspicious device 2](iot/NDIAS_2026/Suspicious%20device%202/AI_WRITEUP.md) | 依赖stage1环境和服务状态；凭据、库名及工具路径均属于题目镜像。本次没有执行远程命令或数据库查询。 |
| iot | [Suspicious device 3](iot/NDIAS_2026/Suspicious%20device%203/AI_WRITEUP.md) | 官方第101页提供反编译逻辑，本地不含独立完整竞争脚本；本文仅静态整理，没有进行跨主机连接。 |
| iot | [Tiny crackme](iot/NDIAS_2026/Tiny%20crackme/AI_WRITEUP.md) | 原文dict只保留每个CRC状态的一个4字节候选，可能覆盖碰撞；若复现失败需保留候选列表。63^4约1575万条Python记录，内存不可忽略。本次未执行穷举或QEMU。 |
| iot | [虚验室制取稀硫酸](iot/NepCTF%202026/23_%E8%99%9A%E9%AA%8C%E5%AE%A4%E5%88%B6%E5%8F%96%E7%A8%80%E7%A1%AB%E9%85%B8/AI_WRITEUP.md) | 这是仿真题流程；原文脚本硬编码历史HOST、PORT及本地目录，需要替换为受控实例配置。本文未操作PLC或执行脚本。 |
| iot | [赛博心情电梯](iot/NepCTF%202026/24_%E8%B5%9B%E5%8D%9A%E5%BF%83%E6%83%85%E7%94%B5%E6%A2%AF/AI_WRITEUP.md) | 原文含多版测试/race脚本，主线是live_travel_then_spoof，不能把早期失败试验当最终流程。本次未执行仿真控制。 |
| iot | [UnknownFirmware](iot/NepCTF%202026/37_UnknownFirmware/AI_WRITEUP.md) | 代码存在筛选风险：先按整个blob计算h并要求h<=400，较大固件可能在尝试局部hh之前就全部跳过。复现需按明确窗口切片并检查边界；原文仅给启发式而非保证解。 |
| iot | [谁引闪了我的灯](iot/NepCTF%202026/46_%E8%B0%81%E5%BC%95%E9%97%AA%E4%BA%86%E6%88%91%E7%9A%84%E7%81%AF/AI_WRITEUP.md) | channel→group的推导在正文略写；需要原题协议定义支持。该文有“去空格”与大小写不一致问题，本次未运行solver，仅做已知常量的MD5核算。 |
| iot | [SU_EzRouter](iot/SUCTF_2026/SU_EzRouter/AI_WRITEUP.md) | 不应臆造具体堆漏洞名、覆盖偏移或已取得shell。当前缺口：CGI根因、最终触发条件、输出读取与成功验证。依赖requests和pwntools，且context.arch=amd64。 |
| iot | [SU_老年固件](iot/SUCTF_2026/SU_%E8%80%81%E5%B9%B4%E5%9B%BA%E4%BB%B6/AI_WRITEUP.md) | 提取脚本默认attachment路径相对writeups层级可能不匹配，应显式传--attachment。ZIP成员写盘前还须规范化路径并限制在输出目录。本文没有运行原提取脚本。 |
| iot | [Brick_by_Brick](iot/umassctf_2026/Brick_by_Brick/AI_WRITEUP.md) | 原文run持续时间实现用timestamps[j-1]-timestamps[i]，会少一个采样间隔；不要原样照抄。按半开区间边界计算，或直接使用时间轴中心采样。 |
| iot | [Smart_Brick_v2](iot/umassctf_2026/Smart_Brick_v2/AI_WRITEUP.md) | 原文把NAND(NAND(G7,x),NAND(G7,NOT x))称为XOR并不准确，该式化简为G7。依据真值表模拟即可避免此误导；本地README引用的完整模拟脚本未在writeups中提供。 |
| android | [Boring_APK](android/bkisc_2026/Boring_APK/AI_WRITEUP.md) | README未列资产key全部字节或完整solver，需从APK补取。NDK basic_string ABI、Linux加载器patch属于可选执行方案，不能当作对任意Android so通用的方法。原文“21个free positions”亦有计数疑点：27-6-1=20，须以实际索引边界为准。 |
| android | [doremi](android/BSidesSF%20CTF%202026/doremi/AI_WRITEUP.md) | README写arya.xml而solution.py实际使用aria；复现以APK资源名核实。solution.py会删除指定workdir/decoded并调用npx安装转换工具，先检查路径与依赖再执行。本次未运行该脚本。 |
| android | [vinyl-drop](android/BSidesSF%20CTF%202026/vinyl-drop/AI_WRITEUP.md) | 现成Test QRs是历史时刻样本，过期后不能作为当前成功测试。仅改变客户端显示不代表后端接受；应保留实际Cloud Function响应。 |
| android | [back_and_forth](android/BYUCTF%202026/back_and_forth/AI_WRITEUP.md) | 作者明确承认尾部JNI比较长度及strcmp方向有设计错误，28f6属于预期值，不应宣称当前程序唯一强制该后缀。本地只提供brute.py，文中提到的gen_bytes.cpp和Main.java未在writeups目录中。 |
| android | [d3llvm](android/D%5E3CTF%202026/d3llvm/AI_WRITEUP.md) | 模型优化节点名可能随MNN版本/后端改变，不能用未优化图的名字直接代入。token长度是64个字符即32字节，不是64bit整数。原脚本简略unpad只截最后字节，复现应补完整填充验证。 |
| android | [I_HATE_THIS_APP](android/lyknctf_2026/I_HATE_THIS_APP/AI_WRITEUP.md) | 本题材料中同时包含另8道crack题，只有第6节相关。保留原目录但明确平台纠偏；本次未执行PE。 |
| android | [I_HATE_THIS_APP_REVENGE](android/lyknctf_2026/I_HATE_THIS_APP_REVENGE/AI_WRITEUP.md) | 该题并非Android APK；普通nonce12+counter4构造不适用。若比赛实例设置了环境变量则默认key可能不适用；本文依据原文样本。 |
| android | [Hook My Secret](android/NCTF_2026/Hook%20My%20Secret/AI_WRITEUP.md) | 本地官方PDF第72—75页含Frida脚本；复制PDF文本会夹杂页码、行号及控制字符，需清理。应核实密钥长度确为16字节和IV长度16。 |
| android | [GuardMaster](android/SCTF_2026/GuardMaster/AI_WRITEUP.md) | 原文建立的是分析别名而非原始符号。native helper调用、状态路径与调度是否输入无关须按原文证据核实；本次仅阅读静态资料，未运行Unicorn/DEX解释器或APK。 |
| android | [Backdrop](android/Securinets%20CTF%20Quals%202026/Backdrop/AI_WRITEUP.md) | 不能把“An error happened”一律叫反调试，需区分捕获到的GCM异常和引擎SIGABRT。计时与渲染参数hook需要在相应初始化前生效；本文未运行APK。 |
| android | [SekaiID](android/SekaiCTF_2026/SekaiID/AI_WRITEUP.md) | 原文关于intent劫持、provider和claimsTag的预期利用包含推测与缺失步骤，不应写为已证明链。run-as仍受设备策略/SELinux影响，不能保证任意debuggable包都可读任意/system文件；本题依赖特定owner与权限。 |
| android | [ufo](android/SekaiCTF_2026/ufo/AI_WRITEUP.md) | 原文使用AI清理图像可能引入像素变化，复现建议以原截图逐模块校验；代码与类名仅针对题目APK版本。本次没有修改用户DataStore。 |
| android | [SU_flumel](android/SUCTF_2026/SU_flumel/AI_WRITEUP.md) | 早期文章伪代码的t1/t2索引与最终exp.py的idx公式不同，应以对应附件真实逻辑核对，不混合两个版本；作者更换过附件。不要浪费上下文逐行分析44万行无关Hermes噪声。 |
