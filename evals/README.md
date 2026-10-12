# Evals

These fixtures are the negative-sample protocol for `scripts/check_claim.py`.
They exist so the checker can be shown to **fail** — not just to pass.

## Run

```bash
python3 scripts/self_test.py
```

Expected: nine states matched, plus a self-check that the harness can detect a
wrong expectation. Exit 0.

## The nine fixtures

| Fixture | Expected | Exit | Guards against |
| --- | --- | --- | --- |
| `01_no_receipt.txt` | BLOCK | 1 | A completion claim with no receipt at all. The common case. |
| `02_full_receipt.txt` | PASS | 0 | A complete, substantive receipt. The good case. |
| `03_empty_field.txt` | UNVERIFIED | 2 | A receipt whose MEASURED field is empty. |
| `04_no_claim.txt` | PASS | 0 | No completion claim — nothing to receipt. |
| `05_all_x_fields.txt` | UNVERIFIED | 2 | Six `x` characters. **Bug 1.** |
| `06_self_admitted_fake.txt` | UNVERIFIED | 2 | A receipt admitting nothing was measured. **Bug 1.** |
| `07_descriptive_prose.txt` | PASS | 0 | Does not fire on exploration or description. |
| `08_thin_measured.txt` | UNVERIFIED | 2 | A MEASURED field too thin to be a reading. |
| `09_good_receipt_2.txt` | PASS | 0 | A second good receipt, different domain — resists overfitting. |

Fixture 04 and 07 matter as much as the others: a checker that flags
*everything* is a wrong gate, and a wrong gate gets ignored.

---

## Bug 1 — the checker that did not check

The first version validated only that each field was non-empty. It therefore
passed:

```
DONE       x
MEASURED   x
INSTRUMENT x
NEGATIVE   x
BLIND      x
FALSIFIER  x
```

— with exit 0 and the message "complete receipt covering all six fields". It
also passed a receipt whose BLIND field read *"Everything. I have no evidence
whatsoever."*

Worse, it passed `SKILL.md`'s own documented example of an UNVERIFIED
receipt — the file said UNVERIFIED, the checker said complete. The example was
making a promise the tooling did not keep.

**How it was found:** an adversarial review, whose brief was to break the skill
rather than praise it. It did not read the code and reason about it; it fed the
checker six `x` characters and reported the exit code.

**Why it mattered:** a checker nobody can fail is precisely what `SKILL.md` warns
about in failure mode 8 — *a gate nobody runs is not a gate*. This one ran, and
still gated nothing.

**The fix:** classify each field value as empty / filler / absence / substantive,
and treat a self-declared UNVERIFIED as authoritative. Fixtures 05 and 06 are
the regression lines.

---

## Bug 2 — the regex that ate the next line

The first version reported **PASS** on `03_empty_field.txt`, whose MEASURED
field was blank.

It used `\s*` for intra-line whitespace:

```python
r"^\s*" + field + r"\s*:?\s*(.*)$"
```

Told to match against:

```
MEASURED   
INSTRUMENT n/a
```

the `\s*` after MEASURED consumed the trailing spaces **and the newline**, so
the capture group took `INSTRUMENT n/a` as the value of MEASURED. The field was
never empty.

**The fix:** use `[ \t]` instead of `\s` for whitespace that must stay on one
line.

**A second bug found the same way, later:** the value classifier accepted
`INSTRUMENT n/a` and `NEGATIVE n/a` as valid content in the empty-field
fixture, because the absence patterns were anchored too tightly. Fixture 03 now
expects those to be reported as content-free.

---

## Adding a fixture

1. Add the `.txt` to `evals/fixtures/`.
2. Add its expected status and exit code to `CASES` in `scripts/self_test.py`.
3. Run `python3 scripts/self_test.py`.
4. If it fails, fix the **checker**, not the expectation — unless you can argue
   the expectation was wrong, in which case say so explicitly.

## What these fixtures do not prove

They prove the checker **discriminates**. They do not prove it is **right**
about any particular claim, and they do not prove an agent will stop overclaiming
once the skill is loaded. That last question can only be answered by watching
real runs — it cannot be read off these files.

---

## The CI gate is itself proven to fail

`scripts/verify.py` runs the self-tests and all ten translation pairs. A gate that
only ever passes is the thing this project warns about, so it was tested with
two corruptions, each in a throwaway copy of the repository:

| Corruption | Expected | Observed |
| --- | --- | --- |
| A translated number changed (298 to 297 in one file) | verify exits 1 | `VERIFY EXIT=1` |
| Fixture 01 rewritten so it no longer contains a claim | verify exits 1 | `VERIFY EXIT=1` |
| Clean repository (baseline) | verify exits 0 | `VERIFY EXIT=0` |

### The first attempt at this test proved nothing

The first two corruptions were **silent no-ops**, and verify passed — correctly,
because nothing had actually been broken:

1. The number 298 was changed in `i18n/zh-Hant/SKILL.md`, but 298 appears in
   `references/failure-modes.md`, not in SKILL.md. The edit matched nothing.
2. Fixture 01 was edited by replacing the words "fixed" and "validates" — but
   the phrase "tests pass" remained, and that is a claim pattern. The fixture was
   still a valid no-receipt sample, so BLOCK was still correct.

A third error was made while reading the result: piping verify.py into tail and
then reading the exit code captures the exit code of tail, not of the checker.
That is failure mode 9 from `references/failure-modes.md` — the SIGPIPE and pipeline
trap documented there, reproduced by the person who wrote the documentation.

The rule this illustrates: **verify that your negative sample actually changed
the observed value before you conclude the check works.** A no-op sample proves
nothing, and it looks exactly like a passing check.
