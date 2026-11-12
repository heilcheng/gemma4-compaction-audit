"""Build paper/latex/main.tex from paper/draft.md.

The preamble, the table and the figure blocks live here; every paragraph of
prose comes from the draft, so the PDF and the Writeup carry the same text.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

PREAMBLE = r"""\documentclass[11pt,a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=1in]{geometry}
\usepackage{microtype}
\usepackage{booktabs}
\usepackage{array}
\usepackage{graphicx}
\renewcommand{\topfraction}{0.88}
\renewcommand{\textfraction}{0.1}
\renewcommand{\floatpagefraction}{0.85}
\usepackage[authoryear,round]{natbib}
\usepackage[colorlinks=true,linkcolor=black,citecolor=black,urlcolor=black]{hyperref}

\graphicspath{{../../figures/}}
\emergencystretch=2em

\title{%s}
\author{Hailey H. L. Cheng\\Columbia University\\Submission topic: Tasks and Benchmarks.}
\date{November 2026}

\begin{document}
\maketitle
"""

CITES = [
    ("(Google DeepMind, 2026)", r"\citep{deepmind2026}"),
    ("Lindenbauer et al. (2025)", r"\citet{lindenbauer2025}"),
    ("Salle et al. (2026)", r"\citet{salle2026}"),
    ("(Zheng et al., 2026)", r"\citep{zheng2026}"),
    ("Gao et al. (2026)", r"\citet{gao2026}"),
    ("(Hsu et al., 2026)", r"\citep{hsu2026}"),
    ("(Tiwari et al., 2026)", r"\citep{tiwari2026}"),
    ("(Wang et al., 2026)", r"\citep{wang2026}"),
    ("Miller (2024)", r"\citet{miller2024}"),
    ("Madaan et al. (2024)", r"\citet{madaan2024}"),
    ("Bjarnason et al. (2026)", r"\citet{bjarnason2026}"),
    ("(Yang et al., 2024)", r"\citep{yang2024}"),
    ("(Kwon et al., 2023)", r"\citep{kwon2023}"),
    ("(Jimenez et al., 2024; Chowdhury et al., 2024)", r"\citep{jimenez2024,chowdhury2024}"),
]

# Literal strings set in typewriter type, with break points after / and -.
MONO = [
    "google/gemma-4-12B-it-qat-w4a16-ct",
    "logs/actions/*.jsonl.gz",
    "github.com/heilcheng/gemma4-compaction-audit",
    "results/",
    "logs/diag",
]

RUN_IN = ["Compaction policies.", "Stale evidence and its labelling.", "Testing and noise."]

FIGS = {1: "overview", 2: "diff", 3: "flips", 4: "funnel", 5: "stall"}


def figure(name, width, label, caption):
    return (
        "\\begin{figure}[t]\n\\centering\n\\includegraphics[width=%s]{%s.pdf}\n"
        "\\caption{%s}\n\\label{fig:%s}\n\\end{figure}\n" % (width, name, caption, label)
    )


def table(rows, caption):
    out = [
        r"\begin{table}[tbp]", r"\centering", r"\footnotesize", r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lrrrlcrr>{\raggedleft\arraybackslash}p{2.4cm}}",
        r"\toprule",
    ]
    for k, row in enumerate(rows):
        cells = [c.strip().replace("%", r"\%") for c in row.strip().strip("|").split("|")]
        out.append(" & ".join(cells) + r" \\")
        if k == 0:
            out.append(r"\midrule")
    out += [r"\bottomrule", r"\end{tabular*}", "\\caption{%s}" % caption, r"\label{tab:main}", r"\end{table}", ""]
    return "\n".join(out)


def mono(s):
    body = s.replace("/", "/\\allowbreak ").replace("-", "-\\allowbreak ").rstrip()
    if body.endswith("\\allowbreak"):
        body = body[: -len("\\allowbreak")].rstrip()
    return "\\texttt{" + body + "}"


def tex(p):
    for a, b in CITES:
        p = p.replace(a, b)
    held = []
    for m in MONO:
        if m in p:
            held.append(mono(m))
            p = p.replace(m, "@@%d@@" % (len(held) - 1))
    p = p.replace("#", r"\#").replace("%", r"\%")
    p = re.sub(r'"([^"]*)"', r"``\1''", p)
    p = re.sub(r"\bp = (0\.\d+)", r"$p = \1$", p)
    p = re.sub(r"Figure (\d)", lambda m: "Figure~\\ref{fig:%s}" % FIGS[int(m.group(1))], p)
    p = p.replace("Table 1", "Table~\\ref{tab:main}")
    for head in RUN_IN:
        if p.startswith(head):
            p = "\\textbf{%s}" % head + p[len(head):]
    for k, h in enumerate(held):
        p = p.replace("@@%d@@" % k, h)
    return p


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("mw", ROOT / "scripts" / "make_writeup.py")
    mw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mw)
    caps = {n: tex(c[1]) for n, c in mw.CAPTIONS.items()}
    widths = {1: r"\textwidth", 2: r"0.95\textwidth", 3: r"0.6\textwidth", 4: r"0.85\textwidth", 5: r"\textwidth"}
    files = {n: c[0].rsplit(".", 1)[0] for n, c in mw.CAPTIONS.items()}

    draft = (ROOT / "paper" / "draft.md").read_text().split("## References")[0]
    paras = [b.strip() for b in draft.split("\n\n") if b.strip()]
    out = [PREAMBLE % paras[0].lstrip("# ").strip()]
    k = 1
    while k < len(paras):
        p = paras[k]
        k += 1
        if p == "## Abstract":
            out.append("\\begin{abstract}\n%s\n\\end{abstract}\n" % tex(paras[k]))
            k += 1
        elif p.startswith("## "):
            out.append("\\section{%s}\n" % p[3:])
        elif p.startswith("|"):
            caption = tex(paras[k]).split(". ", 1)[1]
            k += 1
            out.append(table([r for r in p.split("\n") if not r.startswith("|---")], caption))
            out.append(figure(files[2], widths[2], FIGS[2], caps[2]))
        elif p.startswith("Use of AI tools:"):
            out.append("\\bigskip\n\\noindent " + tex(p) + "\n")
        else:
            if p.startswith("Figure 1 summarises"):
                out.append(figure(files[1], widths[1], FIGS[1], caps[1]))
            out.append(tex(p) + "\n")
            for n, start in ((3, "Rerunning flat with a new seed"), (4, "Window logging in the replicate"), (5, "Replies with no command.")):
                if p.startswith(start):
                    out.append(figure(files[n], widths[n], FIGS[n], caps[n]))
    out.append("\\bibliographystyle{plainnat}\n\\bibliography{refs}\n\n\\end{document}\n")
    (ROOT / "paper" / "latex" / "main.tex").write_text("\n".join(out))
    print("wrote paper/latex/main.tex")


if __name__ == "__main__":
    main()
