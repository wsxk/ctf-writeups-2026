# Grandma's Famous Sparse-QR Scanwich (The One That Unmaps libc)

<p align="center">
  <a href="https://binary.ninja/"><img alt="Binary Ninja" src="https://img.shields.io/badge/Binary%20Ninja-mise%20en%20place-8a2be2"></a>
  <a href="https://github.com/Vector35/binaryninja-mcp"><img alt="Binary Ninja MCP" src="https://img.shields.io/badge/BN%20MCP-line%20cook-8a2be2"></a>
  <img alt="Course" src="https://img.shields.io/badge/course-main%20%2F%20pwn%20%2F%20web-2b6cb0">
  <img alt="Prep time" src="https://img.shields.io/badge/prep-2%20days%20of%20suffering-005f73">
  <img alt="Yield" src="https://img.shields.io/badge/yield-1%20flag-b00020">
</p>

**Category:** Pwn / Web | **Difficulty:** Extra Crispy | **Author:** vurlo | **Flag:** `GPNCTF{sc4nWicH_S74tI0n_sP3C14L_0Rd3R_exTra_5hE1lS}`

> ⭐⭐⭐⭐⭐ "Made this last night and my whole libc disappeared. Five stars, would corrupt allocator metadata again." — *a review I am writing about myself*

<p align="center"><strong><a href="#-the-recipe-card-finally">⏬ JUMP TO RECIPE ⏬</a></strong></p>

---

## A Word Before We Cook (You Knew This Was Coming)

If you have ever searched the internet for a sandwich recipe, you already know the rules of the genre. You typed "grilled cheese" into a search bar like a normal, food-having adult, and what you got back was four thousand words about a woman named Brenda, her trip to a coastal village in 2009, the way the light came through the kitchen window of a rental cottage, and a deeply moving paragraph about *the bread of her childhood* — all before a single instruction about butter. There is a "Jump to Recipe" button, sure, but Brenda knows you won't press it on the first read. Brenda knows you'll scroll. Brenda always wins.

I am Brenda now. This is my villain origin story. Pull up a chair.

This challenge is called **Scanwich Station**, and it is, on the surface, the most innocent little thing on the GPN menu: a cheerful web app that scans QR codes off uploaded images. You bring it a picture of a QR code, it reads the QR code, it tells you what the QR code says. That's the whole pitch. It's the food court of CTF challenges — bright signage, a laminated menu, a teenager in a visor asking if you'd like to make it a combo.

But here's the thing about food courts. Behind every cheerful sneeze-guarded counter there is a *kitchen*, and behind every kitchen there is a walk-in freezer, and somewhere in the back of that walk-in freezer, behind the boxes of frozen fries, there is a 32-bit integer that absolutely should have been 64 bits, quietly leaking cold air into the rest of the building. This writeup is the story of how I found the freezer, pried it open, and let all the cold air out until libc itself caught hypothermia and fell over.

