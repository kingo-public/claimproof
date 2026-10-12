# Claimproof

> **Stops your AI agent from claiming success it cannot prove.**

An agent's report of success is a *claim*, not a *fact*. Claimproof forces every
"done", "fixed", "deployed", "tests pass", or "verified" to come with
reproducible evidence — a measurement, not a description.

## The problem

Agents report success confidently and wrongly. Not because they lie, but because
their instruments lie quietly:

- a test suite that was never run;
- a deploy that copied files but served stale bytes;
- a linter that greps a string and walks past the code that matters;
- a green check that means "something passed", not "the right thing passed".

Every existing verification tool asks **"is this true?"** Claimproof asks a
different question: **"could this claim have failed? If not, you have not
verified anything."**

## What it does

Before reporting completion, the agent emits a **Claim Receipt**:

```
DONE       What I claim is now true. One sentence, falsifiable.
MEASURED   The actual number / output / bytes. Not what I set. What I observed.
INSTRUMENT What measured it, plus the positive control proving it can see.
NEGATIVE   The deliberately-broken sample I ran, and that it went red.
BLIND      What I did NOT measure. Not "nothing" — name the gap.
FALSIFIER  What evidence would overturn the DONE line above.
```

If a field cannot be filled, **that is the finding** — the claim is marked
`UNVERIFIED` instead of being reported as success.

## Install

```bash
# user level (available in every project)
cp -r claimproof ~/.dsh/skills/claimproof

# or project level
cp -r claimproof <your-project>/.dsh/skills/claimproof
```

DSH discovers skills from the filesystem automatically — no restart needed.

## The checker

```bash
python3 scripts/check_claim.py report.md   # 0 PASS / 1 BLOCK / 2 UNVERIFIED
python3 scripts/self_test.py               # the negative-sample protocol
```

**What it can do:** reject a receipt that is hollow. Six `x` characters, a
field admitting "nothing was measured", or a `MEASURED` too thin to be an
observation all fail.

**What it cannot do:** prove a claim true. A confident, detailed, entirely
fabricated receipt passes. This is a floor against hollow reporting, not a
proof of correctness. Do not present a PASS as more than it is.

The checker is itself held to the rule it enforces. `self_test.py` runs nine
fixtures, including four that are **deliberately broken and must fail**.

Two real bugs were caught this way, both by deliberately-broken samples:

- a field regex using `\s` absorbed the next line as its value, so an empty
  `MEASURED` field reported PASS;
- version 1 accepted six `x` characters as a complete receipt — found by an
  adversarial review, which observed that a checker nobody can fail is the
  exact thing this skill warns about.

See `evals/README.md`.

Every check above — both self-tests and all ten translation pairs — runs in CI on
every push via `scripts/verify.py`. See `.github/workflows/verify.yml`.

## Intensity levels

| Level | Behaviour |
| --- | --- |
| `lite` | Append one `FALSIFIER:` line to completion claims. |
| `full` *(default)* | Full receipt, and run the negative sample when a check is involved. |
| `ultra` | Also hunt the counterexample *before* claiming — try to break your own work first. |

## Translations

| Language | README | Skill + references |
| --- | --- | --- |
| English *(canonical)* | this file | [SKILL.md](SKILL.md), [references/](references/) |
| 繁體中文 | [README.zh-Hant.md](README.zh-Hant.md) | [i18n/zh-Hant/](i18n/zh-Hant/) |
| 简体中文 | [README.zh-Hans.md](README.zh-Hans.md) | [i18n/zh-Hans/](i18n/zh-Hans/) |

DSH always loads the root `SKILL.md`. The `i18n/` files sit too deep to be
discovered as skills, so they can never create an ambiguous trigger. See
[i18n/README.md](i18n/README.md) for the translation policy and how dropped
content is detected.

Translations are checked for dropped content by `scripts/check_translations.py`,
which compares structure, numbers, and code blocks — and whose own self-test
proves it can fail.

## Layout

```
claimproof/
├── SKILL.md                       the skill itself (English, canonical)
├── README.md                      English
├── README.zh-Hant.md              繁體中文
├── README.zh-Hans.md              简体中文
├── LICENSE                        MIT
├── references/
│   ├── failure-modes.md           the nine shapes of a false report
│   ├── instrument.md              positive controls and why zeros prove nothing
│   └── negative-samples.md        the four-state protocol
├── scripts/
│   ├── check_claim.py             receipt checker
│   ├── self_test.py               nine-fixture regression protocol
│   └── check_translations.py      proves a translation dropped nothing
├── evals/
│   ├── README.md                  incl. the bugs the negative samples caught
│   └── fixtures/                  one fixture per state
└── i18n/
    ├── README.md                  translation policy
    ├── zh-Hant/                   繁體版 skill 與參考文件
    └── zh-Hans/                   简体版 skill 与参考文件
```

## Does it work?

Unknown, and partly measured. A two-agent experiment found that **claimproof
prevented no error** on a small pagination bug — both a control agent and a
claimproof agent found and fixed it. The measured difference was narrower: the
claimproof report stated what it had **not** verified, and was machine-checkable.

The same experiment also found that the checker **rejects an honest prose report**
that is entirely correct, because it grades format rather than truth. Read
[docs/comparison.md](docs/comparison.md) before trusting either result.

## The one rule

> **A check that cannot fail cannot verify.**

If you have never seen a check go red, you do not know that it is looking at
anything.

## License

MIT
