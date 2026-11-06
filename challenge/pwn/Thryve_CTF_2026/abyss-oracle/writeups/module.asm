
extracted/abyss_oracle.ko:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <.text>:
   0:	90                   	nop
   1:	90                   	nop
   2:	90                   	nop
   3:	90                   	nop
   4:	90                   	nop
   5:	90                   	nop
   6:	90                   	nop
   7:	90                   	nop
   8:	90                   	nop
   9:	90                   	nop
   a:	90                   	nop
   b:	90                   	nop
   c:	90                   	nop
   d:	90                   	nop
   e:	90                   	nop
   f:	90                   	nop
  10:	f3 0f 1e fa          	endbr64
  14:	e8 00 00 00 00       	call   19 <.text+0x19>	15: R_X86_64_PLT32	__fentry__-0x4
  19:	48 8b 47 10          	mov    rax,QWORD PTR [rdi+0x10]
  1d:	48 33 47 30          	xor    rax,QWORD PTR [rdi+0x30]
  21:	48 33 47 40          	xor    rax,QWORD PTR [rdi+0x40]
  25:	e9 00 00 00 00       	jmp    2a <.text+0x2a>	26: R_X86_64_PLT32	__x86_return_thunk-0x4
  2a:	66 0f 1f 44 00 00    	nop    WORD PTR [rax+rax*1+0x0]
  30:	90                   	nop
  31:	90                   	nop
  32:	90                   	nop
  33:	90                   	nop
  34:	90                   	nop
  35:	90                   	nop
  36:	90                   	nop
  37:	90                   	nop
  38:	90                   	nop
  39:	90                   	nop
  3a:	90                   	nop
  3b:	90                   	nop
  3c:	90                   	nop
  3d:	90                   	nop
  3e:	90                   	nop
  3f:	90                   	nop
  40:	e8 00 00 00 00       	call   45 <.text+0x45>	41: R_X86_64_PLT32	__fentry__-0x4
  45:	41 55                	push   r13
  47:	b9 10 00 00 00       	mov    ecx,0x10
  4c:	ba 18 00 00 00       	mov    edx,0x18
  51:	41 54                	push   r12
  53:	55                   	push   rbp
  54:	48 89 fd             	mov    rbp,rdi
  57:	53                   	push   rbx
  58:	48 81 ec a0 00 00 00 	sub    rsp,0xa0
  5f:	65 48 8b 04 25 28 00 00 00 	mov    rax,QWORD PTR gs:0x28
  68:	48 89 84 24 98 00 00 00 	mov    QWORD PTR [rsp+0x98],rax
  70:	31 c0                	xor    eax,eax
  72:	4c 8d 64 24 18       	lea    r12,[rsp+0x18]
  77:	48 c7 04 24 00 00 00 00 	mov    QWORD PTR [rsp],0x0
  7f:	48 c7 44 24 08 00 00 00 00 	mov    QWORD PTR [rsp+0x8],0x0
  88:	4c 89 e7             	mov    rdi,r12
  8b:	48 c7 44 24 10 00 00 00 00 	mov    QWORD PTR [rsp+0x10],0x0
  94:	f3 48 ab             	rep stos QWORD PTR [rdi],rax
  97:	48 89 e7             	mov    rdi,rsp
  9a:	e8 00 00 00 00       	call   9f <.text+0x9f>	9b: R_X86_64_PLT32	_copy_from_user-0x4
  9f:	48 85 c0             	test   rax,rax
  a2:	0f 85 34 01 00 00    	jne    1dc <.text+0x1dc>
  a8:	8b 04 24             	mov    eax,DWORD PTR [rsp]
  ab:	83 f8 3f             	cmp    eax,0x3f
  ae:	0f 87 1f 01 00 00    	ja     1d3 <.text+0x1d3>
  b4:	8b 54 24 04          	mov    edx,DWORD PTR [rsp+0x4]
  b8:	8d 4a ff             	lea    ecx,[rdx-0x1]
  bb:	83 f9 7f             	cmp    ecx,0x7f
  be:	0f 87 0f 01 00 00    	ja     1d3 <.text+0x1d3>
  c4:	48 c1 e0 04          	shl    rax,0x4
  c8:	48 83 7c 28 30 00    	cmp    QWORD PTR [rax+rbp*1+0x30],0x0
  ce:	0f 85 11 01 00 00    	jne    1e5 <.text+0x1e5>
  d4:	89 d3                	mov    ebx,edx
  d6:	4c 8b 6c 24 10       	mov    r13,QWORD PTR [rsp+0x10]
  db:	31 d2                	xor    edx,edx
  dd:	4c 89 e7             	mov    rdi,r12
  e0:	48 89 de             	mov    rsi,rbx
  e3:	e8 00 00 00 00       	call   e8 <.text+0xe8>	e4: R_X86_64_PLT32	__check_object_size-0x4
  e8:	48 89 da             	mov    rdx,rbx
  eb:	4c 89 ee             	mov    rsi,r13
  ee:	4c 89 e7             	mov    rdi,r12
  f1:	e8 00 00 00 00       	call   f6 <.text+0xf6>	f2: R_X86_64_PLT32	_copy_from_user-0x4
  f6:	48 85 c0             	test   rax,rax
  f9:	0f 85 dd 00 00 00    	jne    1dc <.text+0x1dc>
  ff:	48 8b 3d 00 00 00 00 	mov    rdi,QWORD PTR [rip+0x0]        # 106 <.text+0x106>	102: R_X86_64_PC32	.bss-0x4
 106:	be c0 0d 00 00       	mov    esi,0xdc0
 10b:	e8 00 00 00 00       	call   110 <.text+0x110>	10c: R_X86_64_PLT32	kmem_cache_alloc_noprof-0x4
 110:	48 89 c3             	mov    rbx,rax
 113:	48 85 c0             	test   rax,rax
 116:	0f 84 d2 00 00 00    	je     1ee <.text+0x1ee>
 11c:	c7 43 08 01 00 00 00 	mov    DWORD PTR [rbx+0x8],0x1
 123:	48 8d 7b 10          	lea    rdi,[rbx+0x10]
 127:	be 08 00 00 00       	mov    esi,0x8
 12c:	48 b8 37 13 00 00 01 00 00 00 	movabs rax,0x100001337
 136:	48 89 03             	mov    QWORD PTR [rbx],rax
 139:	e8 00 00 00 00       	call   13e <.text+0x13e>	13a: R_X86_64_PLT32	get_random_bytes-0x4
 13e:	48 8b 54 24 08       	mov    rdx,QWORD PTR [rsp+0x8]
 143:	48 8b 43 10          	mov    rax,QWORD PTR [rbx+0x10]
 147:	48 8d 7b 38          	lea    rdi,[rbx+0x38]
 14b:	48 8b 4d 20          	mov    rcx,QWORD PTR [rbp+0x20]
 14f:	83 e2 1f             	and    edx,0x1f
 152:	48 0d 01 01 00 00    	or     rax,0x101
 158:	48 89 53 18          	mov    QWORD PTR [rbx+0x18],rdx
 15c:	48 8b 55 28          	mov    rdx,QWORD PTR [rbp+0x28]
 160:	48 31 f9             	xor    rcx,rdi
 163:	48 89 43 10          	mov    QWORD PTR [rbx+0x10],rax
 167:	48 c1 c0 11          	rol    rax,0x11
 16b:	48 89 53 20          	mov    QWORD PTR [rbx+0x20],rdx
 16f:	8b 54 24 04          	mov    edx,DWORD PTR [rsp+0x4]
 173:	48 31 c8             	xor    rax,rcx
 176:	48 89 43 28          	mov    QWORD PTR [rbx+0x28],rax
 17a:	48 89 53 30          	mov    QWORD PTR [rbx+0x30],rdx
 17e:	48 81 fa 80 00 00 00 	cmp    rdx,0x80
 185:	0f 87 00 00 00 00    	ja     18b <.text+0x18b>	187: R_X86_64_PC32	.text.unlikely-0x4
 18b:	4c 89 e6             	mov    rsi,r12
 18e:	e8 00 00 00 00       	call   193 <.text+0x193>	18f: R_X86_64_PLT32	memcpy-0x4
 193:	8b 04 24             	mov    eax,DWORD PTR [rsp]
 196:	48 83 c0 03          	add    rax,0x3
 19a:	48 c1 e0 04          	shl    rax,0x4
 19e:	48 89 5c 05 00       	mov    QWORD PTR [rbp+rax*1+0x0],rbx
 1a3:	48 c7 44 05 08 37 13 00 00 	mov    QWORD PTR [rbp+rax*1+0x8],0x1337
 1ac:	31 c0                	xor    eax,eax
 1ae:	48 8b 94 24 98 00 00 00 	mov    rdx,QWORD PTR [rsp+0x98]
 1b6:	65 48 2b 14 25 28 00 00 00 	sub    rdx,QWORD PTR gs:0x28
 1bf:	75 36                	jne    1f7 <.text+0x1f7>
 1c1:	48 81 c4 a0 00 00 00 	add    rsp,0xa0
 1c8:	5b                   	pop    rbx
 1c9:	5d                   	pop    rbp
 1ca:	41 5c                	pop    r12
 1cc:	41 5d                	pop    r13
 1ce:	e9 00 00 00 00       	jmp    1d3 <.text+0x1d3>	1cf: R_X86_64_PLT32	__x86_return_thunk-0x4
 1d3:	48 c7 c0 ea ff ff ff 	mov    rax,0xffffffffffffffea
 1da:	eb d2                	jmp    1ae <.text+0x1ae>
 1dc:	48 c7 c0 f2 ff ff ff 	mov    rax,0xfffffffffffffff2
 1e3:	eb c9                	jmp    1ae <.text+0x1ae>
 1e5:	48 c7 c0 f0 ff ff ff 	mov    rax,0xfffffffffffffff0
 1ec:	eb c0                	jmp    1ae <.text+0x1ae>
 1ee:	48 c7 c0 f4 ff ff ff 	mov    rax,0xfffffffffffffff4
 1f5:	eb b7                	jmp    1ae <.text+0x1ae>
 1f7:	e8 00 00 00 00       	call   1fc <.text+0x1fc>	1f8: R_X86_64_PLT32	__stack_chk_fail-0x4
 1fc:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
 200:	90                   	nop
 201:	90                   	nop
 202:	90                   	nop
 203:	90                   	nop
 204:	90                   	nop
 205:	90                   	nop
 206:	90                   	nop
 207:	90                   	nop
 208:	90                   	nop
 209:	90                   	nop
 20a:	90                   	nop
 20b:	90                   	nop
 20c:	90                   	nop
 20d:	90                   	nop
 20e:	90                   	nop
 20f:	90                   	nop
 210:	e8 00 00 00 00       	call   215 <.text+0x215>	211: R_X86_64_PLT32	__fentry__-0x4
 215:	41 55                	push   r13
 217:	b9 10 00 00 00       	mov    ecx,0x10
 21c:	ba 18 00 00 00       	mov    edx,0x18
 221:	41 54                	push   r12
 223:	55                   	push   rbp
 224:	48 89 fd             	mov    rbp,rdi
 227:	53                   	push   rbx
 228:	48 81 ec a0 00 00 00 	sub    rsp,0xa0
 22f:	65 48 8b 04 25 28 00 00 00 	mov    rax,QWORD PTR gs:0x28
 238:	48 89 84 24 98 00 00 00 	mov    QWORD PTR [rsp+0x98],rax
 240:	31 c0                	xor    eax,eax
 242:	48 8d 5c 24 18       	lea    rbx,[rsp+0x18]
 247:	48 c7 04 24 00 00 00 00 	mov    QWORD PTR [rsp],0x0
 24f:	48 c7 44 24 08 00 00 00 00 	mov    QWORD PTR [rsp+0x8],0x0
 258:	48 89 df             	mov    rdi,rbx
 25b:	48 c7 44 24 10 00 00 00 00 	mov    QWORD PTR [rsp+0x10],0x0
 264:	f3 48 ab             	rep stos QWORD PTR [rdi],rax
 267:	48 89 e7             	mov    rdi,rsp
 26a:	e8 00 00 00 00       	call   26f <.text+0x26f>	26b: R_X86_64_PLT32	_copy_from_user-0x4
 26f:	48 85 c0             	test   rax,rax
 272:	0f 85 29 01 00 00    	jne    3a1 <.text+0x3a1>
 278:	8b 04 24             	mov    eax,DWORD PTR [rsp]
 27b:	83 f8 3f             	cmp    eax,0x3f
 27e:	0f 87 07 01 00 00    	ja     38b <.text+0x38b>
 284:	8b 54 24 04          	mov    edx,DWORD PTR [rsp+0x4]
 288:	81 fa 80 00 00 00    	cmp    edx,0x80
 28e:	0f 87 f7 00 00 00    	ja     38b <.text+0x38b>
 294:	48 8b 7c 24 08       	mov    rdi,QWORD PTR [rsp+0x8]
 299:	40 f6 c7 07          	test   dil,0x7
 29d:	0f 85 e8 00 00 00    	jne    38b <.text+0x38b>
 2a3:	48 c1 e0 04          	shl    rax,0x4
 2a7:	48 01 e8             	add    rax,rbp
 2aa:	48 8b 48 30          	mov    rcx,QWORD PTR [rax+0x30]
 2ae:	48 85 c9             	test   rcx,rcx
 2b1:	0f 84 fc 00 00 00    	je     3b3 <.text+0x3b3>
 2b7:	48 8b 75 28          	mov    rsi,QWORD PTR [rbp+0x28]
 2bb:	48 39 71 20          	cmp    QWORD PTR [rcx+0x20],rsi
 2bf:	0f 85 e5 00 00 00    	jne    3aa <.text+0x3aa>
 2c5:	f6 41 18 01          	test   BYTE PTR [rcx+0x18],0x1
 2c9:	0f 84 db 00 00 00    	je     3aa <.text+0x3aa>
 2cf:	48 8b 41 10          	mov    rax,QWORD PTR [rcx+0x10]
 2d3:	48 8b 71 28          	mov    rsi,QWORD PTR [rcx+0x28]
 2d7:	48 33 75 20          	xor    rsi,QWORD PTR [rbp+0x20]
 2db:	48 c1 c0 11          	rol    rax,0x11
 2df:	48 31 c6             	xor    rsi,rax
 2e2:	48 8b 41 30          	mov    rax,QWORD PTR [rcx+0x30]
 2e6:	48 85 f6             	test   rsi,rsi
 2e9:	0f 84 9c 00 00 00    	je     38b <.text+0x38b>
 2ef:	48 89 f9             	mov    rcx,rdi
 2f2:	48 01 d1             	add    rcx,rdx
 2f5:	0f 82 90 00 00 00    	jb     38b <.text+0x38b>
 2fb:	48 39 c8             	cmp    rax,rcx
 2fe:	0f 82 87 00 00 00    	jb     38b <.text+0x38b>
 304:	48 01 fe             	add    rsi,rdi
 307:	48 3b 35 00 00 00 00 	cmp    rsi,QWORD PTR [rip+0x0]        # 30e <.text+0x30e>	30a: R_X86_64_PC32	page_offset_base-0x4
 30e:	48 c7 c5 ff ff ff ff 	mov    rbp,0xffffffffffffffff
 315:	72 4c                	jb     363 <.text+0x363>
 317:	40 f6 c6 07          	test   sil,0x7
 31b:	75 46                	jne    363 <.text+0x363>
 31d:	48 89 df             	mov    rdi,rbx
 320:	e8 00 00 00 00       	call   325 <.text+0x325>	321: R_X86_64_PLT32	copy_from_kernel_nofault-0x4
 325:	48 89 c5             	mov    rbp,rax
 328:	48 85 c0             	test   rax,rax
 32b:	75 74                	jne    3a1 <.text+0x3a1>
 32d:	44 8b 64 24 04       	mov    r12d,DWORD PTR [rsp+0x4]
 332:	4c 8b 6c 24 10       	mov    r13,QWORD PTR [rsp+0x10]
 337:	49 81 fc 80 00 00 00 	cmp    r12,0x80
 33e:	77 54                	ja     394 <.text+0x394>
 340:	ba 01 00 00 00       	mov    edx,0x1
 345:	4c 89 e6             	mov    rsi,r12
 348:	48 89 df             	mov    rdi,rbx
 34b:	e8 00 00 00 00       	call   350 <.text+0x350>	34c: R_X86_64_PLT32	__check_object_size-0x4
 350:	4c 89 e2             	mov    rdx,r12
 353:	48 89 de             	mov    rsi,rbx
 356:	4c 89 ef             	mov    rdi,r13
 359:	e8 00 00 00 00       	call   35e <.text+0x35e>	35a: R_X86_64_PLT32	_copy_to_user-0x4
 35e:	48 85 c0             	test   rax,rax
 361:	75 3e                	jne    3a1 <.text+0x3a1>
 363:	48 8b 84 24 98 00 00 00 	mov    rax,QWORD PTR [rsp+0x98]
 36b:	65 48 2b 04 25 28 00 00 00 	sub    rax,QWORD PTR gs:0x28
 374:	75 46                	jne    3bc <.text+0x3bc>
 376:	48 81 c4 a0 00 00 00 	add    rsp,0xa0
 37d:	48 89 e8             	mov    rax,rbp
 380:	5b                   	pop    rbx
 381:	5d                   	pop    rbp
 382:	41 5c                	pop    r12
 384:	41 5d                	pop    r13
 386:	e9 00 00 00 00       	jmp    38b <.text+0x38b>	387: R_X86_64_PLT32	__x86_return_thunk-0x4
 38b:	48 c7 c5 ea ff ff ff 	mov    rbp,0xffffffffffffffea
 392:	eb cf                	jmp    363 <.text+0x363>
 394:	4c 89 e6             	mov    rsi,r12
 397:	bf 80 00 00 00       	mov    edi,0x80
 39c:	e8 00 00 00 00       	call   3a1 <.text+0x3a1>	39d: R_X86_64_PLT32	__copy_overflow-0x4
 3a1:	48 c7 c5 f2 ff ff ff 	mov    rbp,0xfffffffffffffff2
 3a8:	eb b9                	jmp    363 <.text+0x363>
 3aa:	48 c7 c5 ff ff ff ff 	mov    rbp,0xffffffffffffffff
 3b1:	eb b0                	jmp    363 <.text+0x363>
 3b3:	48 c7 c5 fe ff ff ff 	mov    rbp,0xfffffffffffffffe
 3ba:	eb a7                	jmp    363 <.text+0x363>
 3bc:	e8 00 00 00 00       	call   3c1 <.text+0x3c1>	3bd: R_X86_64_PLT32	__stack_chk_fail-0x4
 3c1:	66 66 2e 0f 1f 84 00 00 00 00 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
 3cc:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
 3d0:	90                   	nop
 3d1:	90                   	nop
 3d2:	90                   	nop
 3d3:	90                   	nop
 3d4:	90                   	nop
 3d5:	90                   	nop
 3d6:	90                   	nop
 3d7:	90                   	nop
 3d8:	90                   	nop
 3d9:	90                   	nop
 3da:	90                   	nop
 3db:	90                   	nop
 3dc:	90                   	nop
 3dd:	90                   	nop
 3de:	90                   	nop
 3df:	90                   	nop
 3e0:	f3 0f 1e fa          	endbr64
 3e4:	e8 00 00 00 00       	call   3e9 <.text+0x3e9>	3e5: R_X86_64_PLT32	__fentry__-0x4
 3e9:	55                   	push   rbp
 3ea:	48 8b 3d 00 00 00 00 	mov    rdi,QWORD PTR [rip+0x0]        # 3f1 <.text+0x3f1>	3ed: R_X86_64_PC32	kmalloc_caches+0x54
 3f1:	48 89 f5             	mov    rbp,rsi
 3f4:	ba 38 05 00 00       	mov    edx,0x538
 3f9:	53                   	push   rbx
 3fa:	be c0 0d 00 00       	mov    esi,0xdc0
 3ff:	e8 00 00 00 00       	call   404 <.text+0x404>	400: R_X86_64_PLT32	__kmalloc_cache_noprof-0x4
 404:	48 85 c0             	test   rax,rax
 407:	74 5e                	je     467 <.text+0x467>
 409:	48 89 c3             	mov    rbx,rax
 40c:	48 89 c7             	mov    rdi,rax
 40f:	48 c7 c2 00 00 00 00 	mov    rdx,0x0	412: R_X86_64_32S	.bss
 416:	48 c7 c6 00 00 00 00 	mov    rsi,0x0	419: R_X86_64_32S	.rodata.str1.1+0x18
 41d:	e8 00 00 00 00       	call   422 <.text+0x422>	41e: R_X86_64_PLT32	__mutex_init-0x4
 422:	48 8d 7b 20          	lea    rdi,[rbx+0x20]
 426:	be 08 00 00 00       	mov    esi,0x8
 42b:	e8 00 00 00 00       	call   430 <.text+0x430>	42c: R_X86_64_PLT32	get_random_bytes-0x4
 430:	48 8d 7b 28          	lea    rdi,[rbx+0x28]
 434:	be 08 00 00 00       	mov    esi,0x8
 439:	e8 00 00 00 00       	call   43e <.text+0x43e>	43a: R_X86_64_PLT32	get_random_bytes-0x4
 43e:	48 89 5d 20          	mov    QWORD PTR [rbp+0x20],rbx
 442:	48 b8 01 01 01 01 01 01 01 01 	movabs rax,0x101010101010101
 44c:	48 09 43 20          	or     QWORD PTR [rbx+0x20],rax
 450:	48 b8 02 02 02 02 02 02 02 02 	movabs rax,0x202020202020202
 45a:	48 09 43 28          	or     QWORD PTR [rbx+0x28],rax
 45e:	31 c0                	xor    eax,eax
 460:	5b                   	pop    rbx
 461:	5d                   	pop    rbp
 462:	e9 00 00 00 00       	jmp    467 <.text+0x467>	463: R_X86_64_PLT32	__x86_return_thunk-0x4
 467:	b8 f4 ff ff ff       	mov    eax,0xfffffff4
 46c:	eb f2                	jmp    460 <.text+0x460>
 46e:	66 90                	xchg   ax,ax
 470:	90                   	nop
 471:	90                   	nop
 472:	90                   	nop
 473:	90                   	nop
 474:	90                   	nop
 475:	90                   	nop
 476:	90                   	nop
 477:	90                   	nop
 478:	90                   	nop
 479:	90                   	nop
 47a:	90                   	nop
 47b:	90                   	nop
 47c:	90                   	nop
 47d:	90                   	nop
 47e:	90                   	nop
 47f:	90                   	nop
 480:	f3 0f 1e fa          	endbr64
 484:	e8 00 00 00 00       	call   489 <.text+0x489>	485: R_X86_64_PLT32	__fentry__-0x4
 489:	41 56                	push   r14
 48b:	41 55                	push   r13
 48d:	41 54                	push   r12
 48f:	55                   	push   rbp
 490:	53                   	push   rbx
 491:	4c 8b 6e 20          	mov    r13,QWORD PTR [rsi+0x20]
 495:	4d 85 ed             	test   r13,r13
 498:	0f 84 01 01 00 00    	je     59f <.text+0x59f>
 49e:	4c 89 ef             	mov    rdi,r13
 4a1:	49 8d 5d 30          	lea    rbx,[r13+0x30]
 4a5:	49 8d ad 30 04 00 00 	lea    rbp,[r13+0x430]
 4ac:	41 be ff ff ff ff    	mov    r14d,0xffffffff
 4b2:	e8 00 00 00 00       	call   4b7 <.text+0x4b7>	4b3: R_X86_64_PLT32	mutex_lock-0x4
 4b7:	eb 23                	jmp    4dc <.text+0x4dc>
 4b9:	3d 42 41 00 00       	cmp    eax,0x4142
 4be:	74 35                	je     4f5 <.text+0x4f5>
 4c0:	48 c7 03 00 00 00 00 	mov    QWORD PTR [rbx],0x0
 4c7:	48 c7 43 08 00 00 00 00 	mov    QWORD PTR [rbx+0x8],0x0
 4cf:	48 83 c3 10          	add    rbx,0x10
 4d3:	48 39 dd             	cmp    rbp,rbx
 4d6:	0f 84 85 00 00 00    	je     561 <.text+0x561>
 4dc:	4c 8b 23             	mov    r12,QWORD PTR [rbx]
 4df:	4d 85 e4             	test   r12,r12
 4e2:	74 eb                	je     4cf <.text+0x4cf>
 4e4:	8b 43 0c             	mov    eax,DWORD PTR [rbx+0xc]
 4e7:	85 c0                	test   eax,eax
 4e9:	75 d5                	jne    4c0 <.text+0x4c0>
 4eb:	8b 43 08             	mov    eax,DWORD PTR [rbx+0x8]
 4ee:	3d 37 13 00 00       	cmp    eax,0x1337
 4f3:	75 c4                	jne    4b9 <.text+0x4b9>
 4f5:	49 8d 7c 24 08       	lea    rdi,[r12+0x8]
 4fa:	44 89 f0             	mov    eax,r14d
 4fd:	f0 41 0f c1 44 24 08 	lock xadd DWORD PTR [r12+0x8],eax
 504:	83 f8 01             	cmp    eax,0x1
 507:	74 10                	je     519 <.text+0x519>
 509:	85 c0                	test   eax,eax
 50b:	7f b3                	jg     4c0 <.text+0x4c0>
 50d:	be 03 00 00 00       	mov    esi,0x3
 512:	e8 00 00 00 00       	call   517 <.text+0x517>	513: R_X86_64_PLT32	refcount_warn_saturate-0x4
 517:	eb a7                	jmp    4c0 <.text+0x4c0>
 519:	41 8b 85 30 05 00 00 	mov    eax,DWORD PTR [r13+0x530]
 520:	89 c2                	mov    edx,eax
 522:	83 e2 1f             	and    edx,0x1f
 525:	49 8b b4 d5 30 04 00 00 	mov    rsi,QWORD PTR [r13+rdx*8+0x430]
 52d:	48 85 f6             	test   rsi,rsi
 530:	74 18                	je     54a <.text+0x54a>
 532:	48 8b 3d 00 00 00 00 	mov    rdi,QWORD PTR [rip+0x0]        # 539 <.text+0x539>	535: R_X86_64_PC32	.bss-0x4
 539:	e8 00 00 00 00       	call   53e <.text+0x53e>	53a: R_X86_64_PLT32	kmem_cache_free-0x4
 53e:	41 8b 85 30 05 00 00 	mov    eax,DWORD PTR [r13+0x530]
 545:	89 c2                	mov    edx,eax
 547:	83 e2 1f             	and    edx,0x1f
 54a:	83 c0 01             	add    eax,0x1
 54d:	4d 89 a4 d5 30 04 00 00 	mov    QWORD PTR [r13+rdx*8+0x430],r12
 555:	41 89 85 30 05 00 00 	mov    DWORD PTR [r13+0x530],eax
 55c:	e9 5f ff ff ff       	jmp    4c0 <.text+0x4c0>
 561:	48 89 eb             	mov    rbx,rbp
 564:	49 8d ad 30 05 00 00 	lea    rbp,[r13+0x530]
 56b:	48 8b 33             	mov    rsi,QWORD PTR [rbx]
 56e:	48 85 f6             	test   rsi,rsi
 571:	74 13                	je     586 <.text+0x586>
 573:	48 8b 3d 00 00 00 00 	mov    rdi,QWORD PTR [rip+0x0]        # 57a <.text+0x57a>	576: R_X86_64_PC32	.bss-0x4
 57a:	e8 00 00 00 00       	call   57f <.text+0x57f>	57b: R_X86_64_PLT32	kmem_cache_free-0x4
 57f:	48 c7 03 00 00 00 00 	mov    QWORD PTR [rbx],0x0
 586:	48 83 c3 08          	add    rbx,0x8
 58a:	48 39 dd             	cmp    rbp,rbx
 58d:	75 dc                	jne    56b <.text+0x56b>
 58f:	4c 89 ef             	mov    rdi,r13
 592:	e8 00 00 00 00       	call   597 <.text+0x597>	593: R_X86_64_PLT32	mutex_unlock-0x4
 597:	4c 89 ef             	mov    rdi,r13
 59a:	e8 00 00 00 00       	call   59f <.text+0x59f>	59b: R_X86_64_PLT32	kfree-0x4
 59f:	5b                   	pop    rbx
 5a0:	31 c0                	xor    eax,eax
 5a2:	5d                   	pop    rbp
 5a3:	41 5c                	pop    r12
 5a5:	41 5d                	pop    r13
 5a7:	41 5e                	pop    r14
 5a9:	e9 00 00 00 00       	jmp    5ae <.text+0x5ae>	5aa: R_X86_64_PLT32	__x86_return_thunk-0x4
 5ae:	66 90                	xchg   ax,ax
 5b0:	90                   	nop
 5b1:	90                   	nop
 5b2:	90                   	nop
 5b3:	90                   	nop
 5b4:	90                   	nop
 5b5:	90                   	nop
 5b6:	90                   	nop
 5b7:	90                   	nop
 5b8:	90                   	nop
 5b9:	90                   	nop
 5ba:	90                   	nop
 5bb:	90                   	nop
 5bc:	90                   	nop
 5bd:	90                   	nop
 5be:	90                   	nop
 5bf:	90                   	nop
 5c0:	f3 0f 1e fa          	endbr64
 5c4:	e8 00 00 00 00       	call   5c9 <.text+0x5c9>	5c5: R_X86_64_PLT32	__fentry__-0x4
 5c9:	41 56                	push   r14
 5cb:	41 55                	push   r13
 5cd:	41 54                	push   r12
 5cf:	55                   	push   rbp
 5d0:	53                   	push   rbx
 5d1:	48 83 ec 38          	sub    rsp,0x38
 5d5:	65 48 8b 2c 25 28 00 00 00 	mov    rbp,QWORD PTR gs:0x28
 5de:	48 89 6c 24 30       	mov    QWORD PTR [rsp+0x30],rbp
 5e3:	48 8b 6f 20          	mov    rbp,QWORD PTR [rdi+0x20]
 5e7:	48 85 ed             	test   rbp,rbp
 5ea:	0f 84 fd 08 00 00    	je     eed <.text+0xeed>
 5f0:	89 f3                	mov    ebx,esi
 5f2:	48 89 ef             	mov    rdi,rbp
 5f5:	49 89 d4             	mov    r12,rdx
 5f8:	e8 00 00 00 00       	call   5fd <.text+0x5fd>	5f9: R_X86_64_PLT32	mutex_lock-0x4
 5fd:	81 fb 01 a8 18 40    	cmp    ebx,0x4018a801
 603:	0f 84 52 07 00 00    	je     d5b <.text+0xd5b>
 609:	0f 87 dd 00 00 00    	ja     6ec <.text+0x6ec>
 60f:	81 fb 05 a8 04 40    	cmp    ebx,0x4004a805
 615:	0f 84 66 07 00 00    	je     d81 <.text+0xd81>
 61b:	0f 87 df 01 00 00    	ja     800 <.text+0x800>
 621:	81 fb 0a a8 00 00    	cmp    ebx,0xa80a
 627:	0f 84 f2 05 00 00    	je     c1f <.text+0xc1f>
 62d:	81 fb 02 a8 04 40    	cmp    ebx,0x4004a802
 633:	0f 85 2b 06 00 00    	jne    c64 <.text+0xc64>
 639:	48 8d 7c 24 08       	lea    rdi,[rsp+0x8]
 63e:	ba 04 00 00 00       	mov    edx,0x4
 643:	4c 89 e6             	mov    rsi,r12
 646:	c7 44 24 08 00 00 00 00 	mov    DWORD PTR [rsp+0x8],0x0
 64e:	e8 00 00 00 00       	call   653 <.text+0x653>	64f: R_X86_64_PLT32	_copy_from_user-0x4
 653:	48 85 c0             	test   rax,rax
 656:	0f 85 f3 06 00 00    	jne    d4f <.text+0xd4f>
 65c:	8b 44 24 08          	mov    eax,DWORD PTR [rsp+0x8]
 660:	83 f8 3f             	cmp    eax,0x3f
 663:	0f 87 fb 05 00 00    	ja     c64 <.text+0xc64>
 669:	48 c1 e0 04          	shl    rax,0x4
 66d:	48 01 e8             	add    rax,rbp
 670:	48 8b 50 30          	mov    rdx,QWORD PTR [rax+0x30]
 674:	48 85 d2             	test   rdx,rdx
 677:	0f 84 64 08 00 00    	je     ee1 <.text+0xee1>
 67d:	81 78 38 37 13 00 00 	cmp    DWORD PTR [rax+0x38],0x1337
 684:	0f 85 57 08 00 00    	jne    ee1 <.text+0xee1>
 68a:	48 8b 45 28          	mov    rax,QWORD PTR [rbp+0x28]
 68e:	48 39 42 20          	cmp    QWORD PTR [rdx+0x20],rax
 692:	0f 85 c0 05 00 00    	jne    c58 <.text+0xc58>
 698:	81 3a 37 13 00 00    	cmp    DWORD PTR [rdx],0x1337
 69e:	0f 85 b4 05 00 00    	jne    c58 <.text+0xc58>
 6a4:	83 7a 04 01          	cmp    DWORD PTR [rdx+0x4],0x1
 6a8:	0f 85 b6 05 00 00    	jne    c64 <.text+0xc64>
 6ae:	48 83 62 18 1f       	and    QWORD PTR [rdx+0x18],0x1f
 6b3:	31 db                	xor    ebx,ebx
 6b5:	c7 42 04 02 00 00 00 	mov    DWORD PTR [rdx+0x4],0x2
 6bc:	48 89 ef             	mov    rdi,rbp
 6bf:	e8 00 00 00 00       	call   6c4 <.text+0x6c4>	6c0: R_X86_64_PLT32	mutex_unlock-0x4
 6c4:	48 8b 44 24 30       	mov    rax,QWORD PTR [rsp+0x30]
 6c9:	65 48 2b 04 25 28 00 00 00 	sub    rax,QWORD PTR gs:0x28
 6d2:	0f 85 9a 08 00 00    	jne    f72 <.text+0xf72>
 6d8:	48 83 c4 38          	add    rsp,0x38
 6dc:	48 89 d8             	mov    rax,rbx
 6df:	5b                   	pop    rbx
 6e0:	5d                   	pop    rbp
 6e1:	41 5c                	pop    r12
 6e3:	41 5d                	pop    r13
 6e5:	41 5e                	pop    r14
 6e7:	e9 00 00 00 00       	jmp    6ec <.text+0x6ec>	6e8: R_X86_64_PLT32	__x86_return_thunk-0x4
 6ec:	81 fb 06 a8 18 c0    	cmp    ebx,0xc018a806
 6f2:	0f 84 76 06 00 00    	je     d6e <.text+0xd6e>
 6f8:	0f 87 72 05 00 00    	ja     c70 <.text+0xc70>
 6fe:	81 fb 07 a8 18 40    	cmp    ebx,0x4018a807
 704:	0f 84 ed 02 00 00    	je     9f7 <.text+0x9f7>
 70a:	81 fb 08 a8 18 40    	cmp    ebx,0x4018a808
 710:	0f 85 4e 05 00 00    	jne    c64 <.text+0xc64>
 716:	48 8d 7c 24 08       	lea    rdi,[rsp+0x8]
 71b:	ba 18 00 00 00       	mov    edx,0x18
 720:	4c 89 e6             	mov    rsi,r12
 723:	48 c7 44 24 08 00 00 00 00 	mov    QWORD PTR [rsp+0x8],0x0
 72c:	48 c7 44 24 10 00 00 00 00 	mov    QWORD PTR [rsp+0x10],0x0
 735:	48 c7 44 24 18 00 00 00 00 	mov    QWORD PTR [rsp+0x18],0x0
 73e:	e8 00 00 00 00       	call   743 <.text+0x743>	73f: R_X86_64_PLT32	_copy_from_user-0x4
 743:	48 85 c0             	test   rax,rax
 746:	0f 85 03 06 00 00    	jne    d4f <.text+0xd4f>
 74c:	8b 44 24 08          	mov    eax,DWORD PTR [rsp+0x8]
 750:	83 f8 3f             	cmp    eax,0x3f
 753:	0f 87 0b 05 00 00    	ja     c64 <.text+0xc64>
 759:	48 c1 e0 04          	shl    rax,0x4
 75d:	48 01 e8             	add    rax,rbp
 760:	48 8b 50 30          	mov    rdx,QWORD PTR [rax+0x30]
 764:	48 85 d2             	test   rdx,rdx
 767:	0f 84 74 07 00 00    	je     ee1 <.text+0xee1>
 76d:	81 78 38 42 41 00 00 	cmp    DWORD PTR [rax+0x38],0x4142
 774:	0f 85 67 07 00 00    	jne    ee1 <.text+0xee1>
 77a:	48 8b 74 24 18       	mov    rsi,QWORD PTR [rsp+0x18]
 77f:	48 81 fe 00 04 00 00 	cmp    rsi,0x400
 786:	0f 87 d8 04 00 00    	ja     c64 <.text+0xc64>
 78c:	48 8b 45 28          	mov    rax,QWORD PTR [rbp+0x28]
 790:	48 39 42 20          	cmp    QWORD PTR [rdx+0x20],rax
 794:	0f 85 be 04 00 00    	jne    c58 <.text+0xc58>
 79a:	81 3a 42 41 00 00    	cmp    DWORD PTR [rdx],0x4142
 7a0:	0f 85 b2 04 00 00    	jne    c58 <.text+0xc58>
 7a6:	f6 42 18 20          	test   BYTE PTR [rdx+0x18],0x20
 7aa:	0f 84 a8 04 00 00    	je     c58 <.text+0xc58>
 7b0:	48 81 7a 38 00 00 00 00 	cmp    QWORD PTR [rdx+0x38],0x0	7b4: R_X86_64_32S	.rodata+0x108
 7b8:	0f 85 9a 04 00 00    	jne    c58 <.text+0xc58>
 7be:	48 8b 7c 24 10       	mov    rdi,QWORD PTR [rsp+0x10]
 7c3:	48 8b 45 20          	mov    rax,QWORD PTR [rbp+0x20]
 7c7:	48 c7 c3 ff ff ff ff 	mov    rbx,0xffffffffffffffff
 7ce:	48 8b 4a 10          	mov    rcx,QWORD PTR [rdx+0x10]
 7d2:	48 31 f8             	xor    rax,rdi
 7d5:	48 c1 c1 11          	rol    rcx,0x11
 7d9:	48 31 c8             	xor    rax,rcx
 7dc:	48 3b 05 00 00 00 00 	cmp    rax,QWORD PTR [rip+0x0]        # 7e3 <.text+0x7e3>	7df: R_X86_64_PC32	page_offset_base-0x4
 7e3:	0f 82 d3 fe ff ff    	jb     6bc <.text+0x6bc>
 7e9:	a8 07                	test   al,0x7
 7eb:	0f 85 cb fe ff ff    	jne    6bc <.text+0x6bc>
 7f1:	48 89 7a 28          	mov    QWORD PTR [rdx+0x28],rdi
 7f5:	31 db                	xor    ebx,ebx
 7f7:	48 89 72 30          	mov    QWORD PTR [rdx+0x30],rsi
 7fb:	e9 bc fe ff ff       	jmp    6bc <.text+0x6bc>
 800:	81 fb 03 a8 10 40    	cmp    ebx,0x4010a803
 806:	0f 84 40 03 00 00    	je     b4c <.text+0xb4c>
 80c:	81 fb 04 a8 10 40    	cmp    ebx,0x4010a804
 812:	0f 85 4c 04 00 00    	jne    c64 <.text+0xc64>
 818:	48 8d 7c 24 08       	lea    rdi,[rsp+0x8]
 81d:	ba 10 00 00 00       	mov    edx,0x10
 822:	4c 89 e6             	mov    rsi,r12
 825:	48 c7 44 24 08 00 00 00 00 	mov    QWORD PTR [rsp+0x8],0x0
 82e:	48 c7 44 24 10 00 00 00 00 	mov    QWORD PTR [rsp+0x10],0x0
 837:	e8 00 00 00 00       	call   83c <.text+0x83c>	838: R_X86_64_PLT32	_copy_from_user-0x4
 83c:	48 85 c0             	test   rax,rax
 83f:	0f 85 0a 05 00 00    	jne    d4f <.text+0xd4f>
 845:	8b 44 24 08          	mov    eax,DWORD PTR [rsp+0x8]
 849:	83 f8 3f             	cmp    eax,0x3f
 84c:	0f 87 12 04 00 00    	ja     c64 <.text+0xc64>
 852:	8b 54 24 0c          	mov    edx,DWORD PTR [rsp+0xc]
 856:	83 fa 3f             	cmp    edx,0x3f
 859:	0f 87 05 04 00 00    	ja     c64 <.text+0xc64>
 85f:	8b 4c 24 10          	mov    ecx,DWORD PTR [rsp+0x10]
 863:	83 f9 3f             	cmp    ecx,0x3f
 866:	0f 87 f8 03 00 00    	ja     c64 <.text+0xc64>
 86c:	48 c1 e1 04          	shl    rcx,0x4
 870:	48 83 7c 29 30 00    	cmp    QWORD PTR [rcx+rbp*1+0x30],0x0
 876:	0f 85 ea 06 00 00    	jne    f66 <.text+0xf66>
 87c:	48 c1 e0 04          	shl    rax,0x4
 880:	48 01 e8             	add    rax,rbp
 883:	4c 8b 70 30          	mov    r14,QWORD PTR [rax+0x30]
 887:	4d 85 f6             	test   r14,r14
 88a:	0f 84 51 06 00 00    	je     ee1 <.text+0xee1>
 890:	48 c1 e2 04          	shl    rdx,0x4
 894:	48 01 ea             	add    rdx,rbp
 897:	4c 8b 62 30          	mov    r12,QWORD PTR [rdx+0x30]
 89b:	4d 85 e4             	test   r12,r12
 89e:	0f 84 3d 06 00 00    	je     ee1 <.text+0xee1>
 8a4:	81 78 38 37 13 00 00 	cmp    DWORD PTR [rax+0x38],0x1337
 8ab:	0f 85 b3 03 00 00    	jne    c64 <.text+0xc64>
 8b1:	81 7a 38 37 13 00 00 	cmp    DWORD PTR [rdx+0x38],0x1337
 8b8:	0f 85 a6 03 00 00    	jne    c64 <.text+0xc64>
 8be:	48 8b 45 28          	mov    rax,QWORD PTR [rbp+0x28]
 8c2:	49 39 46 20          	cmp    QWORD PTR [r14+0x20],rax
 8c6:	0f 85 8c 03 00 00    	jne    c58 <.text+0xc58>
 8cc:	49 3b 44 24 20       	cmp    rax,QWORD PTR [r12+0x20]
 8d1:	0f 85 81 03 00 00    	jne    c58 <.text+0xc58>
 8d7:	41 8b 46 04          	mov    eax,DWORD PTR [r14+0x4]
 8db:	83 e8 02             	sub    eax,0x2
 8de:	83 e0 fd             	and    eax,0xfffffffd
 8e1:	0f 85 7d 03 00 00    	jne    c64 <.text+0xc64>
 8e7:	41 83 7c 24 04 02    	cmp    DWORD PTR [r12+0x4],0x2
 8ed:	0f 85 71 03 00 00    	jne    c64 <.text+0xc64>
 8f3:	41 f6 46 18 08       	test   BYTE PTR [r14+0x18],0x8
 8f8:	0f 84 5a 03 00 00    	je     c58 <.text+0xc58>
 8fe:	41 f6 44 24 18 08    	test   BYTE PTR [r12+0x18],0x8
 904:	0f 84 4e 03 00 00    	je     c58 <.text+0xc58>
 90a:	48 8b 3d 00 00 00 00 	mov    rdi,QWORD PTR [rip+0x0]        # 911 <.text+0x911>	90d: R_X86_64_PC32	.bss-0x4
 911:	be c0 0d 00 00       	mov    esi,0xdc0
 916:	e8 00 00 00 00       	call   91b <.text+0x91b>	917: R_X86_64_PLT32	kmem_cache_alloc_noprof-0x4
 91b:	48 89 c3             	mov    rbx,rax
 91e:	48 85 c0             	test   rax,rax
 921:	0f 84 50 06 00 00    	je     f77 <.text+0xf77>
 927:	4d 8b 6e 18          	mov    r13,QWORD PTR [r14+0x18]
 92b:	4d 0b 6c 24 18       	or     r13,QWORD PTR [r12+0x18]
 930:	48 8d 7b 10          	lea    rdi,[rbx+0x10]
 934:	48 b8 42 41 00 00 03 00 00 00 	movabs rax,0x300004142
 93e:	48 89 03             	mov    QWORD PTR [rbx],rax
 941:	be 08 00 00 00       	mov    esi,0x8
 946:	c7 43 08 01 00 00 00 	mov    DWORD PTR [rbx+0x8],0x1
 94d:	e8 00 00 00 00       	call   952 <.text+0x952>	94e: R_X86_64_PLT32	get_random_bytes-0x4
 952:	48 8b 43 10          	mov    rax,QWORD PTR [rbx+0x10]
 956:	4c 89 6b 18          	mov    QWORD PTR [rbx+0x18],r13
 95a:	48 0d 03 03 00 00    	or     rax,0x303
 960:	48 89 43 10          	mov    QWORD PTR [rbx+0x10],rax
 964:	41 83 7e 04 04       	cmp    DWORD PTR [r14+0x4],0x4
 969:	0f 84 33 05 00 00    	je     ea2 <.text+0xea2>
 96f:	48 8b 55 28          	mov    rdx,QWORD PTR [rbp+0x28]
 973:	49 8d 74 24 38       	lea    rsi,[r12+0x38]
 978:	48 c1 c0 11          	rol    rax,0x11
 97c:	b9 90 00 00 00       	mov    ecx,0x90
 981:	48 89 53 20          	mov    QWORD PTR [rbx+0x20],rdx
 985:	48 8b 55 20          	mov    rdx,QWORD PTR [rbp+0x20]
 989:	48 31 f2             	xor    rdx,rsi
 98c:	48 31 d0             	xor    rax,rdx
 98f:	48 8d 53 48          	lea    rdx,[rbx+0x48]
 993:	48 89 43 28          	mov    QWORD PTR [rbx+0x28],rax
 997:	49 8b 44 24 30       	mov    rax,QWORD PTR [r12+0x30]
 99c:	48 c7 43 38 00 00 00 00 	mov    QWORD PTR [rbx+0x38],0x0	9a0: R_X86_64_32S	.rodata+0x108
 9a4:	48 89 43 30          	mov    QWORD PTR [rbx+0x30],rax
 9a8:	48 c7 43 40 00 00 00 00 	mov    QWORD PTR [rbx+0x40],0x0	9ac: R_X86_64_32S	init_task
 9b0:	49 8b 44 24 30       	mov    rax,QWORD PTR [r12+0x30]
 9b5:	48 39 c8             	cmp    rax,rcx
 9b8:	48 0f 47 c1          	cmova  rax,rcx
 9bc:	83 f8 08             	cmp    eax,0x8
 9bf:	0f 83 a6 04 00 00    	jae    e6b <.text+0xe6b>
 9c5:	a8 04                	test   al,0x4
 9c7:	0f 85 71 05 00 00    	jne    f3e <.text+0xf3e>
 9cd:	85 c0                	test   eax,eax
 9cf:	0f 84 b0 04 00 00    	je     e85 <.text+0xe85>
 9d5:	41 0f b6 4c 24 38    	movzx  ecx,BYTE PTR [r12+0x38]
 9db:	88 4b 48             	mov    BYTE PTR [rbx+0x48],cl
 9de:	a8 02                	test   al,0x2
 9e0:	0f 84 9f 04 00 00    	je     e85 <.text+0xe85>
 9e6:	89 c0                	mov    eax,eax
 9e8:	0f b7 4c 06 fe       	movzx  ecx,WORD PTR [rsi+rax*1-0x2]
 9ed:	66 89 4c 02 fe       	mov    WORD PTR [rdx+rax*1-0x2],cx
 9f2:	e9 8e 04 00 00       	jmp    e85 <.text+0xe85>
 9f7:	48 8d 7c 24 08       	lea    rdi,[rsp+0x8]
 9fc:	ba 18 00 00 00       	mov    edx,0x18
 a01:	4c 89 e6             	mov    rsi,r12
 a04:	48 c7 44 24 08 00 00 00 00 	mov    QWORD PTR [rsp+0x8],0x0
 a0d:	48 c7 44 24 10 00 00 00 00 	mov    QWORD PTR [rsp+0x10],0x0
 a16:	48 c7 44 24 18 00 00 00 00 	mov    QWORD PTR [rsp+0x18],0x0
 a1f:	48 c7 04 24 00 00 00 00 	mov    QWORD PTR [rsp],0x0
 a27:	e8 00 00 00 00       	call   a2c <.text+0xa2c>	a28: R_X86_64_PLT32	_copy_from_user-0x4
 a2c:	48 85 c0             	test   rax,rax
 a2f:	0f 85 1a 03 00 00    	jne    d4f <.text+0xd4f>
 a35:	8b 44 24 08          	mov    eax,DWORD PTR [rsp+0x8]
 a39:	83 f8 3f             	cmp    eax,0x3f
 a3c:	0f 87 22 02 00 00    	ja     c64 <.text+0xc64>
 a42:	8b 5c 24 0c          	mov    ebx,DWORD PTR [rsp+0xc]
 a46:	8d 53 ff             	lea    edx,[rbx-0x1]
 a49:	83 fa 07             	cmp    edx,0x7
 a4c:	0f 87 12 02 00 00    	ja     c64 <.text+0xc64>
 a52:	48 8b 54 24 10       	mov    rdx,QWORD PTR [rsp+0x10]
 a57:	f6 c2 07             	test   dl,0x7
 a5a:	0f 85 04 02 00 00    	jne    c64 <.text+0xc64>
 a60:	48 c1 e0 04          	shl    rax,0x4
 a64:	48 01 e8             	add    rax,rbp
 a67:	48 8b 48 30          	mov    rcx,QWORD PTR [rax+0x30]
 a6b:	48 85 c9             	test   rcx,rcx
 a6e:	0f 84 6d 04 00 00    	je     ee1 <.text+0xee1>
 a74:	48 8b 75 28          	mov    rsi,QWORD PTR [rbp+0x28]
 a78:	48 39 71 20          	cmp    QWORD PTR [rcx+0x20],rsi
 a7c:	0f 85 d6 01 00 00    	jne    c58 <.text+0xc58>
 a82:	f6 41 18 02          	test   BYTE PTR [rcx+0x18],0x2
 a86:	0f 84 cc 01 00 00    	je     c58 <.text+0xc58>
 a8c:	48 8b 41 10          	mov    rax,QWORD PTR [rcx+0x10]
 a90:	48 8b 79 28          	mov    rdi,QWORD PTR [rcx+0x28]
 a94:	48 33 7d 20          	xor    rdi,QWORD PTR [rbp+0x20]
 a98:	48 8b 49 30          	mov    rcx,QWORD PTR [rcx+0x30]
 a9c:	48 c1 c0 11          	rol    rax,0x11
 aa0:	48 31 c7             	xor    rdi,rax
 aa3:	49 89 fc             	mov    r12,rdi
 aa6:	48 85 ff             	test   rdi,rdi
 aa9:	0f 84 b5 01 00 00    	je     c64 <.text+0xc64>
 aaf:	48 89 d0             	mov    rax,rdx
 ab2:	48 01 d8             	add    rax,rbx
 ab5:	0f 82 a9 01 00 00    	jb     c64 <.text+0xc64>
 abb:	48 39 c1             	cmp    rcx,rax
 abe:	0f 82 a0 01 00 00    	jb     c64 <.text+0xc64>
 ac4:	48 01 fa             	add    rdx,rdi
 ac7:	48 3b 15 00 00 00 00 	cmp    rdx,QWORD PTR [rip+0x0]        # ace <.text+0xace>	aca: R_X86_64_PC32	page_offset_base-0x4
 ace:	0f 82 84 01 00 00    	jb     c58 <.text+0xc58>
 ad4:	f6 c2 07             	test   dl,0x7
 ad7:	0f 85 7b 01 00 00    	jne    c58 <.text+0xc58>
 add:	48 b8 ff ff ff 7f ff ff ff ff 	movabs rax,0xffffffff7fffffff
 ae7:	48 39 d0             	cmp    rax,rdx
 aea:	0f 82 68 01 00 00    	jb     c58 <.text+0xc58>
 af0:	31 d2                	xor    edx,edx
 af2:	4c 8b 74 24 18       	mov    r14,QWORD PTR [rsp+0x18]
 af7:	48 89 de             	mov    rsi,rbx
 afa:	48 89 e7             	mov    rdi,rsp
 afd:	e8 00 00 00 00       	call   b02 <.text+0xb02>	afe: R_X86_64_PLT32	__check_object_size-0x4
 b02:	48 89 da             	mov    rdx,rbx
 b05:	4c 89 f6             	mov    rsi,r14
 b08:	48 89 e7             	mov    rdi,rsp
 b0b:	e8 00 00 00 00       	call   b10 <.text+0xb10>	b0c: R_X86_64_PLT32	_copy_from_user-0x4
 b10:	48 85 c0             	test   rax,rax
 b13:	0f 85 36 02 00 00    	jne    d4f <.text+0xd4f>
 b19:	48 8b 7c 24 10       	mov    rdi,QWORD PTR [rsp+0x10]
 b1e:	8b 54 24 0c          	mov    edx,DWORD PTR [rsp+0xc]
 b22:	48 b8 a5 5a a5 5a a5 5a 5a a5 	movabs rax,0xa55a5aa55aa55aa5
 b2c:	48 31 04 24          	xor    QWORD PTR [rsp],rax
 b30:	4c 01 e7             	add    rdi,r12
 b33:	48 83 fa 08          	cmp    rdx,0x8
 b37:	0f 87 00 00 00 00    	ja     b3d <.text+0xb3d>	b39: R_X86_64_PC32	.text.unlikely+0xb
 b3d:	48 89 e6             	mov    rsi,rsp
 b40:	31 db                	xor    ebx,ebx
 b42:	e8 00 00 00 00       	call   b47 <.text+0xb47>	b43: R_X86_64_PLT32	memcpy-0x4
 b47:	e9 70 fb ff ff       	jmp    6bc <.text+0x6bc>
 b4c:	48 8d 7c 24 08       	lea    rdi,[rsp+0x8]
 b51:	ba 10 00 00 00       	mov    edx,0x10
 b56:	4c 89 e6             	mov    rsi,r12
 b59:	48 c7 44 24 08 00 00 00 00 	mov    QWORD PTR [rsp+0x8],0x0
 b62:	48 c7 44 24 10 00 00 00 00 	mov    QWORD PTR [rsp+0x10],0x0
 b6b:	e8 00 00 00 00       	call   b70 <.text+0xb70>	b6c: R_X86_64_PLT32	_copy_from_user-0x4
 b70:	48 85 c0             	test   rax,rax
 b73:	0f 85 d6 01 00 00    	jne    d4f <.text+0xd4f>
 b79:	8b 44 24 08          	mov    eax,DWORD PTR [rsp+0x8]
 b7d:	83 f8 3f             	cmp    eax,0x3f
 b80:	0f 87 de 00 00 00    	ja     c64 <.text+0xc64>
 b86:	8b 54 24 0c          	mov    edx,DWORD PTR [rsp+0xc]
 b8a:	83 fa 3f             	cmp    edx,0x3f
 b8d:	0f 87 d1 00 00 00    	ja     c64 <.text+0xc64>
 b93:	48 89 d6             	mov    rsi,rdx
 b96:	48 c1 e6 04          	shl    rsi,0x4
 b9a:	48 01 ee             	add    rsi,rbp
 b9d:	48 83 7e 30 00       	cmp    QWORD PTR [rsi+0x30],0x0
 ba2:	0f 85 bc 00 00 00    	jne    c64 <.text+0xc64>
 ba8:	48 c1 e0 04          	shl    rax,0x4
 bac:	48 01 e8             	add    rax,rbp
 baf:	48 8b 48 30          	mov    rcx,QWORD PTR [rax+0x30]
 bb3:	48 85 c9             	test   rcx,rcx
 bb6:	0f 84 a8 00 00 00    	je     c64 <.text+0xc64>
 bbc:	81 78 38 37 13 00 00 	cmp    DWORD PTR [rax+0x38],0x1337
 bc3:	0f 85 9b 00 00 00    	jne    c64 <.text+0xc64>
 bc9:	48 8b 45 28          	mov    rax,QWORD PTR [rbp+0x28]
 bcd:	48 39 41 20          	cmp    QWORD PTR [rcx+0x20],rax
 bd1:	0f 85 81 00 00 00    	jne    c58 <.text+0xc58>
 bd7:	81 39 37 13 00 00    	cmp    DWORD PTR [rcx],0x1337
 bdd:	75 79                	jne    c58 <.text+0xc58>
 bdf:	f6 41 18 04          	test   BYTE PTR [rcx+0x18],0x4
 be3:	74 73                	je     c58 <.text+0xc58>
 be5:	83 79 04 02          	cmp    DWORD PTR [rcx+0x4],0x2
 be9:	75 6d                	jne    c58 <.text+0xc58>
 beb:	48 c1 e2 04          	shl    rdx,0x4
 bef:	48 89 4e 30          	mov    QWORD PTR [rsi+0x30],rcx
 bf3:	48 b8 00 00 00 00 00 00 ad de 	movabs rax,0xdead000000000000
 bfd:	48 c7 44 2a 38 37 13 00 00 	mov    QWORD PTR [rdx+rbp*1+0x38],0x1337
 c06:	48 23 44 24 10       	and    rax,QWORD PTR [rsp+0x10]
 c0b:	0f 84 9e 02 00 00    	je     eaf <.text+0xeaf>
 c11:	c7 46 3c 01 00 00 00 	mov    DWORD PTR [rsi+0x3c],0x1
 c18:	31 db                	xor    ebx,ebx
 c1a:	e9 9d fa ff ff       	jmp    6bc <.text+0x6bc>
 c1f:	48 8d 9d 30 04 00 00 	lea    rbx,[rbp+0x430]
 c26:	4c 8d a5 30 05 00 00 	lea    r12,[rbp+0x530]
 c2d:	48 8b 33             	mov    rsi,QWORD PTR [rbx]
 c30:	48 85 f6             	test   rsi,rsi
 c33:	74 13                	je     c48 <.text+0xc48>
 c35:	48 8b 3d 00 00 00 00 	mov    rdi,QWORD PTR [rip+0x0]        # c3c <.text+0xc3c>	c38: R_X86_64_PC32	.bss-0x4
 c3c:	e8 00 00 00 00       	call   c41 <.text+0xc41>	c3d: R_X86_64_PLT32	kmem_cache_free-0x4
 c41:	48 c7 03 00 00 00 00 	mov    QWORD PTR [rbx],0x0
 c48:	48 83 c3 08          	add    rbx,0x8
 c4c:	49 39 dc             	cmp    r12,rbx
 c4f:	75 dc                	jne    c2d <.text+0xc2d>
 c51:	31 db                	xor    ebx,ebx
 c53:	e9 64 fa ff ff       	jmp    6bc <.text+0x6bc>
 c58:	48 c7 c3 ff ff ff ff 	mov    rbx,0xffffffffffffffff
 c5f:	e9 58 fa ff ff       	jmp    6bc <.text+0x6bc>
 c64:	48 c7 c3 ea ff ff ff 	mov    rbx,0xffffffffffffffea
 c6b:	e9 4c fa ff ff       	jmp    6bc <.text+0x6bc>
 c70:	81 fb 09 a8 28 c0    	cmp    ebx,0xc028a809
 c76:	75 ec                	jne    c64 <.text+0xc64>
 c78:	48 8d 5c 24 08       	lea    rbx,[rsp+0x8]
 c7d:	ba 28 00 00 00       	mov    edx,0x28
 c82:	4c 89 e6             	mov    rsi,r12
 c85:	48 c7 44 24 08 00 00 00 00 	mov    QWORD PTR [rsp+0x8],0x0
 c8e:	48 c7 44 24 10 00 00 00 00 	mov    QWORD PTR [rsp+0x10],0x0
 c97:	48 89 df             	mov    rdi,rbx
 c9a:	48 c7 44 24 18 00 00 00 00 	mov    QWORD PTR [rsp+0x18],0x0
 ca3:	48 c7 44 24 20 00 00 00 00 	mov    QWORD PTR [rsp+0x20],0x0
 cac:	48 c7 44 24 28 00 00 00 00 	mov    QWORD PTR [rsp+0x28],0x0
 cb5:	e8 00 00 00 00       	call   cba <.text+0xcba>	cb6: R_X86_64_PLT32	_copy_from_user-0x4
 cba:	48 85 c0             	test   rax,rax
 cbd:	0f 85 8c 00 00 00    	jne    d4f <.text+0xd4f>
 cc3:	8b 44 24 08          	mov    eax,DWORD PTR [rsp+0x8]
 cc7:	83 f8 3f             	cmp    eax,0x3f
 cca:	77 98                	ja     c64 <.text+0xc64>
 ccc:	48 c1 e0 04          	shl    rax,0x4
 cd0:	48 01 e8             	add    rax,rbp
 cd3:	48 8b 50 30          	mov    rdx,QWORD PTR [rax+0x30]
 cd7:	48 85 d2             	test   rdx,rdx
 cda:	0f 84 01 02 00 00    	je     ee1 <.text+0xee1>
 ce0:	81 78 38 42 41 00 00 	cmp    DWORD PTR [rax+0x38],0x4142
 ce7:	0f 85 f4 01 00 00    	jne    ee1 <.text+0xee1>
 ced:	48 8b 45 28          	mov    rax,QWORD PTR [rbp+0x28]
 cf1:	48 39 42 20          	cmp    QWORD PTR [rdx+0x20],rax
 cf5:	0f 85 5d ff ff ff    	jne    c58 <.text+0xc58>
 cfb:	81 3a 42 41 00 00    	cmp    DWORD PTR [rdx],0x4142
 d01:	0f 85 51 ff ff ff    	jne    c58 <.text+0xc58>
 d07:	48 8b 42 10          	mov    rax,QWORD PTR [rdx+0x10]
 d0b:	48 89 de             	mov    rsi,rbx
 d0e:	4c 89 e7             	mov    rdi,r12
 d11:	48 89 44 24 10       	mov    QWORD PTR [rsp+0x10],rax
 d16:	48 8b 42 28          	mov    rax,QWORD PTR [rdx+0x28]
 d1a:	48 89 44 24 18       	mov    QWORD PTR [rsp+0x18],rax
 d1f:	48 8b 4a 10          	mov    rcx,QWORD PTR [rdx+0x10]
 d23:	48 33 45 20          	xor    rax,QWORD PTR [rbp+0x20]
 d27:	48 c1 c1 11          	rol    rcx,0x11
 d2b:	48 31 c8             	xor    rax,rcx
 d2e:	48 89 44 24 20       	mov    QWORD PTR [rsp+0x20],rax
 d33:	48 8b 42 40          	mov    rax,QWORD PTR [rdx+0x40]
 d37:	ba 28 00 00 00       	mov    edx,0x28
 d3c:	48 89 44 24 28       	mov    QWORD PTR [rsp+0x28],rax
 d41:	e8 00 00 00 00       	call   d46 <.text+0xd46>	d42: R_X86_64_PLT32	_copy_to_user-0x4
 d46:	48 85 c0             	test   rax,rax
 d49:	0f 84 c9 fe ff ff    	je     c18 <.text+0xc18>
 d4f:	48 c7 c3 f2 ff ff ff 	mov    rbx,0xfffffffffffffff2
 d56:	e9 61 f9 ff ff       	jmp    6bc <.text+0x6bc>
 d5b:	4c 89 e6             	mov    rsi,r12
 d5e:	48 89 ef             	mov    rdi,rbp
 d61:	e8 da f2 ff ff       	call   40 <.text+0x40>
 d66:	48 89 c3             	mov    rbx,rax
 d69:	e9 4e f9 ff ff       	jmp    6bc <.text+0x6bc>
 d6e:	4c 89 e6             	mov    rsi,r12
 d71:	48 89 ef             	mov    rdi,rbp
 d74:	e8 97 f4 ff ff       	call   210 <.text+0x210>
 d79:	48 89 c3             	mov    rbx,rax
 d7c:	e9 3b f9 ff ff       	jmp    6bc <.text+0x6bc>
 d81:	48 8d 7c 24 08       	lea    rdi,[rsp+0x8]
 d86:	ba 04 00 00 00       	mov    edx,0x4
 d8b:	4c 89 e6             	mov    rsi,r12
 d8e:	c7 44 24 08 00 00 00 00 	mov    DWORD PTR [rsp+0x8],0x0
 d96:	e8 00 00 00 00       	call   d9b <.text+0xd9b>	d97: R_X86_64_PLT32	_copy_from_user-0x4
 d9b:	48 85 c0             	test   rax,rax
 d9e:	75 af                	jne    d4f <.text+0xd4f>
 da0:	8b 44 24 08          	mov    eax,DWORD PTR [rsp+0x8]
 da4:	83 f8 3f             	cmp    eax,0x3f
 da7:	0f 87 b7 fe ff ff    	ja     c64 <.text+0xc64>
 dad:	41 89 c5             	mov    r13d,eax
 db0:	4c 89 eb             	mov    rbx,r13
 db3:	48 c1 e3 04          	shl    rbx,0x4
 db7:	48 01 eb             	add    rbx,rbp
 dba:	48 8b 43 30          	mov    rax,QWORD PTR [rbx+0x30]
 dbe:	48 85 c0             	test   rax,rax
 dc1:	0f 84 1a 01 00 00    	je     ee1 <.text+0xee1>
 dc7:	81 7b 38 37 13 00 00 	cmp    DWORD PTR [rbx+0x38],0x1337
 dce:	0f 85 0d 01 00 00    	jne    ee1 <.text+0xee1>
 dd4:	48 8b 4d 28          	mov    rcx,QWORD PTR [rbp+0x28]
 dd8:	48 39 48 20          	cmp    QWORD PTR [rax+0x20],rcx
 ddc:	0f 85 76 fe ff ff    	jne    c58 <.text+0xc58>
 de2:	81 38 37 13 00 00    	cmp    DWORD PTR [rax],0x1337
 de8:	0f 85 6a fe ff ff    	jne    c58 <.text+0xc58>
 dee:	f6 40 18 10          	test   BYTE PTR [rax+0x18],0x10
 df2:	0f 84 60 fe ff ff    	je     c58 <.text+0xc58>
 df8:	c7 40 04 04 00 00 00 	mov    DWORD PTR [rax+0x4],0x4
 dff:	4c 8b 63 30          	mov    r12,QWORD PTR [rbx+0x30]
 e03:	4d 85 e4             	test   r12,r12
 e06:	0f 84 0c fe ff ff    	je     c18 <.text+0xc18>
 e0c:	8b 43 3c             	mov    eax,DWORD PTR [rbx+0x3c]
 e0f:	85 c0                	test   eax,eax
 e11:	75 39                	jne    e4c <.text+0xe4c>
 e13:	8b 43 38             	mov    eax,DWORD PTR [rbx+0x38]
 e16:	3d 37 13 00 00       	cmp    eax,0x1337
 e1b:	74 07                	je     e24 <.text+0xe24>
 e1d:	3d 42 41 00 00       	cmp    eax,0x4142
 e22:	75 28                	jne    e4c <.text+0xe4c>
 e24:	49 8d 7c 24 08       	lea    rdi,[r12+0x8]
 e29:	b8 ff ff ff ff       	mov    eax,0xffffffff
 e2e:	f0 41 0f c1 44 24 08 	lock xadd DWORD PTR [r12+0x8],eax
 e35:	83 f8 01             	cmp    eax,0x1
 e38:	0f 84 bb 00 00 00    	je     ef9 <.text+0xef9>
 e3e:	85 c0                	test   eax,eax
 e40:	7f 0a                	jg     e4c <.text+0xe4c>
 e42:	be 03 00 00 00       	mov    esi,0x3
 e47:	e8 00 00 00 00       	call   e4c <.text+0xe4c>	e48: R_X86_64_PLT32	refcount_warn_saturate-0x4
 e4c:	4c 89 e8             	mov    rax,r13
 e4f:	48 c7 43 30 00 00 00 00 	mov    QWORD PTR [rbx+0x30],0x0
 e57:	31 db                	xor    ebx,ebx
 e59:	48 c1 e0 04          	shl    rax,0x4
 e5d:	48 c7 44 28 38 00 00 00 00 	mov    QWORD PTR [rax+rbp*1+0x38],0x0
 e66:	e9 51 f8 ff ff       	jmp    6bc <.text+0x6bc>
 e6b:	89 c1                	mov    ecx,eax
 e6d:	83 e8 01             	sub    eax,0x1
 e70:	48 8b 7c 0e f8       	mov    rdi,QWORD PTR [rsi+rcx*1-0x8]
 e75:	c1 e8 03             	shr    eax,0x3
 e78:	48 89 7c 0a f8       	mov    QWORD PTR [rdx+rcx*1-0x8],rdi
 e7d:	89 c1                	mov    ecx,eax
 e7f:	48 89 d7             	mov    rdi,rdx
 e82:	f3 48 a5             	rep movs QWORD PTR [rdi],QWORD PTR [rsi]
 e85:	8b 44 24 10          	mov    eax,DWORD PTR [rsp+0x10]
 e89:	48 c1 e0 04          	shl    rax,0x4
 e8d:	48 01 e8             	add    rax,rbp
 e90:	48 89 58 30          	mov    QWORD PTR [rax+0x30],rbx
 e94:	31 db                	xor    ebx,ebx
 e96:	c7 40 38 42 41 00 00 	mov    DWORD PTR [rax+0x38],0x4142
 e9d:	e9 1a f8 ff ff       	jmp    6bc <.text+0x6bc>
 ea2:	49 83 cd 20          	or     r13,0x20
 ea6:	4c 89 6b 18          	mov    QWORD PTR [rbx+0x18],r13
 eaa:	e9 c0 fa ff ff       	jmp    96f <.text+0x96f>
 eaf:	48 8d 79 08          	lea    rdi,[rcx+0x8]
 eb3:	b8 01 00 00 00       	mov    eax,0x1
 eb8:	f0 0f c1 41 08       	lock xadd DWORD PTR [rcx+0x8],eax
 ebd:	85 c0                	test   eax,eax
 ebf:	0f 84 90 00 00 00    	je     f55 <.text+0xf55>
 ec5:	8d 50 01             	lea    edx,[rax+0x1]
 ec8:	09 c2                	or     edx,eax
 eca:	0f 89 48 fd ff ff    	jns    c18 <.text+0xc18>
 ed0:	be 01 00 00 00       	mov    esi,0x1
 ed5:	31 db                	xor    ebx,ebx
 ed7:	e8 00 00 00 00       	call   edc <.text+0xedc>	ed8: R_X86_64_PLT32	refcount_warn_saturate-0x4
 edc:	e9 db f7 ff ff       	jmp    6bc <.text+0x6bc>
 ee1:	48 c7 c3 fe ff ff ff 	mov    rbx,0xfffffffffffffffe
 ee8:	e9 cf f7 ff ff       	jmp    6bc <.text+0x6bc>
 eed:	48 c7 c3 ed ff ff ff 	mov    rbx,0xffffffffffffffed
 ef4:	e9 cb f7 ff ff       	jmp    6c4 <.text+0x6c4>
 ef9:	8b 85 30 05 00 00    	mov    eax,DWORD PTR [rbp+0x530]
 eff:	89 c2                	mov    edx,eax
 f01:	83 e2 1f             	and    edx,0x1f
 f04:	48 8b b4 d5 30 04 00 00 	mov    rsi,QWORD PTR [rbp+rdx*8+0x430]
 f0c:	48 85 f6             	test   rsi,rsi
 f0f:	74 17                	je     f28 <.text+0xf28>
 f11:	48 8b 3d 00 00 00 00 	mov    rdi,QWORD PTR [rip+0x0]        # f18 <.text+0xf18>	f14: R_X86_64_PC32	.bss-0x4
 f18:	e8 00 00 00 00       	call   f1d <.text+0xf1d>	f19: R_X86_64_PLT32	kmem_cache_free-0x4
 f1d:	8b 85 30 05 00 00    	mov    eax,DWORD PTR [rbp+0x530]
 f23:	89 c2                	mov    edx,eax
 f25:	83 e2 1f             	and    edx,0x1f
 f28:	83 c0 01             	add    eax,0x1
 f2b:	4c 89 a4 d5 30 04 00 00 	mov    QWORD PTR [rbp+rdx*8+0x430],r12
 f33:	89 85 30 05 00 00    	mov    DWORD PTR [rbp+0x530],eax
 f39:	e9 0e ff ff ff       	jmp    e4c <.text+0xe4c>
 f3e:	41 8b 4c 24 38       	mov    ecx,DWORD PTR [r12+0x38]
 f43:	89 c0                	mov    eax,eax
 f45:	89 4b 48             	mov    DWORD PTR [rbx+0x48],ecx
 f48:	8b 4c 06 fc          	mov    ecx,DWORD PTR [rsi+rax*1-0x4]
 f4c:	89 4c 02 fc          	mov    DWORD PTR [rdx+rax*1-0x4],ecx
 f50:	e9 30 ff ff ff       	jmp    e85 <.text+0xe85>
 f55:	be 02 00 00 00       	mov    esi,0x2
 f5a:	31 db                	xor    ebx,ebx
 f5c:	e8 00 00 00 00       	call   f61 <.text+0xf61>	f5d: R_X86_64_PLT32	refcount_warn_saturate-0x4
 f61:	e9 56 f7 ff ff       	jmp    6bc <.text+0x6bc>
 f66:	48 c7 c3 f0 ff ff ff 	mov    rbx,0xfffffffffffffff0
 f6d:	e9 4a f7 ff ff       	jmp    6bc <.text+0x6bc>
 f72:	e8 00 00 00 00       	call   f77 <.text+0xf77>	f73: R_X86_64_PLT32	__stack_chk_fail-0x4
 f77:	48 c7 c3 f4 ff ff ff 	mov    rbx,0xfffffffffffffff4
 f7e:	e9 39 f7 ff ff       	jmp    6bc <.text+0x6bc>
