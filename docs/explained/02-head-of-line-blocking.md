# 2. Head-of-line blocking

[← back to the README section](../../README.md#2-head-of-line-blocking)

![Head-of-line blocking](../media/02_headofline.gif)

"Head-of-line blocking" means a message cannot start until everything queued in front of it has finished. This page proves how large that wait is, first in the worst case shown in the animation and then on average using standard queueing results, and shows exactly which assumption the dual pool relies on to remove it.

---

## 1. Worst case: one FIFO queue, deterministic

A link of rate $`C`$ sends one message at a time, in arrival order (first in, first out). A message of $`s`$ bytes takes $`s \cdot 8 / C`$ seconds to serialize.

**Claim.** A message arriving behind messages of sizes $`s_1, \dots, s_n`$ waits

```math
W = \frac{8}{C}\sum_{i=1}^n s_i
```

before its first byte is sent (plus whatever remains of the message currently on the wire).

**Proof.** FIFO means the message starts only after all earlier messages complete, and each one occupies the link for its own serialization time. The waits add. $`\square`$

For 1 MiB blocks at 10 Gb/s: $`2^{20}\cdot 8 / 10^{10} = 0.839`$ ms each, so four blocks ahead cost **3.36 ms** for a 4 KiB message whose own transfer takes 3.3 µs. The small message spends about 1000 times longer waiting than moving.

## 2. Average case: the Pollaczek–Khinchine formula

Real traffic is random. The standard model is the **M/G/1 queue**: messages arrive as a Poisson process with rate $`\lambda`$, service times $`S`$ (serialization times) have any distribution, one server (the link), FIFO.

### The formula

Mean waiting time before service:

```math
W = \frac{\lambda\, \mathbb E[S^2]}{2\,(1 - \rho)}, \qquad \rho = \lambda\, \mathbb E[S] < 1 .
```

### Proof

Let $`R`$ be the mean remaining service time of whatever is on the link when a new message arrives (0 if idle), and $`N_q`$ the mean number of messages waiting. An arriving message waits for the one in service to finish and then for everyone already queued:

```math
W = R + N_q\,\mathbb E[S].
```

**Little's law** applied to the waiting line gives $`N_q = \lambda W`$. Substituting, $`W = R + \rho W`$, so

```math
W = \frac{R}{1-\rho}.
```

**Computing $`R`$.** Poisson arrivals see the time-average state of the system (the PASTA property), so $`R`$ is the long-run time average of "remaining service". Plot remaining service against time: each message with service time $`S_k`$ contributes a triangle of height $`S_k`$ and width $`S_k`$, area $`S_k^2/2`$. Over a long interval $`\tau`$ about $`\lambda\tau`$ messages are served, so

```math
R = \frac{1}{\tau}\sum_{k=1}^{\lambda \tau}\frac{S_k^2}{2} \;\longrightarrow\; \frac{\lambda\,\mathbb E[S^2]}{2}.
```

Putting the two together gives the formula. $`\square`$

### What it says about mixing small and large messages

The wait depends on $`\mathbb E[S^2]`$, the **second moment** of the service time, and every message in the queue sees the same $`W`$ regardless of its own size. Mixing in a few huge messages makes $`\mathbb E[S^2]`$ huge, and the tiny messages pay for it.

## 3. A worked example: one queue vs priority vs packet-level interleaving

Assumptions (illustrative, chosen to be plausible for the testbed, not measured):

- link $`C = 10`$ Gb/s;
- cold: 1 MiB messages ($`S_C = 0.839`$ ms) at 60% load, so $`\lambda_C = 715`$ per second;
- hot: 4 KiB messages ($`S_H = 3.28`$ µs) at 10,000 per second, 3.3% load;
- Poisson arrivals for both.

**(a) One FIFO queue.** $`\lambda\mathbb E[S^2] = \lambda_C S_C^2 + \lambda_H S_H^2 \approx 5.03\times10^{-4}`$ s, $`\rho = 0.633`$:

```math
W_{\text{FIFO}} = \frac{5.03\times 10^{-4}}{2(1 - 0.633)} \approx 0.69 \text{ ms}.
```

A hot message waits on average 0.69 ms, about 200 times its own transfer time.

**(b) Two queues, hot first, but the link finishes a message once started.** This is non-preemptive priority. For the high-priority class, Cobham's formula gives

```math
W_H = \frac{R}{1 - \rho_H}, \qquad R = \frac{\lambda\,\mathbb E[S^2]}{2}.
```

Proof: a hot arrival waits for the message in service (mean residual $`R`$, same argument as above) plus the hot messages already queued ($`\rho_H W_H`$ by Little's law); cold messages behind it never go first. So $`W_H = R + \rho_H W_H`$. $`\square`$

Here $`W_H \approx 2.5\times10^{-4}/0.967 \approx`$ **0.26 ms**. Better, but the hot message still often waits for a whole 1 MiB block that had already started.

**(c) Two queues, and the NIC interleaves at packet granularity.** If the sender alternates between queues per packet (say 4 KiB packets), the "service unit" a hot message can get stuck behind is one packet, not a whole message. Re-doing (b) with cold traffic as 4 KiB packets ($`256`$ per message) gives $`R \approx 1.0`$ µs and

```math
W_H \approx 1.07 \text{ µs}.
```

Separate queues **plus** packet-level arbitration bring the average hot wait from 0.69 ms to about 1 µs in this model, a factor of about 640.

## 4. What the dual pool actually guarantees, and what it assumes

- **Guaranteed by construction.** A hot message on the hot endpoint has no cold message ahead of it *in its own queue*. That removes case (a).
- **Assumed, and measured in E3.** Below the queues, the NIC or software stack must take turns between queue pairs at a fine granularity, as in case (c). With a hardware NIC that schedules between QPs per packet or burst, that is plausible. With SoftRoCE, one kernel thread (`rxe`) processes all QPs, and whether it interleaves finely or drains one QP's message before the next is exactly what experiment E3 measures:
  - if dual-endpoint hot p99 under a cold stream stays near the unloaded p99, the arbitration is fine-grained (case c);
  - if it grows with cold message size, the stack is behaving like case (b) or (a) below the queue pair, and the fix has to go lower (e.g. smaller cold writes).
- **Not modeled.** Poisson arrivals, a single link, no retransmissions. Real traffic is burstier, which makes the FIFO case worse ($`\mathbb E[S^2]`$ and correlation both grow).

## 5. Status

| Claim | Status |
|---|---|
| FIFO wait = sum of serialization times ahead | proven, deterministic |
| 3.36 ms behind four 1 MiB blocks at 10 Gb/s | arithmetic |
| Pollaczek–Khinchine and Cobham formulas | proven above under M/G/1 assumptions |
| 0.69 ms / 0.26 ms / 1.07 µs comparison | model output with stated assumptions, not measurements |
| Whether SoftRoCE interleaves QPs finely | open: experiment E3 (notebook 01) |

## References

1. L. Kleinrock. *Queueing Systems, Volume 1: Theory.* Wiley, 1975. *Used for: the M/G/1 model and the mean-residual-time derivation (§2).*
2. F. Pollaczek. "Über eine Aufgabe der Wahrscheinlichkeitstheorie." *Mathematische Zeitschrift* 32, 1930; A. Ya. Khinchine. "Mathematical theory of a stationary queue." *Matematicheskii Sbornik* 39(4), 1932. *Used for: the Pollaczek–Khinchine mean-wait formula (§2).*
3. A. Cobham. "Priority Assignment in Waiting Line Problems." *Operations Research* 2(1):70–76, 1954. [doi:10.1287/opre.2.1.70](https://doi.org/10.1287/opre.2.1.70). *Used for: the non-preemptive priority wait $`W_H = R/(1-\rho_H)`$ (§3b, §3c).*
4. J. D. C. Little. "A Proof for the Queuing Formula: L = λW." *Operations Research* 9(3):383–387, 1961. [doi:10.1287/opre.9.3.383](https://doi.org/10.1287/opre.9.3.383). *Used for: $`N_q = \lambda W`$ in both proofs.*
5. R. W. Wolff. "Poisson Arrivals See Time Averages." *Operations Research* 30(2):223–231, 1982. [doi:10.1287/opre.30.2.223](https://doi.org/10.1287/opre.30.2.223). *Used for: PASTA, which makes $`R`$ the time-average residual (§2).*
6. M. Harchol-Balter. *Performance Modeling and Design of Computer Systems: Queueing Theory in Action.* Cambridge University Press, 2013. *Accessible treatment of the same results.*
7. Update 8, experiment E3 (`Updates/Update8-Libfabric/update8.pdf`) and notebook 01. *Used for: how the separation is measured on SoftRoCE (§4).*
