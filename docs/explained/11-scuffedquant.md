# 11. scuffedQuant: rotate, quantize, sketch the residual

[← back to the README section](../../README.md#11-scuffedquant-rotate-quantize-sketch-the-residual)

![scuffedQuant](../media/11_scuffedquant.gif)

scuffedQuant compresses each K or V vector for the cold path. This page goes through every step with a proof of the property it relies on:

- the rotation preserves length and inner products, and makes coordinates behave alike;
- the codebook is the best possible for that coordinate distribution;
- the sign sketch gives an unbiased correction to inner products, and its error shrinks with more bits;
- the wire format is exactly 64 bytes per vector at head_dim 64.

It also says where the code departs from the textbook version (random ±1 projections instead of Gaussian ones) and what that costs.

Code: `middleware/rdma_tensor_cache/scuffed_quant.py`. Tests: `tests/test_scuffed_quant.py`. Notebook 05.

---

## 0. Notation

- $`x \in \mathbb R^d`$: one key or value vector; $`d`$ = head_dim (64 for Granite 3.3-2B), padded to a power of two if needed.
- $`q`$: a query vector. Attention needs $`\langle q, k\rangle`$ for every key $`k`$, not $`k`$ itself.
- $`b`$: bits per coordinate (3). $`m`$: number of sketch bits (256).

## 1. Normalize

Store $`\lVert x\rVert`$ (fp32, 4 bytes) and continue with $`u = x/\lVert x\rVert`$, so $`\lVert u\rVert = 1`$. Every later step works on unit vectors, and the norm is multiplied back at the end. This costs 4 bytes and makes the codebook independent of the vector's scale.

## 2. Randomized Hadamard rotation

The Hadamard matrix $`H_d`$ ($`d`$ a power of two) has entries $`\pm 1`$ and is built recursively, $`H_1 = [1]`$, $`H_{2n} = \begin{pmatrix} H_n & H_n \\ H_n & -H_n\end{pmatrix}`$. $`D`$ is diagonal with random signs $`D_{jj} \in \{\pm1\}`$, fixed by a seed. The rotation is

```math
y = \tfrac{1}{\sqrt d}\, H_d\, D\, u .
```

The code applies it with the fast Walsh–Hadamard transform in $`O(d \log d)`$ (`_walsh_hadamard`, `_rotate`).

### Lemma 2.1: the rotation is orthogonal

$`H_d H_d^\top = d I`$. Proof by induction: true for $`d = 1`$; if $`H_n H_n^\top = nI`$, then

```math
H_{2n}H_{2n}^\top = \begin{pmatrix} H_nH_n^\top + H_nH_n^\top & H_nH_n^\top - H_nH_n^\top \\ H_nH_n^\top - H_nH_n^\top & H_nH_n^\top + H_nH_n^\top \end{pmatrix} = \begin{pmatrix} 2nI & 0 \\ 0 & 2nI\end{pmatrix}.
```

$`D D^\top = I`$ because $`D_{jj}^2 = 1`$. So $`R = \frac1{\sqrt d}HD`$ satisfies $`RR^\top = \frac1d H D D^\top H^\top = I`$. $`\square`$

**Consequences.** $`\lVert Ru\rVert = \lVert u\rVert = 1`$ and $`\langle Ra, Rb\rangle = \langle a, b\rangle`$ for all $`a, b`$. The rotation loses nothing and changes no inner product. It is undone exactly by $`R^\top`$ (the code's `_unrotate`: Hadamard is its own inverse up to scale, then the signs again).

### Lemma 2.2: every rotated coordinate has mean 0 and variance $`1/d`$

Fix $`u`$ and let the signs $`D_{jj}`$ be independent and uniform on $`\{\pm 1\}`$. Then

```math
y_i = \tfrac1{\sqrt d}\sum_j H_{ij} D_{jj} u_j .
```

$`\mathbb E[y_i] = \frac1{\sqrt d}\sum_j H_{ij} u_j\,\mathbb E[D_{jj}] = 0`$. Since $`\mathbb E[D_{jj}D_{kk}] = \mathbb 1[j=k]`$ and $`H_{ij}^2 = 1`$,

```math
\mathbb E[y_i^2] = \frac1d \sum_{j,k} H_{ij}H_{ik}u_ju_k\,\mathbb E[D_{jj}D_{kk}] = \frac1d\sum_j u_j^2 = \frac1d. \qquad\square
```

So whatever the input looks like (a few huge coordinates, say), after rotation every coordinate has the same mean and spread. $`y_i`$ is a sum of $`d`$ independent terms $`\pm H_{ij}u_j/\sqrt d`$; when no single $`u_j`$ dominates, the central limit theorem (Lindeberg form) makes it close to Gaussian, $`y_i \approx \mathcal N(0, 1/d)`$. If $`u`$ is concentrated on one coordinate the CLT does not apply to a single draw; but then the rotation spreads that one coordinate evenly over all $`d`$ outputs with magnitude $`1/\sqrt d`$, which is also easy to quantize.

This is why the outliers in the animation flatten out: one codebook now fits every coordinate.

## 3. Lloyd–Max scalar quantizer (3 bits)

Each rotated coordinate is replaced by the nearest of $`2^b = 8`$ levels $`c_1 < \dots < c_8`$, and only the 3-bit index is sent.

### What "best" means and the two optimality conditions

For a random coordinate $`Y`$ with density $`f`$, choose levels $`c_k`$ and decision boundaries $`t_0 = -\infty < t_1 < \dots < t_7 < t_8 = \infty`$ to minimize the mean squared error

```math
D = \sum_{k=1}^{8} \int_{t_{k-1}}^{t_k} (y - c_k)^2 f(y)\, dy .
```

**Condition 1 (nearest level).** For fixed levels, each $`y`$ should map to the closest $`c_k`$; otherwise moving it to a closer level lowers its error and $`D`$. So each boundary sits halfway between neighbours: $`t_k = (c_k + c_{k+1})/2`$.

**Condition 2 (centroid).** For fixed regions, $`D`$ is a sum of independent quadratics in each $`c_k`$. Setting the derivative to zero,

```math
\frac{\partial D}{\partial c_k} = -2\int_{t_{k-1}}^{t_k}(y - c_k)f(y)\,dy = 0 \;\Longrightarrow\; c_k = \frac{\int_{t_{k-1}}^{t_k} y f(y)\,dy}{\int_{t_{k-1}}^{t_k} f(y)\,dy} = \mathbb E[Y \mid t_{k-1} < Y \le t_k].
```

The second derivative is $`2\Pr(t_{k-1} < Y \le t_k) \ge 0`$, so this is a minimum.

**Lloyd's iteration** alternates the two conditions. Each half-step can only lower $`D`$ (each one solves its sub-problem exactly), and $`D \ge 0`$, so the sequence of $`D`$ values is non-increasing and bounded below: it converges. (It converges to a point satisfying both conditions. For a log-concave density such as the Gaussian that point is the global optimum, a result due to Fleischer, 1964.)

### What the code fits

`_build_codebook` draws 200,000 random unit vectors in $`\mathbb R^d`$, takes their first coordinate as samples of $`Y`$ (whose exact distribution has mean 0 and variance $`1/d`$, like Lemma 2.2), and runs Lloyd's iteration on those samples. Multiplied by $`\sqrt d`$ the fitted levels are about $`\pm 0.25, \pm 0.75, \pm 1.33, \pm 2.1`$, close to the classical 3-bit Lloyd–Max levels for $`\mathcal N(0,1)`$ ($`\pm 0.245, \pm 0.756, \pm 1.344, \pm 2.152`$; Max, 1960). The codebook is computed once and shared by every vector.

The quantized rotated vector $`\hat y`$ is rotated back and rescaled: $`\hat x = \lVert x\rVert\, R^\top \hat y`$. The **residual** is $`r = x - \hat x`$. By Lemma 2.1 its length equals the quantization error in the rotated space: $`\lVert r\rVert = \lVert x\rVert\,\lVert y - \hat y\rVert`$.

## 4. QJL: a one-bit sketch of the residual

The residual is too expensive to send exactly, but attention only needs $`\langle q, r\rangle`$ to correct $`\langle q, \hat x\rangle`$. The sketch stores $`\lVert r\rVert`$ (fp32, 4 bytes) and $`m = 256`$ sign bits

```math
z_j = \mathrm{sign}\big(\langle s_j, r/\lVert r\rVert\rangle\big), \qquad j = 1..m,
```

where $`s_j`$ are fixed random vectors (rows of $`S`$).

### Lemma 4.1 (the sign–Gaussian identity)

If $`(X, Y)`$ are jointly Gaussian with mean 0, $`\mathrm{Var}X = \sigma_X^2`$ and $`\mathrm{Cov}(X,Y) = \sigma_{XY}`$, then

```math
\mathbb E[\mathrm{sign}(X)\,Y] = \sqrt{\tfrac{2}{\pi}}\;\frac{\sigma_{XY}}{\sigma_X}.
```

**Proof.** Write $`Y = aX + W`$ with $`a = \sigma_{XY}/\sigma_X^2`$ and $`W`$ independent of $`X`$ with mean 0 (the Gaussian regression decomposition). Then $`\mathbb E[\mathrm{sign}(X) W] = \mathbb E[\mathrm{sign}X]\,\mathbb E[W] = 0`$ and

```math
\mathbb E[\mathrm{sign}(X)\,Y] = a\,\mathbb E[\mathrm{sign}(X)X] = a\,\mathbb E|X| = a\,\sigma_X\sqrt{2/\pi},
```

using $`\mathbb E|X| = \sigma_X\sqrt{2/\pi}`$ for $`X \sim \mathcal N(0,\sigma_X^2)`$: $`\int_{-\infty}^{\infty}|x|\frac{e^{-x^2/2\sigma^2}}{\sqrt{2\pi}\sigma}dx = \frac{2}{\sqrt{2\pi}\sigma}\int_0^\infty x e^{-x^2/2\sigma^2}dx = \frac{2\sigma^2}{\sqrt{2\pi}\sigma} = \sigma\sqrt{2/\pi}`$. Substituting $`a`$ gives the claim. $`\square`$

### Proposition 4.2: the correction is unbiased (Gaussian projections)

Let $`s_j \sim \mathcal N(0, I_d)`$ independently and $`\bar r = r/\lVert r\rVert`$. For fixed $`q`$, $`X_j = \langle s_j, \bar r\rangle`$ and $`Y_j = \langle s_j, q\rangle`$ are jointly Gaussian with $`\mathrm{Var}X_j = \lVert\bar r\rVert^2 = 1`$ and $`\mathrm{Cov}(X_j, Y_j) = \langle\bar r, q\rangle`$. By Lemma 4.1, $`\mathbb E[z_j Y_j] = \sqrt{2/\pi}\,\langle\bar r, q\rangle`$. So the estimator

```math
\widehat{\langle q, r\rangle} = \lVert r\rVert\,\frac{\sqrt{\pi/2}}{m}\sum_{j=1}^m z_j\,\langle s_j, q\rangle
```

has expectation $`\lVert r\rVert\,\langle\bar r, q\rangle = \langle q, r\rangle`$: unbiased. $`\square`$

### Proposition 4.3: the error shrinks like $`1/\sqrt m`$

The terms $`z_jY_j`$ are independent and identically distributed with $`\mathbb E[(z_jY_j)^2] = \mathbb E[Y_j^2] = \lVert q\rVert^2`$ (because $`z_j^2 = 1`$). So

```math
\mathrm{Var}\big(\widehat{\langle q, r\rangle}\big) = \lVert r\rVert^2\frac{\pi}{2}\frac{1}{m}\mathrm{Var}(z_1Y_1) \le \frac{\pi}{2m}\,\lVert r\rVert^2\,\lVert q\rVert^2 .
```

The standard deviation is at most $`\sqrt{\pi/2m}\,\lVert r\rVert\lVert q\rVert`$. Two things make it small: $`\lVert r\rVert`$ is only the quantization error (small after a good codebook), and $`m = 256`$ gives $`\sqrt{\pi/512} \approx 0.078`$. $`\square`$

### The full estimate

```math
\langle q, k\rangle = \langle q, \hat k\rangle + \langle q, r\rangle \approx \langle q, \hat k\rangle + \lVert r\rVert\,\frac{\sqrt{\pi/2}}{m}\sum_{j=1}^m \mathrm{sign}(S r)_j\,(S q)_j .
```

This is `attention_scores` = reconstruction term + `_qjl_correct`.

### Where the code differs: ±1 projections

The code uses $`S`$ with independent random $`\pm 1`$ entries, not Gaussian ones (cheaper, and matches the Hadamard spirit). What still holds exactly: $`\mathrm{Var}X_j = \lVert\bar r\rVert^2 = 1`$ and $`\mathrm{Cov}(X_j,Y_j) = \langle\bar r, q\rangle`$, because $`\mathbb E[S_{ja}S_{jb}] = \mathbb 1[a=b]`$. What becomes approximate: $`(X_j, Y_j)`$ is a sum of $`d = 64`$ independent terms, so it is only approximately jointly Gaussian, and Lemma 4.1 holds approximately. The estimator is therefore approximately unbiased, with a bias that vanishes as $`d`$ grows. The variance bound in 4.3 does not need Gaussianity and still holds. If the bias ever shows up in the overlap numbers, switching `S` to Gaussian is a one-line change.

## 5. Wire format: exactly 64 bytes per vector at head_dim 64

`CompressedKV.packed_bytes()` for $`n`$ vectors is

```math
\underbrace{20}_{\text{header}} + \underbrace{4n}_{\lVert x\rVert} + \underbrace{4n}_{\lVert r\rVert} + \underbrace{\lceil n\,d\,b/8\rceil}_{\text{indices}} + \underbrace{\lceil n\,m/8\rceil}_{\text{signs}} .
```

Per vector with $`d = 64`$, $`b = 3`$, $`m = 256`$: $`4 + 4 + 64\cdot3/8 + 256/8 = 4 + 4 + 24 + 32 = 64`$ bytes, plus a 20-byte header shared by the whole batch. FP16 is $`64 \times 2 = 128`$ bytes, so the ratio is $`2\times`$. FP32 is 256 bytes, so $`4\times`$ against FP32. The earlier "4× vs FP16" compared against FP32 by mistake.

## 6. What the measurements say

- Granite 3.3-2B, 40 layers, FP32 KV: top-8 attention overlap (do the 8 highest-scoring keys under the estimate match the exact top 8?) is **91.1% ± 3.3%**, minimum 82.8% (`benchmarks/results/scuffed_quant_llm.json`).
- This is a ranking metric. It does not by itself say how generation quality changes; that needs an end-to-end run with the scuffedQuant codec in the connector (notebook 08 has the switch).

## 7. Status

| Claim | Status |
|---|---|
| Rotation preserves norms and inner products | proven (Lemma 2.1) |
| Rotated coordinates have mean 0, variance $`1/d`$ | proven (Lemma 2.2); Gaussian shape is a CLT approximation |
| Codebook satisfies the Lloyd–Max conditions | derived; fitted numerically in code |
| Sketch correction is unbiased | proven for Gaussian $`S`$; approximate for the ±1 $`S`$ the code uses |
| Error decreases as $`1/\sqrt m`$ | proven (Proposition 4.3) |
| 64 bytes per vector, 2× vs FP16 | arithmetic from the packing code; tested |
| Top-8 overlap 91.1% ± 3.3% | measured |

## References

1. A. Zandieh, M. Daliri, I. Han. "QJL: 1-Bit Quantized JL Transform for KV Cache Quantization with Zero Overhead." *Proc. AAAI Conference on Artificial Intelligence*, 2025. [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/34773), [arXiv:2406.03482](https://arxiv.org/abs/2406.03482). *Used for: the sign sketch and its unbiased estimator (§4).*
2. A. Zandieh et al. "TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate." [arXiv:2504.19874](https://arxiv.org/abs/2504.19874), 2025. *Used for: rotate-then-quantize with a residual sketch (§2–§4).*
3. N. Ailon, B. Chazelle. "The Fast Johnson–Lindenstrauss Transform and Approximate Nearest Neighbors." *SIAM Journal on Computing* 39(1):302–322, 2009. [PDF](https://www.cs.princeton.edu/~chazelle/pubs/FJLT-sicomp09.pdf). *Used for: randomized Hadamard rotations spread a vector's mass (§2).*
4. S. P. Lloyd. "Least squares quantization in PCM." *IEEE Transactions on Information Theory* 28(2):129–137, 1982 (Bell Labs memo, 1957). [PDF](https://www.stat.cmu.edu/~rnugent/PCMI2016/papers/LloydKMeans.pdf). *Used for: the alternating optimality conditions (§3).*
5. J. Max. "Quantizing for minimum distortion." *IRE Transactions on Information Theory* 6(1):7–12, 1960. [PDF](https://cs.nyu.edu/home/people/in_memoriam/roweis/csc2515-2006/readings/max60.pdf). *Used for: the 3-bit Gaussian levels quoted in §3.*
6. P. E. Fleischer. "Sufficient conditions for achieving minimum distortion in a quantizer." *IEEE International Convention Record*, Part 1, pp. 104–111, 1964. *Used for: global optimality for log-concave densities (§3).*
7. M. S. Charikar. "Similarity estimation techniques from rounding algorithms." *Proc. 34th ACM STOC*, 2002. [doi:10.1145/509907.509965](https://doi.org/10.1145/509907.509965). *Background: sign random projections preserve angles.*
8. `middleware/rdma_tensor_cache/scuffed_quant.py`, `tests/test_scuffed_quant.py`, `benchmarks/results/scuffed_quant_llm.json` (top-8 overlap in §6).
