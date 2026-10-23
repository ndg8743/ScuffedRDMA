# 8. WFA classifier: static thresholds vs learned weights

[← back to the README section](../../README.md#8-wfa-classifier-static-thresholds-vs-learned-weights)

![WFA classifier](../media/08_wfa.gif)

The classifier decides, per transfer, whether it goes to the hot endpoint or the cold one. This page states both versions precisely, proves why the static one sends decode traffic cold, derives the learned model's training gradient, proves its training problem has a single optimum, and says exactly what the synthetic evaluation does and does not show.

Code: `middleware/rdma_tensor_cache/wfa_classifier.py` (static), `middleware/rdma_tensor_cache/wfa_learner.py` (learned, synthetic traces, evaluation), `middleware/telemetry.py` (`SignalVector`). Notebook 04.

---

## 1. Objects

A **transfer** is described by a `SignalVector` $x$. Its features are

| feature | meaning |
|---|---|
| $\log_2(\text{size})$ | transfer size in bytes, on a log scale |
| access frequency | how often this tensor id has been seen |
| queue depth | outstanding work on the endpoint when it was posted |
| is_prefill, is_decode | phase indicators (0/1) |
| $\log_2(\text{seq len})$ | sequence length of the request |
| $\log_2(\text{inter-arrival})$ | microseconds since the previous transfer |
| is_control | 1 for token ids and scheduler metadata |

Every tensor id carries a small automaton with three **states**: cold, warm, hot. A state is updated each time that tensor is transferred, and the state decides the route: hot goes to the hot endpoint, warm and cold go to the cold endpoint.

"Weighted finite automaton" here means: the next state depends on the current state and the input, through weights.

## 2. The static classifier

`WFAClassifier` uses fixed rules (defaults in brackets):

1. size $< h$ [4096 B] → hot; size $> c$ [256 KiB] → cold;
2. in between: hot if this tensor id has been seen at least $k$ [10] times, else cold;
3. **phase adjustment.** A phase detector looks at the last $w$ [8] layer indices:
   - all consecutive differences equal 1 (a sweep $\ell, \ell+1, \ell+2, \dots$) → PREFILL;
   - else the last three indices equal → DECODE;
   - else UNKNOWN.

   In PREFILL a hot decision is kept only for sizes $\le h/2$. In DECODE a cold mid-size decision becomes hot after $k/2$ accesses.

### Proposition 1: the phase detector never reports DECODE for layer-by-layer decode traffic

**Claim.** Suppose each decode step produces one KV transfer per layer, visiting layers $0, 1, \dots, L-1$ in order, with $L \ge 2$. Then the detector never outputs DECODE. Inside a step it outputs PREFILL; around the wrap from $L-1$ to $0$ it outputs UNKNOWN.

**Proof.** DECODE requires the last three layer indices to be equal. Within a step consecutive indices differ by $+1$. At the boundary between steps the difference is $0 - (L-1) = -(L-1) \ne 0$. So two consecutive indices are never equal, and in particular three never are. A window lying inside one step has all differences equal to 1, which is the PREFILL condition. A window that contains the wrap has one difference $-(L-1) \ne 1$, so it is neither PREFILL nor DECODE, hence UNKNOWN. $\square$

The assumption is not artificial: vLLM's forward pass calls `save_kv_layer` once per attention layer in order, so a connector sees exactly this pattern.

### Corollary: most decode KV deltas are routed cold

A decode KV delta of $b$ new tokens is $b \times 2 h_{kv} d \times 2$ bytes per layer. For the synthetic model (8 KV heads, head_dim 128) and $b \in [1, 64]$ that is 4 KiB to 256 KiB: the middle band. In the middle band the decision is hot only after $k = 10$ accesses. The DECODE boost (hot after $k/2$) never applies, by Proposition 1. In PREFILL, a hot decision would additionally need size $\le 2$ KiB, which these never are. So a decode delta is hot only once its tensor id has been seen 10 times. Until then, it goes cold.

**Measured on synthetic traces** (decode-only mix, 32 layers, 4,000 events; `SyntheticTraceGenerator(seed=5)`):

- the detector reported PREFILL for 2,903 decode KV transfers, UNKNOWN for 976, DECODE for none;
- of 3,849 decode KV transfers the oracle labels hot, 3,295 (86%) were routed cold.

The counts are from synthetic traces. The mechanism (Proposition 1) holds for any trace that visits layers in order.

## 3. The learned WFA

### Model

Let $\varphi(x) \in \mathbb R^F$ be the feature vector, standardized with the training mean and standard deviation, plus a constant 1 (bias), plus two interaction terms:

$$\varphi(x) = \big(z(x),\; 1,\; \log_2 \text{size}\cdot\text{is\_prefill},\; \log_2 \text{size}\cdot\text{is\_decode}\big).$$

(The interactions are standardized together with the rest.) For each current state $s$ and next state $s'$ there is a weight vector $W_{s,s'} \in \mathbb R^F$. The probability of moving to $s'$ is a softmax over the three scores:

