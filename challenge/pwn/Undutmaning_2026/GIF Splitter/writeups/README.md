# GIF Splitter

| Field      | Value |
|------------|-------|
| Category   | pwn |
| Points     | 100 |
| Solves     | 84 |
| Tags       | medel |

## Description

<div style="text-align: center;">
<img src="/files/images/decoy.gif" width="300" style="border: 1px solid #000000;">
<br>
<br>
		<span class="badge rounded-pill text-bg-primary" style="background:#3a74d3 !important;">pwn</span>
	 <span class="badge rounded-pill text-bg-primary" style="background:#3a74d3 !important;">rev</span>
	<br>
	<br>
</div>

---

Det kan bli lite långtråkigt nere på havsbotten ibland, så forskarna på CASCADA roar sig ofta med att skicka memes till varandra. Det har dock gått lite över styr och för att verksamheten och arbetsmoralen inte ska gå helt på näsan har ledningen tvingats (för att censurera och motverka brainrot) slussa alla mediafiler genom ett system för analys. En av komponenterna för hantering av GIF:ar har visat sig vara exponerad på nätverket.

Harriet har kommit över en läcka för denna server och GIF-bibilioteket som används ser mer eller mindre vibe-kodat ut. Redan en mycket kort fuzzning visar att det finns en bugg i koden. 

Harriet misstänker att det kan finnas användbar information på servern. Filen `/flag.txt`  kan troligen innehålla något intressant. Du kanske kan använda buggen för att hjälpa henne att komma åt informationen.

Du hittar servern här: [https://undutmaning-cascada-gif-splitter.chals.io](https://undutmaning-cascada-gif-splitter.chals.io)

## Files

- [chall.tar.gz](./chall.tar.gz)
- [docker_selfhost.tar.gz](./docker_selfhost.tar.gz)

## Writeup

### Flag

```

```

### Executive Summary


### Vulnerability Analysis


### Exploit Strategy


### Implementation


### Execution & Results


