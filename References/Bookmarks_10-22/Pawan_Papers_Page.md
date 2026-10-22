# papers · pawan (papers implemented / papers loved)

- **Source:** https://cintu07.github.io/papers/
- **Bookmarked:** 2026-10-05 (Chrome, Bookmarks bar > RDMA > 10-22)
- **Retrieved:** 2026-10-22
- **Linked PDFs saved:** `Engler_Bugs_as_Deviant_Behavior_SOSP01.pdf`, `Era_of_1-bit_LLMs_2402.17764.pdf`, `Equality_Saturation_1012.1802.pdf`

---

# papers i implement

the ones i read with an editor open. each links to the code.

## [Bugs as Deviant Behavior: A General Approach to Inferring Errors in Systems Code](https://web.stanford.edu/~engler/deviant-sosp-01.pdf)

Dawson Engler, David Yu Chen, Seth Hallem, Andy Chou, Benjamin Chelf, SOSP 2001

code says what it believes by repeating it. heresy counts how often a rule holds across a go codebase and flags the sites that break one kept hundreds of times. lock release and nil checks so far, run on 16 big repos.

## [The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits](https://arxiv.org/abs/2402.17764)

Shuming Ma et al., arXiv 2024

the paper shows ternary weights lose little accuracy. the kernel side is where the published work thins out, so ciot is that part: a ternary matvec on arm neon with no multiplies, checked bit for bit against a scalar reference.

# papers i love

not mine, just the ones i keep going back to.

## [Equality Saturation: A New Approach to Optimization](https://arxiv.org/abs/1012.1802)

Ross Tate, Michael Stepp, Zachary Tatlock, Sorin Lerner, Logical Methods in Computer Science, 2011

a compiler usually rewrites the program pass by pass, and every pass throws away the version before it, so the order of the passes decides what you end up with. this paper keeps every equal version at once in one graph, and picks the best one at the end. no pass order to get wrong. it is the idea under e-graphs and egg.