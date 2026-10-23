# 10. PMP bang-bang controller: hot, cold or spill

[← back to the README section](../../README.md#10-pmp-bang-bang-controller-hot-cold-or-spill)

![PMP controller](../media/10_pmp.gif)

This page derives the controller from scratch, proves why its decisions are all-or-nothing ("bang-bang"), shows where the queue-depth approximation comes from, and then checks the sign of the rule against the code. That check found a real inconsistency, written up in [section 6](#6-checking-the-implemented-rule).

Code: `middleware/rdma_tensor_cache/pmp_controller.py` (`decide`, `decide_with_storage`). Original statement: Update 4, Section "PMP: Bang-Bang QP Allocation"; storage extension: Update 6.

---

## 1. What the controller decides

Two queues share one link of capacity $`C`$:

- $`q_H(t)`$: work waiting on the **hot** endpoint (small, latency-critical transfers),
- $`q_C(t)`$: work waiting on the **cold** endpoint (bulk KV).

Each queue has a service rate when it has the link: $`C\mu_H`$ for hot, $`C\mu_C`$ for cold. At every instant the controller makes one choice, written as a number $`u(t)`$. The choice is the control, and the controller wants to keep the total waiting cost low.

There are two different things $`u`$ can mean, and they lead to different rules. Sections 2 to 5 use Update 4's meaning; section 6 shows why the code actually implements the other one.

- **Service allocation.** $`u \in [0,1]`$ is the share of the link given to the hot queue right now.
- **Routing.** $`u \in [0,1]`$ is the share of newly arriving transfers sent to the hot queue.

## 2. The model (Update 4's dynamics)

With service allocation, arrivals $`\lambda_H(t), \lambda_C(t)`$ come from the classifier and the queues evolve as

```math
\dot q_H = \lambda_H - u\, C\mu_H, \qquad \dot q_C = \lambda_C - (1-u)\, C\mu_C, \qquad u \in [0,1].
```

(While a queue is empty its service term is zero; that boundary does not change the argument below.)

The cost to minimize over a horizon $`[0, T]`$ is a holding cost on the queues:

```math
J = \int_0^T L\big(q_H(t), q_C(t)\big)\, dt .
```

Two choices of $`L`$ matter:

- linear: $`L = \alpha q_H + \beta q_C`$ (cost proportional to how much is waiting),
- quadratic: $`L = \tfrac12(\alpha q_H^2 + \beta q_C^2)`$ (long queues cost disproportionately more, which is what tail latency feels like).

$`\alpha > \beta`$ says hot backlog is more expensive than cold backlog.

## 3. Pontryagin's principle, stated for this problem

Define the **Hamiltonian** (minimum-principle form)

```math
\mathcal H(q, u, p) = L(q) + p_H\,\dot q_H + p_C\,\dot q_C = L(q) + p_H(\lambda_H - uC\mu_H) + p_C(\lambda_C - (1-u)C\mu_C).
```

$`p_H, p_C`$ are the **costates**: $`p_i(t)`$ is the marginal cost-to-go of one more unit of work in queue $`i`$ at time $`t`$ (a "shadow price"). Pontryagin's minimum principle says that along an optimal trajectory:

1. the costates evolve as $`\dot p_i = -\partial \mathcal H / \partial q_i`$, with $`p_i(T) = 0`$ when there is no terminal cost;
2. at every $`t`$, the optimal control minimizes $`\mathcal H`$ over the allowed set: $`u^*(t) \in \arg\min_{u \in [0,1]} \mathcal H(q(t), u, p(t))`$.

These are necessary conditions (Pontryagin et al. 1962).

## 4. Why the optimal choice is all-or-nothing

Collect the terms of $`\mathcal H`$ that contain $`u`$:

```math
\mathcal H = \underbrace{L + p_H\lambda_H + p_C(\lambda_C - C\mu_C)}_{\text{does not depend on } u} \; - \; u\,\underbrace{\big(p_H C\mu_H - p_C C\mu_C\big)}_{S(t)} .
```

$`S(t) = p_H C\mu_H - p_C C\mu_C`$ is the **switching function**.

**Lemma (a linear function on an interval is minimized at an endpoint).** If $`f(u) = a - uS`$ on $`[0,1]`$, then $`f(1) - f(0) = -S`$. If $`S > 0`$, $`f(1) < f(0)`$ and $`f`$ is strictly decreasing, so the unique minimizer is $`u = 1`$. If $`S < 0`$ it is strictly increasing and the minimizer is $`u = 0`$. If $`S = 0`$ every $`u`$ is a minimizer. $`\square`$

So under service allocation:

```math
u^*(t) = \begin{cases} 1 \;(\text{give the link to hot}) & S(t) > 0 \\ 0 \;(\text{give the link to cold}) & S(t) < 0 \\ \text{undetermined} & S(t) = 0. \end{cases}
```

That is the "bang-bang" property: the optimum never splits the link fractionally except on the set where $`S = 0`$ (a singular arc). It holds because the dynamics and the cost are linear in $`u`$, not because of any property of RDMA.

**The same argument with three options.** With spill, the control is $`(u_H, u_C, u_S)`$ on the simplex $`u_H + u_C + u_S = 1`$, $`u_i \ge 0`$, and $`\mathcal H = \text{const} + \sum_i u_i \sigma_i`$ for some coefficients $`\sigma_i`$. A linear function on the simplex is minimized at a vertex: for any point, $`\sum_i u_i\sigma_i \ge \min_i \sigma_i \sum_i u_i = \min_i \sigma_i`$, with equality at the vertex $`u_{k} = 1`$ for $`k = \arg\min_i \sigma_i`$. $`\square`$ So the three-way controller picks the single option with the smallest coefficient. That is what `decide_with_storage` does.

## 5. Where "costate ≈ queue depth" comes from

The controller cannot solve the costate equations online (they run backward from $`T`$). It replaces $`p_H, p_C`$ with something observable. The costate equation tells us what is reasonable:

- **Linear holding cost.** $`\dot p_H = -\partial \mathcal H/\partial q_H = -\alpha`$, so $`p_H(t) = \alpha (T - t)`$ and likewise $`p_C(t) = \beta(T-t)`$. Then $`S = (T-t)\,C\,(\alpha\mu_H - \beta\mu_C)`$. Its sign never changes, so the optimal policy is a fixed priority: always serve the queue with the larger $`\alpha\mu`$ (cost times service rate). This is the classical $`c\mu`$ rule (Cox and Smith, 1961). Queue depth does not appear at all.
- **Quadratic holding cost.** $`\dot p_H = -\alpha q_H`$, so $`p_H(t) = \int_t^T \alpha\, q_H(s)\, ds`$. Over a short look-ahead window $`\tau`$ in which $`q_H`$ changes little, $`p_H(t) \approx \alpha\,\tau\, q_H(t)`$, and the same for cold. Substituting, $`S \approx \tau C\,(\alpha q_H \mu_H - \beta q_C \mu_C)`$, and the positive factor $`\tau`$ does not change the sign.

So **"costate proportional to queue depth" is the myopic approximation to a quadratic holding cost**. It is an approximation, not a theorem: it ignores how the queues will evolve inside the window. With it, the service-allocation rule reads

```math
\text{give the link to hot} \iff \alpha\, q_H\, \mu_H > \beta\, q_C\, \mu_C ,
```

which is a queue-length-weighted $`c\mu`$ rule: serve the queue whose backlog is most expensive to leave waiting, scaled by how quickly serving it pays off.

## 6. Checking the implemented rule

`decide()` computes exactly $`S = \alpha q_H C\mu_H - \beta q_C C\mu_C`$, and then:

```python
if S > deadband:   decision = COLD_QP   # "hot congested relative to cold: send to cold"
elif S < -deadband: decision = HOT_QP
```

and its return value is used as **the queue the next transfer joins**. That is the routing meaning of $`u`$, not service allocation. Two problems follow.

1. **Sign.** Under the model the switching function was derived from (service allocation), $`S > 0`$ means *serve hot* (section 4). The code maps $`S > 0`$ to cold. The comment's reasoning ("hot is congested, so send new work elsewhere") is a routing argument applied to a formula derived for service.
2. **The $`\mu`$ factors.** Redo the derivation with routing as the control. If a fraction $`u`$ of arrivals $`\lambda`$ goes to hot,

   ```math
   \dot q_H = u\lambda - C\mu_H, \qquad \dot q_C = (1-u)\lambda - C\mu_C,
   ```

   the $`u`$-terms of $`\mathcal H`$ are $`u\,\lambda\,(p_H - p_C)`$, and by the lemma the minimizer is $`u = 1`$ (join hot) when $`p_H < p_C`$ and $`u = 0`$ (join cold) when $`p_H > p_C`$. With the quadratic-cost approximation $`p_i \approx \tau\,(\text{weight}_i)\, q_i`$, the rule is **join the queue with the smaller weighted backlog**, $`\alpha q_H`$ vs $`\beta q_C`$: no $`\mu`$ at all. If instead the cost is the delay the new transfer itself will see, joining queue $`i`$ costs its expected wait $`q_i / (C\mu_i)`$, giving

   ```math
   \text{join cold} \iff \frac{\alpha\, q_H}{C\mu_H} > \frac{\beta\, q_C}{C\mu_C}.
   ```

   Either way the service rates divide, they do not multiply. Multiplying makes a *faster* hot queue look *more* expensive.

**Consequence with the default parameters** ($`\alpha = 2, \beta = 1, \mu_H = 10000, \mu_C = 2000`$): the code sends a transfer to cold whenever $`20000\,q_H > 2000\,q_C`$, i.e. whenever $`q_H > q_C/10`$. One outstanding hot operation and fewer than ten cold ones already routes the next transfer to cold. The routing-consistent rule with expected wait would compare $`2q_H/10000`$ with $`q_C/2000`$, i.e. route to cold only when $`q_H > 2.5\, q_C`$.

**What this means for the thesis.** The bang-bang structure (section 4) is proven and stays. The specific switching function in the code is not the one the stated model implies. Two consistent options:

- keep routing as the control and use $`S_{\text{route}} = \alpha q_H/\mu_H - \beta q_C/\mu_C`$ (join cold when positive), or
- make the controller allocate service (a weighted share of polling or posting between endpoints) and keep $`S`$ with the corrected sign.

The code has not been changed yet; the existing tests encode the current behavior. Experiment-wise, notebook 07 and any PMP result should be re-run after the fix.

## 7. The spill option (Update 6)

Add GPU KV occupancy $`u_{\text{gpu}} \in [0,1]`$ and a watermark $`u_0`$. Define the normalized pressure

```math
p = \frac{\max(0,\; u_{\text{gpu}} - u_0)}{1 - u_0} \in [0, 1],
```

which is 0 below the watermark and 1 when memory is full. Add a running cost $`\gamma\,\max(0, u_{\text{gpu}} - u_0)`$ and a third queue $`q_S`$ (NVMe spill, service rate $`\mu_S`$). Sending a block to spill is the only option that lowers occupancy, so its coefficient gets a negative term proportional to the pressure. With the same queue-depth approximation the three coefficients are

```math
\sigma_H = \alpha\, q_H\, C\mu_H, \qquad \sigma_C = \beta\, q_C\, C\mu_C, \qquad \sigma_S = \delta\, q_S\, \mu_S - \gamma\, p,
```

and by the simplex lemma (section 4) the controller picks $`\arg\min_i \sigma_i`$. Properties that follow directly:

- **Below the watermark nothing changes.** $`p = 0`$, and the code skips the spill option entirely, so the result equals the two-queue decision. (Proof: `decide_with_storage` calls `decide` when `pressure <= 0`.)
- **Spill wins once pressure is high enough.** $`\sigma_S < \min(\sigma_H, \sigma_C)`$ exactly when $`\gamma p > \delta q_S \mu_S - \min(\sigma_H, \sigma_C)`$. With $`\gamma`$ large (default 50000) a small amount of pressure suffices.
- **Spill backs off as its own queue grows.** $`\sigma_S`$ increases with $`q_S`$, so a slow drive with a long spill queue stops winning.

The $`\mu`$-multiplication issue from section 6 applies to $`\sigma_H`$ and $`\sigma_C`$ here as well.

## 8. Chattering and the deadband

Near $`S = 0`$ a pure bang-bang rule can flip on every decision (in continuous time, an infinite switching rate; this is the classic chattering problem of sliding modes). The code adds hysteresis: it switches only when $`|S|`$ exceeds a deadband $`\epsilon`$, and otherwise keeps the previous choice. For the three-way rule it keeps the previous option while $`\sigma_{\text{prev}} - \min_i \sigma_i \le \epsilon`$.

Why this bounds switching: between two switches $`S`$ must travel from $`+\epsilon`$ to $`-\epsilon`$ (or back), a distance of $`2\epsilon`$. If $`S`$ changes at most at rate $`|\dot S| \le M`$, consecutive switches are at least $`2\epsilon / M`$ apart. In discrete decisions, where $`S`$ changes by at most $`\Delta`$ per decision, at least $`\lceil 2\epsilon/\Delta \rceil`$ decisions separate two switches. The price is that inside the band the decision can be up to $`\epsilon`$ worse than the instantaneous optimum.

## 9. Status

| Claim | Status |
|---|---|
| Bang-bang optimality given linear dynamics and cost | proven above (necessary condition from PMP + the endpoint/vertex lemma) |
| Costate ∝ queue depth | approximation; justified for quadratic holding cost over a short window |
| Sign and form of the implemented switching function | inconsistent with the model it was derived from (section 6); fix proposed, not applied |
| Values in the animation | illustrative queue depths, not measurements |
| Effect on latency | not measured yet; needs the cluster runs |

## References

1. L. S. Pontryagin, V. G. Boltyanskii, R. V. Gamkrelidze, E. F. Mishchenko. *The Mathematical Theory of Optimal Processes.* Interscience, 1962. *Used for: the minimum principle (§3).*
2. D. Liberzon. *Calculus of Variations and Optimal Control Theory: A Concise Introduction.* Princeton University Press, 2012, Ch. 4 (the maximum principle, with time-optimal and bang-bang controls). *Modern statement of §3–§4.*
3. R. Bellman, I. Glicksberg, O. Gross. "On the 'bang-bang' control problem." *Quarterly of Applied Mathematics* 14(1):11–18, 1956. [AMS](https://www.ams.org/qam/1956-14-01/S0033-569X-1956-78516-4/). *Used for: optimality of bang-bang control for linear systems (§4).*
4. D. R. Cox, W. L. Smith. *Queues.* Methuen, 1961. *Used for: the cμ rule (§5).*
5. C. Buyukkoc, P. Varaiya, J. Walrand. "The cμ rule revisited." *Advances in Applied Probability* 17(1):237–238, 1985. [Cambridge](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/4208A5791793438658BF774D4D9DF013/S0001867800014774a.pdf/div-class-title-the-span-class-italic-c-span-rule-revisited-div.pdf). *Short proof of the cμ rule (§5).*
6. J. A. Van Mieghem. "Dynamic Scheduling with Convex Delay Costs: The Generalized cμ Rule." *Annals of Applied Probability* 5(3):809–833, 1995. [Project Euclid](https://projecteuclid.org/euclid.aoap/1177004706). *Used for: with convex (e.g. quadratic) costs the priority depends on queue state, which is what the queue-depth approximation captures (§5).*
7. V. I. Utkin. "Variable structure systems with sliding modes." *IEEE Transactions on Automatic Control* 22(2):212–222, 1977. *Used for: chattering near the switching surface (§8).*
8. Update 4 (`Updates/Update4-UCX/update4.tex`, Section "PMP: Bang-Bang QP Allocation") and Update 6 (`Updates/Update6-StorageTier/update6.tex`). *The original statements checked in §6–§7.*