I want to be honest with you, the way Brenda is honest about how this recipe is "a labor of love" (read: it took two days and there was crying). This challenge took **two days**. There were dead ends. There were `__free_hook` rabbit holes that turned out to be empty (more on that betrayal later — it deserves its own paragraph and it's going to get one). There was a glorious moment where I made the binary segfault and felt like a genius, immediately followed by the crushing realization that a segfault is not a flag, it's just a very loud way of accomplishing nothing.

So let's cook. But first, obviously, more backstory, because that is the law.

### The Sandwich That Started It All

Every good recipe blog has a sandwich that *means something*. Mine is the humble principle that **the dangerous part of a program is almost never the part that's trying to look dangerous.** Scanwich Station hands you a QR scanner written in safe, cozy Python with Pillow and pyzbar — a non-stick pan, basically, the kind that physically cannot let you burn anything. You could upload garbage to that thing all day and the worst that happens is it politely says "couldn't read that, chef."

The Python scanner is the dining room. It's where the guests sit. It is *load-bearing decoration*. The real cooking — the part where someone could actually get hurt — happens somewhere else entirely, and the entire challenge is about finding the door to the back.

We'll find the door. Then we'll find the freezer. Then we'll commit several federal allocator crimes. But the door first.

---

## What's In The Box (Ingredients We Were Handed)

The challenge ships as a tarball with both a **web** half and a **pwn** half, which is the CTF equivalent of a meal kit that arrives with both the marinade *and* a live animal. You get:

```text
app/                     # the Flask web app (the dining room)
  app.py
  helpers/image.py       # PNG -> custom frame converter (the prep station)
  helpers/decoder.py     # picks guest vs. kitchen scanner
  helpers/job.py         # the ScanJob dataclass with the hidden field
src/qrscan.c             # the NATIVE scanner (the actual kitchen)
src/read_flag.c          # setuid helper that prints /flag
vendor/quirc/            # the QR library with the bug in it
Dockerfile               # how the meal is plated in prod
docker_dist/             # the exact libc/loader/binary shipped to remote
```

The `Dockerfile` is the nutrition label, and it tells us how this dish actually wants to be eaten:

```dockerfile
RUN echo "$FLAG" > /flag && \
    chown root:root /flag /read_flag && \
    chmod 4555 /read_flag && \
    chmod 000 /flag
```

Read that like an allergy warning. `/flag` is mode `000`, owned by root — you, a humble `ctf` user with uid 1337, cannot read it. But `/read_flag` is **setuid root** (`4555`). It's a little spoon that's allowed to reach into the locked jar. We don't need to read the flag. We need to convince the kitchen to run `/read_flag` for us. That's the whole dish. Everything else is technique.

So the objective crystallizes: **get code execution inside the native scanner, run `/read_flag`, collect flag, write insufferable blog post.** One of those three is already done by the time you read this.

---

## Initial Recon (The Part Where I Read the Menu Twice)

First instinct on anything web-shaped: poke the routes. The Flask app exposes exactly two:

```python
@app.post("/scan")
def scan():
    filename, result = decode_upload(request.files.get("image"), request.form.to_dict())
```

Nothing exciting. Upload an image, it scans it. But look at that second argument — `request.form.to_dict()`. The *entire form* gets handed downstream. That's a recipe blog "Brenda's secret ingredient" if I've ever seen one: the whole form dictionary goes somewhere, and somewhere always wants something.

Following the smell into `decode_upload`, the form dict gets splatted straight into a dataclass:

```python
def prepare_job(upload, values):
    return ScanJob(prepare_upload(upload), **values)   # <- **values, oh no

@dataclass
class ScanJob:
    image: object
    station: str = "guest"
```

There it is. The hidden field. `station` defaults to `"guest"`, but if *you* put a `station` field in your upload form, you set it yourself. And what does `station` control?

```python
if job.station == "kitchen":
    return job.image.name, kitchen_scan(job)     # the native scanner
return job.image.name, guest_scan(job)           # the cozy Python one
```

**`station=kitchen` is the door to the back.** One extra form field and you stop being a guest in the dining room and start being staff in the kitchen, standing next to the deep fryer with no training and a clipboard.

```bash
curl 'https://HOST/scan?raw=1' -F station=kitchen -F image=@ticket.png
```

This is the single most important sentence in the web half of the challenge, and it's *one word in a default dataclass value.* The author hid the entire native attack surface behind a field that looks like leftover scaffolding. Beautiful. Cruel. I respect it enormously.

---

## Prepping the Station (How the Kitchen Eats Its Images)

Here's a fun twist, and it matters a lot later: the kitchen scanner does **not** eat PNGs. The Python prep station (`helpers/image.py`) chops your PNG up and re-plates it into a custom raw format before sliding it across the pass to the C binary:

```text
uint32  width
uint32  height
uint8   pixels[width * height]      # ... and you can stack multiple of these "frames"
```

And the validation on the Python side feels safe:

```python
MAX_DIMENSION = 0x7fffffff
MAX_PIXELS    = 5 * 1024 * 1024 * 1024   # 5 GiB
```

Width and height each capped below 2³¹, total pixels capped at 5 GiB. A reasonable person reads that and thinks "fine, big but bounded." A reasonable person has never met a 32-bit multiply. We'll come back to this — it's the spoiled-milk-at-the-back-of-the-fridge of the whole challenge.

But the *genuinely* clever ingredient is how the converter writes its output:

```python
if row != zero_row:
    out.seek(start + count * width)
    out.write(row)
...
out.seek(start + width * height)
out.truncate(out.tell())            # sparse file: holes cost nothing
```

It **seeks over all-zero rows** instead of writing them. That makes the output a *sparse file* — logically gigabytes, physically a few KB on disk. Pair that with PNG's love of compressing solid-black-and-white images, and you can ship an **8 MB upload** that the kitchen sees as **multiple frames totaling over 4 GB.** This is the loaves-and-fishes miracle of the challenge: a tiny file that multiplies into something enormous the moment it crosses into the kitchen. Keep it in your back pocket. It's the only reason any of this fits under Flask's 16 MB limit.

---

## Reading the Recipe Card Nobody Wanted: `qrscan` Under Binary Ninja

Okay. The native scanner. This is where I stopped being a web person and started being a binary person, and it's where my real kitchen appliance — **[Binary Ninja](https://binary.ninja/)** — gets dragged into the story whether it likes it or not.

The deployed `qrscan` is stripped (`-s` in the build line), which is the author's way of serving you the dish with no menu and no ingredient list. But the build is reproducible — the Dockerfile hands you the exact source and compiler flags — so I rebuilt an **unstripped** twin locally and dropped *that* into Binary Ninja with symbols intact. Now I've got a fully-labeled decompilation of the same dish that's running on remote.

The first thing I wanted from the decompiler was dead simple and absolutely critical: **how wide is the multiply?** The `quirc` library stores `w` and `h` as `int`, and there are a dozen spots that multiply them. The whole exploit lives or dies on whether the compiler does that math in 32 bits or 64. Eyeballing `objdump` and counting `imul` operand sizes by hand is exactly the kind of finicky bookkeeping I will get wrong at 2 AM. So I let Binary Ninja answer it.

In the HLIL for `quirc_end` → `pixels_setup`, the decompiler laid it bare. Hover the multiply, check the IL, and Binary Ninja types it for you:

```c
// Binary Ninja HLIL (rebuilt unstripped twin), lightly trimmed:
int32_t w = q->w;
int32_t h = q->h;
uint32_t numPixels = w * h;          // <-- 32-bit product. NOT size_t.
```

That `uint32_t` is the entire challenge. The decompiler showing me the **width of the result type** — not the source-level `int`, but what the optimized code *actually computes in* — is the moment the freezer door clicked open. If I'd trusted the C source I'd have seen `q->w * q->h` and shrugged. Binary Ninja showed me the compiler had baked it into a 32-bit `imul` whose result silently truncates, and that's a completely different sandwich.

I leaned on the [Binary Ninja MCP plugin](https://github.com/Vector35/binaryninja-mcp) for the rest of the reconnaissance, the same way you'd keep a line cook stationed at the prep counter calling out tickets. Instead of me hand-copying disassembly into a chat window like I'm reading a fax to someone, the model I was pairing with could query the analysis database directly — pull the HLIL for `region_code`, chase xrefs to `q->pixels`, and **dump `struct quirc`'s field offsets straight from the types view** so I didn't have to recompute them by hand:

```text
# offsets the model pulled out of Binary Ninja's type view for `struct quirc`
image                offset 0
pixels               offset 8
w                    offset 16
h                    offset 20
num_regions          offset 24
regions              offset 28
...
sizeof(struct quirc) = 15640
```

Concretely, here's the kind of question I'd fire at the MCP-connected model mid-cook:

> *"In `region_code`, what's the exact index expression into `q->pixels`, and what type is the index computed in?"*

and it would read it back out of the decompiler:

```c
// region_code(), via Binary Ninja HLIL over the MCP plugin
quirc_pixel_t pixel = q->pixels[y * q->w + x];   // y*w computed as 32-bit int -> wraps
```

`y * q->w + x`, computed in 32-bit, **wrapping**. That's the OOB primitive in one line, and I got it without ever leaving the decompiler. The thing I love about a seasoned Binary Ninja setup — types named, IL level dialed in, the MCP server wired to the model — is that it turns "go reverse this function" into "ask a question, get the ground truth back." It's having your *mise en place* prepped: every offset labeled, every xref within arm's reach, no rummaging through a cold `objdump` walk-in hoping the struct layout is on a shelf somewhere. On a challenge whose entire bug is *which integer width the multiply uses*, the tool that tells you the integer width is the tool that solves the challenge.

(There's a fuller, gushier love letter to Binary Ninja at the bottom of this post, in the footnotes, where Brenda keeps her affiliate links. You've been warned.)

---

## The Bug, Explained Like You're Standing in My Kitchen

Right. Decompiler's done its job. Here's the bug in plain English, no jargon, the way I'd explain it to a friend who just wandered in asking why my laptop is making the fan noise.

The QR library measures images with a tape measure that only goes up to about 4 billion (that's 2³², the limit of a 32-bit number). The web app, meanwhile, is happy to hand it an image with up to **5 billion** pixels. So you give the library something bigger than its tape measure can hold, and it does what a too-short tape measure does: it **wraps around to zero and keeps going.** It allocates a giant 4 GB+ buffer correctly (that part uses a real 64-bit size), but then every loop that walks through the image uses the wrapped, tiny, *wrong* measurement.

The practical consequence: the library computes the position of a pixel as `y * width + x`, in 32-bit math, and for the right giant dimensions that arithmetic **wraps past zero and points just *before* the buffer instead of inside it.** It thinks it's coloring in a pixel deep inside a huge image. It's actually reaching backwards, off the front of the buffer, into the memory that lives right before it.

And what lives right before a giant `mmap`'d buffer? The **allocator's bookkeeping header.** glibc stamps a little metadata tag right in front of every big allocation — `prev_size` and `size` — like a sticky label on a takeout container saying how much food is inside. The QR library's wrapped pointer reaches back and lets us **scribble on that label.**

> [!TIP]
> The one-sentence version, the thing to remember if you remember nothing else: **a too-small integer let a QR scanner color outside the lines, and the line it crossed was the allocator's "how big is this chunk" label.**

Now, one cooking note that cost me real time, so you don't have to bleed for it. In `region_code`, the library treats pixel value `1` as "black, please flood-fill me," but any value `≥ 2` as "already labeled, skip." My first crash PoC painted with `0xff` (255) and nothing happened, because 255 ≥ 2, so the library went "already done, next." You have to paint your trigger pattern with the byte `0x01` specifically. It's the difference between "preheat to 1°" and "preheat to 350°" — same dial, wildly different dinner. (Binary Ninja's HLIL for `region_code` is exactly what showed me the `>= QUIRC_PIXEL_REGION` early-return; I'd have been baffled for an hour otherwise.)

---

## From "It Crashes" to "It Cooks" (The Dead Ends, Honestly)

Here is the part of the recipe blog where Brenda admits the first three times she made this, it came out wrong. Because a segfault is not a flag. Making the scanner crash proved the bug was real, and then I sat there holding a crash like a smoke alarm going off, which tells you there's a fire but does not, itself, cook anything.

A few honest dead ends, plated for your education:

- **`__free_hook` / `__malloc_hook`.** The old reliable. Overwrite a glibc function pointer, get a free shell. Except modern glibc *removed these hooks*, and the symbols that remain are inert compatibility ghosts. I set them. I prayed. `free(strdup("echo HOOKED"))` did exactly nothing. This is the CTF equivalent of reaching for grandma's cast-iron pan and finding out it's a non-stick imposter from 2023. A whole evening, gone.
- **Just crash it and hope.** No. DoS is not the dish.
- **Web path traversal to `/flag`.** `/static/../app.py`, `/flag`, the usual. All 404. The dining room has no secret door; the door is in the kitchen.

What actually works is turning that one-byte scribble on the allocator label into a **controlled remapping of libc.** Here's the chain, and it is genuinely one of the more elegant things I've built, so I'm going to enjoy describing it.

### Step 1 — Lie about the chunk size

We use the wrapped pixel write to flip **one byte** of the big buffer's `size` field. The buffer's real size header reads `0x100010002`. We bump a byte so it reads `0x100030002` — we told the takeout label the container is bigger than it is, by exactly `0x20000` bytes.

### Step 2 — Free it, and watch glibc unmap too much

The next frame is a tiny `1×1` image. When the scanner resizes from the giant frame down to this little one, the library **frees the giant buffer.** Because it's an `mmap`'d chunk, glibc honors our lie and calls `munmap` on the *inflated* size — so it doesn't just unmap our buffer, it keeps going and unmaps **the first page of libc that sits right after it.** That page holds libc's `.gnu.hash`, `.dynsym`, `.dynstr` — the dynamic linker's phone book for "where does each function live." We just tore the phone book out of the wall and left a hole.

### Step 3 — Pour a new image into the hole

A third giant frame gets allocated, and because of how the address space now looks, it **lands right in the hole** we just made — overlapping the addresses where libc's phone book used to be. We fill the overlapping region with a **copy of libc's real dynamic metadata**, byte-for-byte, with exactly one edit:

```python
# dynsym[puts].st_value = address of system
data[PUTS_DYNSYM_ENTRY + 8 : PUTS_DYNSYM_ENTRY + 16] = struct.pack('<Q', SYSTEM_ST_VALUE)
```

We rewrote *one phone book entry.* Under "puts," we wrote down "system"'s phone number.

### Step 4 — Ask for "puts," get "system"

The scanner is built with **Partial RELRO + lazy binding**, which means `puts` isn't looked up until the *first time it's called*. And `puts` is only ever called on one occasion:

```c
if (!err)
    puts((char *)data.payload);    // print a successfully-decoded QR payload
```

So we hide a perfectly valid QR code in that third frame — painted in `0x01` pixels so it survives the library's thresholding pass — and its payload is the string:

```text
/read_flag
```

The scanner decodes the QR, goes "great, time to `puts` this payload," asks the dynamic linker "hey, where's `puts`?", and our doctored phone book answers **"`puts` lives at `system`, enjoy."** The call becomes:

```c
system("/read_flag");
```

The setuid spoon reaches into the locked jar. The flag pours out. Chef's kiss.

---

## 📋 The Recipe Card (Finally)

> *Brenda voice:* I know, I know, you scrolled. It's fine. Here's the actual recipe. Full code in [`solve.py`](./solve.py).

**Yield:** 1 flag · **Prep:** ~8 MB PNG · **Cook:** under the 90-second decoder timeout · **Difficulty:** Extra Crispy

### Ingredients

- 1 hidden form field, `station=kitchen` (the whole meal is locked behind this)
- 3 grayscale 8-bit PNG frames, concatenated into one upload
  - **Frame 1** — `26827 × 160101`, the size-corrupting frame (one byte: `0x01 → 0x03` at `image[-6]`)
  - **Frame 2** — `1 × 1`, the trigger that frees Frame 1 and unmaps into libc
  - **Frame 3** — `28622 × 150065`, the carrier: a copy of libc's dynamic metadata with `dynsym[puts].st_value = system`, plus a real QR reading `/read_flag`
- 1 copy of the challenge's exact `libc.so.6` (from `docker_dist/`, so offsets match remote)
- A generous handful of sparse zero-rows (free, makes the 4 GB fit in 8 MB)

### Instructions

1. **Open the kitchen.** Send the upload with `station=kitchen` so the native scanner does the cooking.
2. **Stack three frames in one PNG.** The converter parses PNGs until EOF, so concatenating them gives you a three-course meal in one file.
3. **Frame 1 — salt the chunk header.** Use the 32-bit wrap so a `0x01` pixel write lands on the allocator's `size` byte, inflating it by `0x20000`.
4. **Frame 2 — trigger the free.** The `1×1` resize frees Frame 1; glibc `munmap`s into libc's first page. You now have a libc-shaped hole.
5. **Frame 3 — pour and patch.** The next big allocation fills the hole. Lay down real libc metadata, change only `puts → system`, and paint a `/read_flag` QR in `0x01` ink at offset `(20, 20)` so it survives thresholding.
6. **Serve.** The scanner decodes the QR and "prints" it — which is now `system("/read_flag")`. Flag comes out the pass.

```python
# the whole meal, three frames in one PNG (see solve.py)
write_png(f, W1, H1, stage1_rows())                  # corrupt the size byte
write_png(f, W2, H2, {})                             # 1x1: trigger the free
write_png(f, W3, H3, stage3_rows("/read_flag", libc))# remap libc + QR payload
```

---

## Plating It Up (Running the Exploit)

```bash
# build the exploit PNG and fire it at the rotating remote hostname
./solve.py https://smoked-pineapple-under-smashed-dashi-lrk3.gpn24.ctf.kitctf.de
```

```text
[+] wrote exploit.png (8118271 bytes)
GPNCTF{sc4nWicH_S74tI0n_sP3C14L_0Rd3R_exTra_5hE1lS}
```

An 8 MB picture of three QR-ish smudges walked into a sandwich shop, told the allocator it was bigger than it was, unmapped part of libc, replaced the phone book, and got root to read the flag for it. The scanner printed it thinking it was just being a helpful little QR reader. It never knew it catered the whole heist.

```text
GPNCTF{sc4nWicH_S74tI0n_sP3C14L_0Rd3R_exTra_5hE1lS}
```

---

## ⭐ Reviews (Recipe Notes & Variations)

> ⭐⭐⭐⭐⭐ **DonnaFromAccounting** — *"Made this for the family. My libc disappeared exactly as described. One note: I used `0xff` for the trigger pixels like the recipe warns against and it came out flat — DON'T skip the `0x01`, it really does matter!"*

> ⭐⭐⭐⭐⭐ **pwnmom_1989** — *"The `__free_hook` substitution does NOT work on modern glibc, can confirm, wasted a whole evening. The lazy-binding `puts→system` version is the only one that rises properly."*

> ⭐⭐☆☆☆ **anon** — *"Could you just post the recipe without the whole life story?"* → **Brenda:** *No.*

## Key Takeaways (The "Tips for Next Time" Section)

- **The scaffolding field was the door.** `station=kitchen` lived in a default dataclass value. The whole native attack surface hid behind one word `**values` splatted right past you. Always read the boring plumbing.
- **Integer width is everything.** Python's 5 GiB limit met C's 32-bit multiply, and 5 GiB > 4 GiB by just enough to wrap. The bug wasn't in either half alone — it was in the *seam* between the safe language and the unsafe one.
- **Sparse files + PNG compression = a tiny file that's secretly enormous.** 8 MB on the wire, 4 GB+ in the kitchen. Carrier-image tricks are underrated.
- **One byte of allocator metadata is a lever.** Flip a single `size` byte and `munmap` does the heavy lifting, tearing a libc-shaped hole you can pour a fake phone book into.
- **Lazy binding is a remapping attack waiting to happen.** Partial RELRO means symbol resolution is deferred — replace the linker's metadata before the first call and `puts` becomes `system`. No ROP chain, no stack pivot, just a forged phone book.
- **A crash is not a flag.** Proving the bug exists felt great and accomplished nothing. The work is always the second half: crash → control → execution.

---

## 🍴 Footnotes From the Pass

### A genuine (and yes, affiliate-coded) word about Binary Ninja

Every recipe blog has the section where Brenda tells you which $40 garlic press changed her life. This is mine, and I mean it: **[Binary Ninja](https://binary.ninja/) is the garlic press.** This challenge's entire bug is a question of *integer width* — does the multiply happen in 32 bits or 64? — and that is precisely the kind of question a decompiler answers in one glance and `objdump` makes you earn with a magnifying glass and a prayer.

Three things it actually did for me, concretely:

- **It told me the multiply was 32-bit.** The HLIL typed `q->w * q->h` as `uint32_t`, not `size_t`. The *result type* is the whole exploit, and the decompiler handed it to me without my having to decode operand-size prefixes by hand at 2 AM.
- **The [MCP plugin](https://github.com/Vector35/binaryninja-mcp) made the model a line cook at my prep station.** Instead of copy-pasting disassembly into a chat like I'm reading a recipe over a bad phone line, the LLM read the analysis database *directly* — HLIL, xrefs, and the `struct quirc` field offsets straight out of the types view. When I needed the exact index expression in `region_code`, I asked, and it read `q->pixels[y * q->w + x]` back to me with the wrapping math intact. No telephone game, same cutting board.
- **A seasoned setup is frictionless.** Once the types are named and the IL level is where you like it, getting an answer out of Binary Ninja is *mise en place* — every offset labeled and within reach. On a challenge this fiddly, the tool getting out of the way is most of the win.

If you reverse things and haven't wired up Binary Ninja with the MCP server, consider this me leaning across the table, lowering my voice, and telling you to **get the garlic press.**

### A note on who actually plated this writeup

Full honesty from the kitchen, because pretending otherwise is how restaurants implode: **I cooked the dish; an LLM helped me plate it.**

The exploit is mine — the 32-bit wrap, the one-byte `size` corruption, the `munmap`-into-libc trick, the forged-phone-book `puts→system` swap, every dead end logged in [`analysis.md`](./analysis.md), and all two days of suffering. That's the food. What I brought an LLM in for was *front of house*: turning my pile of byte-level scribbles into something a human can actually read, holding the recipe-blog bit together so the jokes land, and making sure the technical steps stay correct while wearing a Brenda costume. I'm the one yelling about wrapped multiplies in the back; the model is the one who folded the napkins, ordered the courses, and kept the water glasses full so the dense parts don't dehydrate you.

To be precise about the line between back-of-house and front-of-house:

- **Back of house (me):** found the hidden `station` field, reversed `qrscan` in Binary Ninja, identified the 32-bit wrap, built and debugged the three-frame `munmap`/remap chain, captured the flag, and supplied the whole Brenda bit.
- **Front of house (the LLM):** structure, pacing, the recipe-card format, and making sure both the comedy and the allocator surgery are legible to someone who wasn't in the kitchen at 2 AM with me.

If the meal lands, it's because the kitchen *and* the dining room showed up. If you came purely for the recipe, the raw ingredients with no garnish are all in [`solve.py`](./solve.py). Tip your server, and for the love of god, paint your trigger pixels `0x01`.

```text
GPNCTF{sc4nWicH_S74tI0n_sP3C14L_0Rd3R_exTra_5hE1lS}
```
