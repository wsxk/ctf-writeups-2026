# Helm Hell - LACTF 2025 Writeup

**Category:** Reverse Engineering
**Flag:** `lactf{t4k1ng_7h3_h3lm_0f_h31m_73mp14t3s}`

---

## The Challenge

> I was migrating our CTF infrastructure over to Helm charts instead of our artisan hand-crafted Kubernetes manifests we've been using for years, but I think I messed up the templates, and now it always outputs false whenever I try and render the templates ._.. Can you help me figure out how to get it to output true?

We're given a Helm chart (a Kubernetes package format) with some template files. When you run it, it outputs either "true" or "false" based on your input. Our job? Figure out what input makes it say "true".

---

## First Look

Let's see what we're working with:

```
helm-hell/
├── Chart.yaml          # Basic chart metadata
├── values.yaml         # Contains input: ""
└── templates/
    ├── _helpers.tpl    # 652KB of... something
    └── output.yaml     # The output template
```

Wait, **652KB** for a helper template file?! That's suspicious. Normal Helm templates are maybe a few KB at most.

Running the chart with empty input:

```bash
$ helm template . --set input=""
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: output
data:
  result:"false"
```

Yep, it outputs "false". Let's try a random guess:

```bash
$ helm template . --set input="lactf{test}"
...
  result:"false"
```

Still false. Time to dig into that massive `_helpers.tpl` file.

---

## What The Heck Is This?

Opening the helpers file, we're greeted with 12,000+ lines of stuff like this:

```go
{{- define "tideInlet200" -}}
{{- $sea := .sea -}}
{{- $helm := .helm -}}
{{- $cargo := .cargo -}}
{{- $provisions := .provisions -}}
{{- $logbook := .logbook -}}
{{- $gatewayData6832 := 9134 -}}
{{- $controllerStack6830 := printf "%d" $helm -}}
{{- $secretPool6829 := default 0 (index $sea $controllerStack6830) -}}
...
```

After staring at this for a while, patterns start to emerge:

- `$sea` - A dictionary that's being used like memory
- `$helm` - A number that moves around (like a pointer)
- `$provisions` - Our input string!
- `$logbook` - Tracks which input character we're reading
- `$cargo` - The output string being built

This is **Brainfuck implemented in Helm templates**!

For those unfamiliar, Brainfuck is an esoteric programming language with only 8 commands. It uses a "tape" of memory cells and a pointer. The Helm template is simulating this:

| Brainfuck | Helm Template Equivalent |
|-----------|-------------------------|
| `>` | `$helm = add $helm 1` |
| `<` | `$helm = sub $helm 1` |
| `+` | `set $sea ... (mod (add ... 1) 256)` |
| `-` | `set $sea ... (mod (add (sub ... 1) 256) 256)` |
| `[` | `if ne $value 0` + recursive function call |
| `]` | End of recursive function |
| `,` | `index $provisions $logbook` |
| `.` | `$cargo = printf "%s%c" ...` |

So someone compiled a Brainfuck program into Helm templates. Absolutely cursed. I love it.

---

## Understanding the Brainfuck Program

Counting the operations:
- **41 input reads** (`,` operations) - So our flag is 41 characters!
- **9 output operations** (`.` operations) - For "true" or "false"
- **406 increment operations** (`+`)
- **77 decrement operations** (`-`)

The flag format is `lactf{...}`, which is 6 + 1 = 7 fixed characters, leaving 34 unknown characters in the middle.

### The Obfuscation

The code is heavily obfuscated:
1. **Nautical variable names** - Everything is named after sailing terms (`$sea`, `$helm`, `$cargo`, `$anchor`, `$stern`, etc.)
2. **Arithmetic obfuscation** - Instead of `+1`, they do `add 126` then `sub 125`
3. **232 functions** - The loops are implemented as recursive function calls
4. **Random noise** - Lots of dead code and meaningless calculations

### How the Validation Works

After tracing through the code, here's how it checks each character:

1. **Build expected value** - Use increments to build up the ASCII value of the expected character
2. **Read input** - Get the next character from our input
3. **Compare** - Subtract one from the other in a loop
4. **Check result** - If both reach zero, they matched!

The classic Brainfuck comparison pattern is:
```brainfuck
[->-<]  // Subtract cell 1 from cell 0, looping until cell 0 is zero
>       // Move to cell 1
[...]   // If not zero (values didn't match), handle error
```

---

## Extracting the Flag

The key insight is that somewhere in all those increment operations, the expected ASCII values for each flag character are being built up.

After analyzing the code structure, I found that each character validation follows a pattern:
1. Build a counter value through increments
2. Multiply it (using a nested loop)
3. Add some post-loop increments
4. Compare with input

Writing a solver to trace these operations and extract the expected values gave us:

```
Position 0:  'l' (108)
Position 1:  'a' (97)
Position 2:  'c' (99)
Position 3:  't' (116)
Position 4:  'f' (102)
Position 5:  '{' (123)
Position 6:  't' (116)
Position 7:  '4' (52)
Position 8:  'k' (107)
...and so on
```

---

## The Flag

```bash
$ helm template . --set 'input=lactf{t4k1ng_7h3_h3lm_0f_h31m_73mp14t3s}'
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: output
data:
  result:"true"
```

**Flag:** `lactf{t4k1ng_7h3_h3lm_0f_h31m_73mp14t3s}`

Which decodes to: **"taking the helm of helm templates"**

A perfect pun for a challenge about controlling (taking the helm of) Helm templates!

---

## Lessons Learned

1. **Helm templates are Turing complete** - You can implement any computation, including Brainfuck interpreters
2. **Obfuscation through naming** - Nautical themes made everything confusing but oddly thematic
3. **Pattern recognition is key** - Once you recognize the Brainfuck patterns, the structure becomes clear
4. **Don't give up on big files** - 652KB looks scary, but it's just repetitive patterns

---

## Tools Used

- `helm` - To run the templates
- Python - For parsing and analysis
- Lots of `grep` and patience

---

## Final Thoughts

This was a beautifully cursed challenge. The idea of implementing a flag checker as a Brainfuck program, then compiling that to Helm templates, is peak CTF creativity. The nautical theming (`$sea` for memory, `$helm` for the pointer) was a nice touch.

10/10 would reverse engineer templating languages again.

*~ Taking the helm of helm templates, one brainfuck at a time ~*
