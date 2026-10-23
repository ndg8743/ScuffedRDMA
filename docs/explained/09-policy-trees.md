# 9. Rule-Node Expression Trees

[← back to the README section](../../README.md#9-rule-node-expression-trees)

![Policy tree evaluation](../media/09_policy.gif)

The policy engine turns signals into a routing decision with rules a person can read and edit. This page defines the semantics precisely and proves four properties:

1. the result does not depend on evaluation shortcuts;
2. each decision field is set by exactly one rule, the highest-priority one that sets it;
3. the trace explains the result;
4. the cost is linear in the size of the policy.

Code: `middleware/policy/tree.py` (`PolicyEngine`), default policy `middleware/policy/default_policy.json`. Notebook 04.

---

## 1. Definitions

**Inputs.** A transfer's `SignalVector` (size, role, phase, ...) and a context dict (for example `gpu_mem_util`, `link_util`). A field name resolves from the context first, then the signal vector, then two derived fields: `log2_size`, and `route` (the route decided so far, else the default).

**Nodes.** A rule's condition is a tree built from

| node | value |
|---|---|
| `{"and": [n1, ..., nk]}` | true iff every child is true |
| `{"or": [n1, ..., nk]}` | true iff some child is true |
| `{"not": n}` | negation |
| `{"threshold": {"field": f, "op": o, "value": v}}` | compares field $f$ with $v$ using $<, \le, >, \ge, =, \ne$ |
| `{"in": {"field": f, "values": [...]}}` | membership |
| `{"classifier": {"name": c, "equals": s}}` | calls registered classifier $c$ (for example the WFA) and compares its state |
| `{"true": true}`, `{"false": true}` | constants |

A leaf whose field is missing is false, and the miss is recorded (strict mode raises instead).

**Rules.** Each rule has a name, a priority, a condition, an action (`route` ∈ {hot, cold, spill} and/or `compress` ∈ {true, false}), and an optional `final` flag.

**Decision procedure.**

1. Sort rules by priority, highest first; ties keep file order.
2. Start with both decision fields unset.
3. For each rule: if its condition is true, set each action field **that is still unset**. Record which rule set it and the leaf values that made it match. If the rule is `final`, stop.
4. Fill any field still unset from the default (`route = cold`, `compress = false`).

## 2. Proposition 1: short-circuiting does not change the result

`and` stops at the first false child and `or` at the first true one.

**Claim.** The value of every condition is the same as if all children were evaluated.

**Proof.** For `and`: if child $j$ is false the conjunction is false regardless of the rest, and if no child is false all children were evaluated. Same for `or` with true. This is only safe if evaluating a child has no effect on later evaluations. Comparison leaves are pure functions of the inputs. Classifier leaves could have side effects (a WFA updates its state when called), so the engine calls each named classifier **at most once per decision** and reuses the answer for every other leaf that names it. With that memoization every leaf is a pure function of (inputs, memo), so skipping a leaf changes nothing that another leaf reads. $\square$

## 3. Proposition 2: each field belongs to the highest-priority rule that sets it

**Claim.** After the procedure, `route` equals the action of the highest-priority rule (earliest in sorted order) whose condition is true and whose action contains `route`, or the default if there is none, stopping early at a `final` rule. The same holds for `compress`.

**Proof (induction over the sorted rule list).** Invariant after processing the first $i$ rules: each field that is set holds the value from the earliest matching rule among those $i$ that sets it, and each unset field has no such rule among them. Initially nothing is set and nothing has been processed. Processing rule $i+1$: if it does not match, nothing changes. If it matches, it sets only fields that are still unset, and by the invariant no earlier matching rule sets those, so rule $i+1$ is the earliest for them. Fields already set are untouched. A `final` rule ends the loop with the invariant intact, and the default fills only fields no processed rule set. $\square$

**Consequence: later rules can read earlier decisions.** Rule 60 in the default policy tests `route ∈ {cold, spill}`. Because rules run in priority order and `route` is resolved as "the route decided so far", rule 60 sees whatever rules 100–70 chose. That is intended: "compress bulk when the link is busy" should apply to whatever is going cold or to disk.

## 4. Worked example (the animation)

Input: a 4 MiB prefill KV block (`role=kv`, `phase=prefill`, `size_bytes=4194304`), context `gpu_mem_util=0.93`, `link_util=0.85`.

| priority | rule | condition | result |
|---|---|---|---|
| 100 | control-messages-hot | role ∈ {metadata, token} | false (role is kv) |
| 90 | spill-bulk-under-gpu-pressure | gpu ≥ 0.9 ∧ size > 256 KiB ∧ ¬(phase = decode) | true: **route = spill** |
| 80 | decode-small-kv-hot | phase = decode ∧ … | false at the first child (short-circuit) |
| 70 | prefill-bulk-cold | phase = prefill ∧ size > 64 KiB | true, but route is already set: no effect |
| 60 | compress-bulk-when-link-busy | link ≥ 0.8 ∧ route ∈ {cold, spill} ∧ size ≥ 256 KiB | true: **compress = true** |
| 30 | wfa-hot | wfa = hot ∧ size ≤ 256 KiB | false |
| 20 | tiny-anything-hot | size < 4 KiB | false |

Decision: spill to NVMe, compressed. The trace names rule 90 for `route` and rule 60 for `compress`, with the leaf values that matched.

## 5. Proposition 3: cost is linear

**Claim.** One decision costs $O(|T| + c)$, where $|T|$ is the total number of nodes in all rules and $c$ the number of distinct classifiers referenced.

**Proof.** Each node is visited at most once per decision (each rule is evaluated at most once, and short-circuiting only skips nodes). A leaf costs $O(1)$ plus, for a classifier leaf, one classifier call at most once per name by memoization. Sorting rules happens once when the policy is loaded, not per decision. $\square$

## 6. Why trees instead of the WFA alone

The WFA predicts one thing (how hot a tensor is) from history. The policy combines that with facts the WFA does not see (GPU memory pressure, link load) and with operator intent (never compress decode traffic, always keep tokens hot), in a form someone can audit. The WFA is one leaf type in the tree, not the policy. The design follows the rule composition of the vLLM Semantic Router.

## 7. Status

| Claim | Status |
|---|---|
| Short-circuiting is safe | proven, given per-decision classifier memoization (implemented) |
| Highest-priority rule owns each field | proven (induction) |
| Linear cost | proven |
| Default policy is the right policy | open: tuned once cluster telemetry exists |

## References

- vLLM Semantic Router (rule composition model).
- `middleware/policy/tree.py` docstring (node types, resolution order).
