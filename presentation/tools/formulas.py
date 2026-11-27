#!/usr/bin/env python3
"""Render the formulas of the deck to transparent PNGs. Writes assets/math/<name>.png and manifest.json
(name -> width_pt, height_pt at a 10 pt base size, alt text)."""
import json, os, subprocess, sys

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "math")
TMP = OUT + "/tmp"
os.makedirs(TMP, exist_ok=True)
F = {
 "attention": (r"\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\!\left(\frac{QK^{\top}}{\sqrt{d}}\right)V",
               "Attention of Q, K and V equals the softmax of Q times K transposed divided by the square root of d, times V"),
 "cache_size": (r"s_{\mathrm{layer}} = 2\,h\,d\,w\,T, \qquad s_{\mathrm{cache}} = L\, s_{\mathrm{layer}}",
                "s layer equals 2 times h times d times w times T, and s cache equals L times s layer"),
 "attention2": (r"\begin{aligned} A &= \mathrm{softmax}\!\Big(\frac{QK^{\top}}{\sqrt{d}}\Big) \\[4pt] \mathrm{output} &= A\,V \end{aligned}",
                "A equals the softmax of Q times K transposed divided by the square root of d, and the output equals A times V"),
 "cache_layer": (r"s_{\mathrm{layer}} = 2\,h\,d\,w\,T",
                 "s layer equals 2 times h times d times w times T"),
 "cache_total": (r"s_{\mathrm{cache}} = L\, s_{\mathrm{layer}}",
                 "s cache equals L times s layer"),
 "pk_defs": (r"S = \frac{8s}{C}, \qquad \rho = \lambda\,\mathrm{E}[S]",
             "S equals 8 s over C, and rho equals lambda times the expected value of S"),
 "chunk_max": (r"\text{chunk payload} \;\le\; B - 64 - |\text{key}|",
               "the chunk payload is at most B minus 64 minus the length of the key"),
 "hessian": (r"\nabla^{2}\,\mathrm{lse}(z) = \mathrm{diag}(\pi) - \pi\,\pi^{\top} \succeq 0",
             "the Hessian of the log-sum-exp function equals the diagonal matrix of pi minus pi times pi transposed, which is positive semidefinite"),
 "yi": (r"y_i = \frac{1}{\sqrt{d}}\sum_{j=1}^{d} H_{ij}\,\delta_j\,u_j",
        "y i equals 1 over the square root of d, times the sum over j of H i j times delta j times u j"),
 "wire": (r"t_{\mathrm{wire}} = \frac{8\, s_{\mathrm{cache}}}{C}",
          "t wire equals 8 times s cache divided by C"),
 "hol": (r"W = \frac{8}{C}\sum_{i=1}^{k} s_i",
         "W equals 8 over C, times the sum of s i for i from 1 to k"),
 "pk": (r"\overline{W} = \frac{\lambda\,\mathrm{E}[S^{2}]}{2\,(1-\rho)}",
        "the mean wait W bar equals lambda times the expected value of S squared, divided by 2 times 1 minus rho"),
 "bound": (r"X \;\le\; \frac{N\,B}{t_{\mathrm{credit}}}",
           "X is at most N times B divided by t credit"),
 "staging": (r"\frac{t_{\mathrm{copy}}}{t_{\mathrm{wire}}} = \frac{s/P}{8s/C} = \frac{C}{8P}",
             "t copy divided by t wire equals s over P divided by 8 s over C, which equals C divided by 8 P"),
 "softmax": (r"P(s' \mid s, x) = \frac{\exp\!\big(W_{s,s'}\cdot\phi(x)\big)}{\sum_{r}\exp\!\big(W_{s,r}\cdot\phi(x)\big)}",
             "the probability of next state s prime, given state s and transfer x, equals the exponential of W s s prime dot phi of x, divided by the sum over the three states r of the exponential of W s r dot phi of x"),
 "objective": (r"J(W) = -\frac{1}{n}\sum_{i=1}^{n}\log P(y_i \mid s_i, x_i) + \frac{\eta}{2}\,\lVert W\rVert^{2}, \qquad \eta > 0",
               "J of W equals minus one over n times the sum over the n examples of the logarithm of the probability of the labeled next state, plus eta over 2 times the squared length of W, with eta greater than zero"),
 "queues": (r"\frac{dq_H}{dt} = \lambda_H - u\,C\,\mu_H, \qquad \frac{dq_C}{dt} = \lambda_C - (1-u)\,C\,\mu_C",
            "the rate of change of q H equals lambda H minus u times C times mu H, and the rate of change of q C equals lambda C minus 1 minus u, times C times mu C"),
 "switching": (r"S = p_H\,C\,\mu_H - p_C\,C\,\mu_C",
               "S equals p H times C times mu H, minus p C times C times mu C"),
 "implemented": (r"\alpha\,q_H\,\mu_H > \beta\,q_C\,\mu_C \;\;\Longleftrightarrow\;\; q_H > \tfrac{1}{10}\,q_C",
                 "alpha times q H times mu H is greater than beta times q C times mu C, which with the default values means q H greater than one tenth of q C"),
 "consistent": (r"\frac{\alpha\,q_H}{\mu_H} > \frac{\beta\,q_C}{\mu_C} \;\;\Longleftrightarrow\;\; q_H > 2.5\,q_C",
                "alpha times q H divided by mu H is greater than beta times q C divided by mu C, which with the default values means q H greater than two and a half times q C"),
 "rotation": (r"y = \frac{1}{\sqrt{d}}\,H\,D\,u",
              "y equals 1 over the square root of d, times H times D times u"),
 "hadamard": (r"H_1 = (1), \qquad H_{2n} = \begin{pmatrix} H_n & H_n \\ H_n & -H_n \end{pmatrix}",
              "H 1 is the one by one matrix 1, and H of 2 n is the two by two block matrix with rows H n, H n and H n, minus H n"),
 "rrt": (r"R = \frac{1}{\sqrt{d}}\,H_d\,D, \qquad R\,R^{\top} = I",
         "R equals 1 over the square root of d, times H d times D, and R times R transposed equals the identity"),
 "variance": (r"\mathrm{E}[y_i] = 0, \qquad \mathrm{Var}[y_i] = \frac{1}{d}",
              "the expected value of y i is zero and the variance of y i is 1 over d"),
 "score": (r"\mathrm{Score}(q) = \langle q, \hat{x}\rangle + \rho\,\frac{\sqrt{\pi/2}}{m}\sum_{j=1}^{m} z_j\,\langle s_j, q\rangle",
           "Score of q equals the inner product of q and x hat, plus rho times the square root of pi over 2 divided by m, times the sum over the m projections of z j times the inner product of s j and q"),
 "packed": (r"s_{\mathrm{packed}} = 4 + 4 + \left\lceil \frac{d\,b}{8} \right\rceil + \left\lceil \frac{m}{8} \right\rceil",
            "s packed equals 4 plus 4 plus the ceiling of d times b over 8, plus the ceiling of m over 8"),
 "packed64": (r"4 + 4 + 24 + 32 = 64\ \text{bytes}",
              "4 plus 4 plus 24 plus 32 equals 64 bytes"),
 "reconstruct": (r"\hat{x} = \frac{\ell}{\sqrt{d}}\,D\,H\,\hat{y}",
                 "x hat equals l over the square root of d, times D times H times y hat"),
 "batching": (r"X(n) = \frac{n\,s_{\mathrm{blk}}}{t_{\mathrm{fix}} + n\,t_{\mathrm{blk}}} \;\longrightarrow\; \frac{s_{\mathrm{blk}}}{t_{\mathrm{blk}}}",
              "X of n equals n times s block, divided by t fix plus n times t block, which tends to s block divided by t block as n grows"),
 "penalty": (r"\mathrm{penalty} = \frac{p99_{\mathrm{hot}}(\text{cold stream on})}{p99_{\mathrm{hot}}(\text{cold stream off})}",
             "penalty equals the 99th percentile of the hot latency with the cold stream on, divided by the 99th percentile with the cold stream off"),
 "ttft": (r"t_{\mathrm{TTFT}} = t_{\mathrm{prefill}} + t_{\mathrm{transfer}} + t_{\mathrm{first\ decode}}",
          "time to first token equals t prefill plus t transfer plus t first decode"),
 "oneway": (r"t_{\mathrm{one\ way}} = \frac{t_{\mathrm{round\ trip}}}{2}",
            "one-way latency equals round-trip time divided by two"),
 "proof54a": (r"(K - N)\,t_{\mathrm{credit}} \;\le\; N\,t_{\mathrm{obs}} \quad\Longrightarrow\quad K \;\le\; N + \frac{N\,t_{\mathrm{obs}}}{t_{\mathrm{credit}}}",
              "K minus N, times t credit, is at most N times t observed, so K is at most N plus N times t observed divided by t credit"),
 "proof54b": (r"X \;\le\; \frac{B\,K}{t_{\mathrm{obs}}} \;\le\; \frac{N\,B}{t_{\mathrm{obs}}} + \frac{N\,B}{t_{\mathrm{credit}}}",
              "X is at most B times K divided by t observed, which is at most N times B divided by t observed, plus N times B divided by t credit"),
 "delta": (r"\Delta(x) = -\gamma_P\,(t\,p - \tau_P\,p) - \gamma_D\,(t\,e - \tau_D\,e)",
           "Delta of x equals minus gamma P times t p minus tau P times p, minus gamma D times t e minus tau D times e"),
 "hht": (r"H_d\,H_d^{\top} = d\,I",
         "H d times H d transposed equals d times the identity"),
 "sketch_est": (r"\langle q, r\rangle \;\approx\; \lVert r\rVert\,\frac{\sqrt{\pi/2}}{m}\sum_{j=1}^{m} z_j\,\langle s_j, q\rangle, \qquad z_j = \mathrm{sign}\,\langle s_j, r\rangle",
                "the inner product of q and r is estimated by the length of r times the square root of pi over 2 divided by m, times the sum of z j times the inner product of s j and q, where z j is the sign of the inner product of s j and r"),
 "sketch_est2": (r"\langle q, r\rangle \;\approx\; \lVert r\rVert\,\frac{\sqrt{\pi/2}}{m}\sum_{j=1}^{m} z_j\,\langle s_j, q\rangle",
                 "the inner product of q and r is estimated by the length of r times the square root of pi over 2 divided by m, times the sum of z j times the inner product of s j and q"),
 "sketch_sd": (r"\text{standard deviation} \;\le\; \sqrt{\frac{\pi}{2m}}\;\lVert r\rVert\,\lVert q\rVert",
               "the standard deviation is at most the square root of pi over 2 m, times the length of r times the length of q"),
 "lemma610": (r"\mathrm{E}\big[\mathrm{sign}(X)\,Y\big] = \sqrt{\frac{2}{\pi}}\;\frac{\kappa}{\sigma}",
              "the expected value of the sign of X times Y equals the square root of 2 over pi, times kappa divided by sigma"),
 "window": (r"N\,B = 8 \times 4\ \mathrm{MiB} = 32\ \mathrm{MiB}",
            "N times B equals 8 times 4 mebibytes, which is 32 mebibytes"),
 "ratio": (r"\frac{4\ \mathrm{MiB}}{8\ \mathrm{bytes}} = 524{,}288",
           "4 mebibytes divided by 8 bytes equals 524,288"),
 "softmax_def": (r"\mathrm{softmax}(z)_i = \frac{e^{z_i}}{\sum_{j} e^{z_j}}",
                 "the softmax of z at entry i equals e to the z i, divided by the sum over j of e to the z j"),
 "wire_num": (r"t_{\mathrm{wire}} = \frac{8\, s_{\mathrm{cache}}}{C} = \frac{8\cdot 160\cdot 2^{20}}{10^{10}}\ \mathrm{s} = 134.2\ \mathrm{ms}",
              "t wire equals 8 times s cache divided by C, which is 8 times 160 times 2 to the 20, divided by 10 to the 10, seconds, which is 134.2 milliseconds"),
 "hol_num": (r"W = \frac{8}{C}\sum_{i=1}^{k} s_i = \frac{8\cdot 4\cdot 2^{20}}{10^{10}}\ \mathrm{s} = 3.36\ \mathrm{ms}",
             "W equals 8 over C times the sum of s i for i from 1 to k, which is 8 times 4 times 2 to the 20, divided by 10 to the 10, seconds, which is 3.36 milliseconds"),
 "cache_num": (r"s_{\mathrm{layer}} = 2\cdot 8\cdot 64\cdot 2\cdot T = 2{,}048\,T\ \text{bytes}",
               "s layer equals 2 times 8 times 64 times 2 times T, which is 2,048 times T bytes"),
 "batch_time": (r"t_{\mathrm{batch}}(n) = t_{\mathrm{fix}} + n\,t_{\mathrm{blk}}",
                "the time of a batch of n blocks equals t fix plus n times t block"),
 "amdahl": (r"S(N) = \frac{1}{(1-P) + P/N}",
            "S of N equals 1 divided by the sum of 1 minus P and P over N"),
}
TEMPLATE = r"""\documentclass[border=1.5pt]{standalone}
\usepackage{amsmath,amssymb,xcolor}
\definecolor{ink}{HTML}{%s}
\begin{document}\color{ink}$\displaystyle %s$\end{document}
"""


def render(name, tex, color="1A202C", suffix=""):
    base = os.path.join(TMP, name + suffix)
    open(base + ".tex", "w").write(TEMPLATE % (color, tex))
    r = subprocess.run(["pdflatex", "-interaction=batchmode", "-halt-on-error", "-output-directory", TMP, base + ".tex"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("LATEX FAILED", name); print(open(base + ".log").read()[-800:]); sys.exit(1)
    subprocess.run(["pdftocairo", "-png", "-r", "500", "-transp", "-singlefile", base + ".pdf", os.path.join(OUT, name + suffix)], check=True)
    info = subprocess.run(["pdfinfo", base + ".pdf"], capture_output=True, text=True).stdout
    line = [l for l in info.splitlines() if l.startswith("Page size")][0].split()
    return float(line[2]), float(line[4])


man = {}
for name, (tex, alt) in F.items():
    w, h = render(name, tex)
    man[name] = {"w": w, "h": h, "alt": alt}
    render(name, tex, color="173A79", suffix="_navy")
json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
print(len(man), "formulas")