$$P(s' \mid s, x) = \frac{\exp\big(W_{s,s'}\cdot \varphi(x)\big)}{\sum_{r \in \{\text{cold, warm, hot}\}} \exp\big(W_{s,r}\cdot\varphi(x)\big)}.$$

At run time the automaton moves to the most probable next state, and the route follows the state.

### Training objective

Training data is a list of transfers $x_n$, each with a label $y_n \in \{\text{cold, warm, hot}\}$ (from the oracle for synthetic traces, or from measured latency for real ones). The previous state $s_n$ is taken from the previous **label** of the same tensor id, not from the model's own prediction ("teacher forcing"). The loss is average cross-entropy plus an L2 penalty:

$$\mathcal L(W) = -\frac1N \sum_{n=1}^N \log P(y_n \mid s_n, x_n) \;+\; \frac{\lambda}{2}\,\lVert W\rVert^2 .$$

### Gradient

Write $z_{n,r} = W_{s_n,r}\cdot \varphi_n$ for the score of next state $r$, and $P_{n,r}$ for its softmax probability. For one example, $-\log P(y_n) = -z_{n,y_n} + \log\sum_r e^{z_{n,r}}$. Differentiating with respect to $z_{n,r}$:

$$\frac{\partial}{\partial z_{n,r}}\Big(-z_{n,y_n} + \log \sum_{r'} e^{z_{n,r'}}\Big) = -\mathbb 1[r = y_n] + \frac{e^{z_{n,r}}}{\sum_{r'} e^{z_{n,r'}}} = P_{n,r} - \mathbb 1[r = y_n].$$

Since $z_{n,r}$ depends on $W_{s,r}$ only when $s = s_n$, and then $\partial z_{n,r}/\partial W_{s,r} = \varphi_n$, the chain rule gives

$$\frac{\partial \mathcal L}{\partial W_{s,r}} = \frac1N \sum_{n:\, s_n = s} \big(P_{n,r} - \mathbb 1[r = y_n]\big)\,\varphi_n \;+\; \lambda W_{s,r}.$$

This is exactly what `LearnedWFA.fit` computes (`G = (P - Y)/n`, `grad[s] = G[idx].T @ X[idx]`, `grad += l2 * W`) before the Adam step.

### Proposition 2: the training problem has exactly one optimum

**Claim.** With $\lambda > 0$, $\mathcal L$ is strictly convex in $W$, so it has a unique global minimizer and no other local minima.

**Proof.**

