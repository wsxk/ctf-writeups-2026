# The Fish - LACTF 2025 Writeup

**Category:** Reverse Engineering
**Points:** 331
**Solves:** 16

## The Challenge

> The fish asks you for the flag. Unfortunately, it can only describe it to you in its own words.

We're given a single Python file called `fish.py`. Running it prompts us for a flag, and then tells us if we're right or wrong. Classic crackme style.

## First Look

Opening the file, we see it's an interpreter for an esoteric programming language called **Fish** (or `><>` - get it? It looks like a fish!). Fish is a 2D stack-based language where the instruction pointer moves around a grid, bouncing off mirrors and executing commands.

The interesting part is this "fisherator" code that processes our input:

```python
fisherator = """r0!&4:*:**+&5:*0l2=?.~~20."W"01&:&1=}@{?.{2*"E"0&:&2%0=?.&3*1+&}}1+{{.&2,:&}@{1=?.{56*0.n;"""
```

And this comparison at the end:

```python
if n == 996566347683429688961961964301023586804079510954147876054559647395459973491017596401595804524870382825132807985366740968983080828765835881807124832265927076916036640789039576345929756821059163439816195513160010797349073195590419779437823883987351911858848638715543148499560927646402894094060736432364692585851367946688748713386570173685483800217158511326927462877856683551550570195482724733002494766595319158951960049962201021071499099433062723722295346927562274516673373002429521459396451578444698733546474629616763677756873373867426542764435331574187942918914671163374771769499428478956051633984434410838284545788689925768605629646947266017951214152725326967051673704710610619169658404581055569343649552237459405389619878622595233883088117550243589990766295123312113223283666311520867475139053092710762637855713671921562262375388239616545168599659887895366565464743090393090917526710854631822434014024:
    self._output("><>? ><>! (Indeed, that is the flag!)")
```

That's a **903-digit number**. Our flag gets transformed into this massive number somehow, and we need to reverse the process.

## Understanding the Encoding

I traced through the Fish code to understand what it does. Here's the algorithm broken down:

### Step 1: Combine Characters

First, it takes all the characters of our flag and combines them into one giant number using base-256:

```
flag = "ABC"
n = ord('A')*256^2 + ord('B')*256 + ord('C')
n = 65*65536 + 66*256 + 67 = 4276803
```

### Step 2: The Collatz-ish Transform

Here's where it gets interesting. The algorithm then applies a **modified Collatz sequence** to this number!

You might have heard of the Collatz Conjecture (also called 3n+1 problem). It goes like this:
- If n is even, divide by 2
- If n is odd, multiply by 3 and add 1
- Repeat until you hit 1

The conjecture says every number eventually reaches 1, but nobody has proven it yet.

The Fish encoding does something similar, but instead of just reaching 1, it **counts the steps** in a clever way:

```python
counter = 1
while n > 1:
    if n % 2 == 0:  # n is even
        counter *= 2
        n = n // 2
    else:           # n is odd
        counter = counter * 2 + 1
        n = (3 * n + 1) // 2
return counter
```

The `counter` encodes the entire "path" the number took through the Collatz sequence. Each bit of the counter tells you whether that step was even (0) or odd (1).

## Reversing the Algorithm

To get the flag back, we need to reverse both steps.

### Reversing the Collatz Counter

Starting from the final counter value and n=1, we work backwards:

```python
def reverse_counter(counter):
    n = 1
    while counter > 1:
        if counter % 2 == 1:
            # Previous step was odd
            # n_prev was odd, n = (3*n_prev + 1) / 2
            # So: n_prev = (2*n - 1) / 3
            n = (2 * n - 1) // 3
            counter = (counter - 1) // 2
        else:
            # Previous step was even
            # n_prev was even, n = n_prev / 2
            # So: n_prev = 2 * n
            n = 2 * n
            counter = counter // 2
    return n
```

### Reversing the Base-256 Encoding

Once we have the big number, converting back to characters is easy:

```python
chars = []
while n > 0:
    chars.append(chr(n % 256))
    n = n // 256
flag = ''.join(reversed(chars))
```

## The Solution

Putting it all together:

```python
target = 996566347683429688961961964301023586804079510954147876054559647395459973491017596401595804524870382825132807985366740968983080828765835881807124832265927076916036640789039576345929756821059163439816195513160010797349073195590419779437823883987351911858848638715543148499560927646402894094060736432364692585851367946688748713386570173685483800217158511326927462877856683551550570195482724733002494766595319158951960049962201021071499099433062723722295346927562274516673373002429521459396451578444698733546474629616763677756873373867426542764435331574187942918914671163374771769499428478956051633984434410838284545788689925768605629646947266017951214152725326967051673704710610619169658404581055569343649552237459405389619878622595233883088117550243589990766295123312113223283666311520867475139053092710762637855713671921562262375388239616545168599659887895366565464743090393090917526710854631822434014024

# Reverse the Collatz counter
n = reverse_counter(target)

# Convert to ASCII
chars = []
while n > 0:
    chars.append(chr(n % 256))
    n = n // 256
flag = ''.join(reversed(chars))

print(flag)
```

## The Flag

```
lactf{7h3r3_m4y_83_50m3_155u35_w17h_7h15_1f_7h3_c011472_c0nj3c7ur3_15_d15pr0v3n}
```

Translated from l33tspeak:

> **"there may be some issues with this if the collatz conjecture is disproven"**

What a perfect flag! The entire encoding scheme relies on the Collatz sequence being reversible, which only works if every number eventually reaches 1. If someone ever finds a counterexample to the Collatz Conjecture, this encoding would break!

## Key Takeaways

- **Fish (><>)** is a fun 2D esoteric language worth checking out
- The **Collatz Conjecture** makes for a creative encoding scheme
- When reversing algorithms, trace through simple examples first to understand the pattern
- A 903-digit number isn't as scary as it looks when you understand what produced it

Great challenge that combines esoteric programming languages with number theory!
