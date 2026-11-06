# 0xFUN CTF 2026 - Phantom (Kernel Exploit Writeup)

## Overview

This challenge provides a vulnerable kernel driver `/dev/phantom`.

The bug is a classic **Use-After-Free (UAF) on a full page (0x1000)**:

1. `CMD_ALLOC` allocates a page in the kernel
2. The page is mapped to userland via `mmap`
3. `CMD_FREE` frees the page
4. The user mapping still remains valid

This leads to a **dangling user pointer to a freed kernel page**, allowing us to manipulate future allocations placed on that page.

---

## Vulnerability

```c
phantom_alloc(fd);
void *uaf = mmap(...);
phantom_free(fd);
```

After `phantom_free()`, the kernel page is returned to the allocator, but the user still has access to it.

---

# Exploitation Strategies

We implemented two different solutions:

1. cred overwrite (simple but unstable)
2. pipe_buffer + msg_msg + modprobe_path (stable)

---

# Solution 1: cred Overwrite

## Idea

Reallocate the freed page as `struct cred` objects, then overwrite UID/GID fields to become root.

---

## Steps

1. Trigger UAF
2. Spray cred objects:
   ```c
   for (int i = 0; i < 0x40; i++) setuid(1000);
   ```
3. Wait for reallocation
4. Overwrite UID/GID:
   ```c
   memset(uaf + 8, 0, 0x20);
   ```
5. Spawn processes waiting for privilege escalation

---

## Important Detail

Memory layout:

```
0x00  refcount
0x08  uid/gid
0x10  euid/egid
```

We must not overwrite the refcount.

---

# Solution 2: pipe_buffer + msg_msg + modprobe_path

## Idea

Build a kernel arbitrary write primitive and overwrite modprobe_path.

---

## Steps

1. pipe spray
2. leak kernel base
3. overwrite pointer
4. msg_msg spray
5. overwrite modprobe_path
6. trigger modprobe

---

# Conclusion

| Method | Stability | Difficulty |
|--------|----------|------------|
| cred overwrite | Low | Easy |
| pipe + msg_msg + modprobe | High | Medium |

---

# 日本語解説

## 概要

本問題では `/dev/phantom` というデバイスドライバに Use-After-Free（UAF）脆弱性が存在します。

```
alloc → mmap → free
```

の後でもユーザ空間からアクセス可能なため、解放済みカーネルページを操作することができます。

この結果、後続のカーネルオブジェクトをそのページ上に再配置させ、任意の内容を書き換えることが可能になります。

---

## 解法1：cred 上書き

### 概要

解放されたページを `struct cred` として再利用させ、UID/GID を 0 に書き換えることで root 権限を取得する方法です。

---

### 手順

1. UAF を発生させる
2. `setuid(1000)` を繰り返して cred をスプレー
3. 解放済みページに cred が再配置されるのを待つ
4. `uaf + 8` から 0 を書き込み、UID/GID を 0 にする
5. fork したプロセスで root 化を検知し flag を取得

---

### 重要ポイント

cred 構造体の先頭は参照カウントです：

```
+0x00 refcount
+0x08 uid/gid
```

refcount を破壊するとカーネルパニックが発生するため、

```
memset(uaf + 8, 0, 0x20);
```

のようにオフセットをずらして書き込みます。

---

### 問題点

- タイミング依存で不安定
- 別オブジェクトを破壊する可能性あり
- リモートでは成功率が低い

---

## 解法2：pipe + msg_msg + modprobe_path

### 概要

UAF を利用して pipe_buffer を再配置し、そこから任意書き込みプリミティブを構築し、modprobe_path を書き換える方法です。

---

### 手順

1. pipe を大量に生成し pipe_buffer をスプレー
2. freed ページに pipe_buffer を配置
3. そこからカーネルアドレスをリーク
4. ポインタを書き換えて任意書き込みプリミティブを構築
5. msg_msg を使って制御可能なデータを書き込む
6. modprobe_path を `/tmp/ex` に変更
7. 不正バイナリを実行して modprobe を発火
8. root 権限でスクリプトを実行し flag を取得

---

### なぜこの方法が安定するか

- race condition に依存しない
- 構造体を壊さない
- 任意書き込みが deterministic

---

## DirtyPipe が使えない理由

```
/proc/sys/kernel/modprobe
```

は page cache を使用しないため、DirtyPipe の対象外です。

---

## busybox の罠

```
/sbin/modprobe → busybox
```

のため、書き換えるとシステム全体が壊れます。

---

## まとめ

- refcount は絶対に壊さない
- 必要最小限のみ書き換える
- modprobe_path が最も安定した昇格手法

---

## 学んだこと

- UAF exploit の基本
- slab allocator の挙動
- DirtyPipe の制約
- kernel exploit における最小変更の重要性