1. **Decomposition.** With teacher forcing, example $n$ involves only the block $W_{s_n} = (W_{s_n,\text{cold}}, W_{s_n,\text{warm}}, W_{s_n,\text{hot}})$. So $\mathcal L(W) = \sum_{s} \mathcal L_s(W_s)$: three separate problems, one per previous state.
2. **The data term is convex.** For one example, $W_s \mapsto z_r = W_{s,r}\cdot\varphi_n$ is linear. $-z_{y}$ is linear. $\log\sum_r e^{z_r}$ (log-sum-exp) is convex: its Hessian is $\operatorname{diag}(P) - PP^\top$, and for any $v$, $v^\top(\operatorname{diag}(P) - PP^\top)v = \sum_r P_r v_r^2 - (\sum_r P_r v_r)^2 = \operatorname{Var}_P(v) \ge 0$. A convex function of a linear map is convex, and sums of convex functions are convex.
3. **The penalty is strictly convex.** $\tfrac\lambda2\lVert W\rVert^2$ has Hessian $\lambda I \succ 0$.
4. Convex plus strictly convex is strictly convex. A strictly convex function has at most one minimizer. A minimizer exists because $\mathcal L \to \infty$ as $\lVert W\rVert \to \infty$ (the penalty dominates and the data term is non-negative). $\square$

So any gradient method that converges finds the same weights regardless of initialization; the random initial $W$ in the code only affects the path. (Adam with a fixed step size is not guaranteed to converge exactly, so in practice we check the loss curve in notebook 04.)

### Proposition 3: how the model represents a size cutoff per phase

Fix the current state and compare two next states, say hot vs warm. The model prefers hot when

$$(W_{s,\text{hot}} - W_{s,\text{warm}})\cdot\varphi(x) > 0 .$$

Holding the other features fixed, this is linear in $t = \log_2 \text{size}$: in prefill it reads $a_P\, t + b_P > 0$, in decode $a_D\, t + b_D > 0$. Here $a$ collects the coefficient on $\log_2$ size plus the coefficient on the matching interaction term, and $b$ collects the bias, the phase indicator and the other features. When $a < 0$ (bigger means less hot) the boundary is

$$t^* = -\frac{b}{a}, \qquad \text{size}^* = 2^{-b/a}.$$

- The phase indicators alone already let $b$ differ between phases, so the cutoff can differ.
- The interaction terms also let the **slope** $a$ differ. That lets one linear model be sharp around 64 KiB for prefill and around 256 KiB for decode at the same time, which is the oracle's rule. Without them it would have to share one slope.

So the learned model can represent a per-phase cutoff, which the static rules cannot express, because the static rules depend on a phase detector that (Proposition 1) never sees decode.

## 4. What the synthetic evaluation shows, and what it doesn't

The synthetic generator labels transfers with an oracle:

- token ids and metadata: hot; weights and SSM state: cold;
- decode KV: hot up to 256 KiB, warm above;
- prefill KV: warm up to 64 KiB, cold above.

On held-out synthetic mixes the learned model reaches about 0.99 to 1.0 routing accuracy, and the static classifier recovers about a sixth of the hot transfers on decode-heavy mixes.

What this proves: the learner, the features and the evaluation harness work, and the static detector has the structural problem in Proposition 1.

What it does not prove: that the oracle's labels are the right ones for real hardware. The learned model is fitting a rule that the generator also uses to make its labels, so high accuracy there is partly by construction. The real test is labels from measured completion latency (`wfa_learner.latency_label`, notebook 04 cluster cell): a transfer is "hot" if routing it cold measurably hurt latency.

## 5. Status

| Claim | Status |
|---|---|
| Static detector never reports DECODE for in-order layer traffic | proven (Proposition 1) |
| Most decode deltas routed cold by the static classifier | follows from Proposition 1 + thresholds; 86% on the synthetic decode trace |
| Training gradient | derived above; matches the code |
| Unique optimum of the learned model's training problem | proven (Proposition 2) |
| Per-phase cutoff representable | shown (Proposition 3) |
| Learned model is better on real traffic | open: needs latency-labeled telemetry from the cluster |

## References

- Mohri, Pereira, Riley, "Weighted automata in text and speech processing," 1996 (weighted finite automata).
- Bishop, *Pattern Recognition and Machine Learning*, 2006, Ch. 4.3 (multinomial logistic regression, convexity of cross-entropy).
- Kingma and Ba, "Adam: A Method for Stochastic Optimization," ICLR 2015.
