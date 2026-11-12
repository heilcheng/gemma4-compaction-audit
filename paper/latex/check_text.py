"""Fidelity check: does every draft sentence's first 40 chars appear in the PDF text?
Usage: uv run --with pypdf python check_text.py
"""
import re, sys, unicodedata
from pathlib import Path
from pypdf import PdfReader

here = Path(__file__).parent
draft = (here / "../draft.md").read_text()
pdf = " ".join(p.extract_text() for p in PdfReader(here / "main.pdf").pages)

def norm(s):
    s = unicodedata.normalize("NFKC", s)  # undoes fi/fl ligatures
    for a, b in {"‘": "'", "’": "'", "“": '"', "”": '"',
                 "−": "-", "‐": "-", "‑": "-"}.items():
        s = s.replace(a, b)
    s = s.replace("\\", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

body = draft.split("\n## References")[0]
body = "\n".join(l for l in body.splitlines()
                 if not l.startswith("#") and not l.startswith("|"))
body = re.sub(r"^Table 1\. ", "", body, flags=re.M)  # LaTeX numbers the caption itself
pdfn = norm(pdf).replace("- ", "-")  # pdf text may break lines after hyphens
pdfn_nospace = pdfn.replace(" ", "")
pdf_dehyph = norm(re.sub(r"-\n", "", pdf))  # join words hyphenated at line ends
pdf_dehyph_ns = pdf_dehyph.replace(" ", "")
sents = [norm(s) for s in re.split(r"\. |\n", body)]
sents = [s for s in sents if s]
missing, hyph = [], []
for s in sents:
    key = s[:40]
    if key in pdfn or key.replace(" ", "") in pdfn_nospace:
        continue
    if key in pdf_dehyph or key.replace(" ", "") in pdf_dehyph_ns:
        hyph.append(s)
    else:
        missing.append(s)
print(f"{len(sents)} sentences checked, {len(missing) + len(hyph)} missed on raw match, "
      f"{len(hyph)} explained by line-end hyphenation, {len(missing)} truly missing")
for m in hyph:
    print("  HYPHENATION:", m[:80])
for m in missing:
    print("  MISSING:", m[:80])
