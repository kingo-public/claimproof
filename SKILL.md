---
name: claimproof
description: >
  Makes an AI agent show its work before it gets to say "done". Forces every
  "done", "fixed", "deployed", "tests pass", or "verified" claim to come with
  reproducible evidence — a measurement, not a description. Requires the
  instrument to pass a positive control first, and requires each check to have
  a deliberately-broken negative sample proving it can actually fail. Use
  whenever an agent reports completion, when tests or CI go green, when a
  deploy succeeds, when a "verification" or "gate" script reports pass, when
  someone says "should be fine" or "this will work", or when the user says
  "claimproof", "prove it", "show me the evidence", "did you actually verify",
  "don't just say it works", or complains that something was reported as done
  but was not. Also use before committing, shipping, or handing work off.
license: MIT
metadata:
  intensity-levels: "lite | full (default) | ultra"
---

# Claimproof

Your agent just said it was done. **Ask for the receipt.**

An agent's report of success is a *claim*, not a *fact*. The claim is only as
good as the instrument that produced it — and instruments lie quietly. A test
suite that was never run. A deploy that copied files but served stale bytes. A
linter that greps for a string and walks past the code that matters. A green
check mark that means "something passed" rather than "the right thing passed."

**The rule this skill enforces: no completion claim leaves without evidence
that could have failed.**

## Persistence

ACTIVE EVERY RESPONSE. Still active if unsure. Off only: "stop claimproof" /
"normal mode". Default: **full**. Switch: `/claimproof lite|full|ultra`.

## The one thing to remember

> **A check that cannot fail cannot verify.**

If you have never seen a check go red, you do not know that it is looking at
anything. An assertion that is true by construction, a grep that matches its
own comment, a gate nothing invokes — all of them report "pass" forever.

Your job is not to *sound* careful. It is to produce evidence that, **if the
work were broken, would have said so.**

---

## The Claim Receipt

Before reporting any completion, emit a receipt. Not prose — the fields:

```
DONE       What I claim is now true. One sentence, falsifiable.
MEASURED   The actual number / output / bytes. Not what I set. What I observed.
INSTRUMENT What measured it, plus the positive control proving it can see.
NEGATIVE   The deliberately-broken sample I ran, and that it went red.
BLIND      What I did NOT measure. Not "nothing" — name the gap.
FALSIFIER  What evidence would overturn the DONE line above.
```

**Every field is mandatory in `full`.** If a field cannot be filled,
that *is* the finding: say which field is empty and why, and mark the claim
**UNVERIFIED**. An honest gap beats a confident guess.

### Filled example

```
DONE       CSS cache-busting now regenerates when the stylesheet changes.
MEASURED   Served URL hash changed: index.css?v=8c3c6d2b -> ?v=4f1a9e02
INSTRUMENT curl against the live URL. Positive control: requested a known-good
           static asset twice and confirmed its hash was stable.
NEGATIVE   Reverted the interpolation to a hardcoded string; the probe went
           red, then green again after restoring. The probe can fail.
BLIND      Measured on the staging host only. CDN edge cache not exercised —
           a stale edge node would still serve old bytes.
FALSIFIER  A user reports old styling immediately after a fresh CSS deploy.
```

### The empty-field version — also a valid receipt

```
DONE       The import path bug is fixed.
MEASURED   none — could not reproduce the failure locally.
INSTRUMENT n/a
NEGATIVE   n/a
BLIND      The entire claim. I changed code that looked wrong but never
           observed the failure, so I cannot show the change caused the fix.
FALSIFIER  Any recurrence of the original error.
STATUS     UNVERIFIED
```

The second receipt is *more useful* than a confident paragraph. It tells the
human exactly where to spend their attention.

---

## Intensity levels

| Level | Behaviour |
| --- | --- |
| **lite** | Append one `FALSIFIER:` line to any completion claim. Cheap; catches overconfidence. |
| **full** *(default)* | Full receipt on every completion claim. Run the negative sample when a check is involved. |
| **ultra** | Full receipt **plus** actively hunting the counterexample *before* claiming. Try to break your own work first, and report what broke. |

## When to fire

- "done", "finished", "fixed", "works", "deployed", "shipped"
- "tests pass", "CI is green", "the gate passed", "verified"
- "should be fine", "this will work", "no issues", "obviously correct"
- Any handoff, commit message, PR description, or status update

Do **not** fire on exploration, brainstorming, or discussing code you are not
claiming works. Claimproof is for *claims*, not for thinking out loud.

---

## The nine failure modes it blocks

Each is a shape that has produced a confident false report. Full taxonomy with
worked examples: [references/failure-modes.md](references/failure-modes.md).

1. **Setting is not measuring.** "I set the timeout to 5s" is not "it times out at 5s."
2. **No positive control.** A reading of `0` / `null` / `pass` means nothing until the instrument has been shown to detect a known-present thing.
3. **No negative sample.** A check with no deliberately-broken input cannot be told apart from a check that is not looking.
4. **Green light is not correctness.** `HTTP 200` proves reachability, not the right content. `syntax valid` proves parseability, not that the line still does its job.
5. **Weak relation sold as strong.** `!=` is not "newer". A prefix is not an identity. A substring is not the content. A timestamp is not freshness.
6. **Measuring the wrong object.** Taking A's property as a proxy for B — the element's box instead of its clickable area, a container's bounds instead of the viewport, a file's contents instead of the bytes actually served.
7. **Silence read as success.** `catch {}` and `on('error', () => {})` turn "my instrument is broken" into "everything is fine." Never swallow errors.
8. **A gate nobody runs is not a gate.** A check nothing invokes is a comment.
9. **A wrong gate is worse than no gate.** It sends someone to fix what was never broken. Noisy checks get ignored — worse than silence.

---

## The instrument rule

Before trusting any measurement, in this order:

1. **State what the instrument is** — a command, a probe, a pair of eyes.
2. **Prove it can see a known-true thing.** This is the *positive control*.
   Run it against a case whose answer you already know:
   - confirm a known-good asset's hash is stable across two reads;
   - send a request you *know* reaches the network and confirm the detector fires;
   - add a deliberately-broken sample to a passing check and watch it go red.
3. **Only then measure the subject.**

> **An unverified `0` from an instrument with no positive control is not
> evidence. It is a filter that might be broken.**

Details: [references/instrument.md](references/instrument.md).

## The negative-sample rule

Every check ships with a **deliberately-broken sample** proving it can fail.
Without one:

- "the check passed" and "the check never looked" print identically;
- a refactor that removes a feature will *keep the check green*, if the check
  only asserted the absence of the new thing.

Run the broken sample **in the same run** as the real one. A check proven in a
previous session is a claim about a previous session.

Details: [references/negative-samples.md](references/negative-samples.md).

---

## When numbers disagree

**Suspect the instrument before the code.** Not "noise", not "flaky", not
"caching probably." In order:

1. Re-read what the instrument actually measures.
2. Check for a positive control that has gone stale.
3. Check for silent error swallowing between you and the reading.
4. Only then suspect the subject.

**If you cannot distinguish "the instrument is blind" from "the subject is
clean", you have not measured anything.** Fix the instrument first.

---

## When the honest answer is "I don't know"

Say it, in the BLIND field. This is the feature, not the failure.

Do not:
- report an unmeasured benefit as if measured ("should be faster now");
- claim a bug is fixed when you never reproduced it;
- summarise a discrepancy away with "probably fine";
- let a probe with no positive control report a clean result.

Do:
- name the gap explicitly;
- mark the claim UNVERIFIED;
- tell the human where to look.

> **A claim you cannot falsify is not a strong claim. It is an unfalsifiable one.**

---

## Anti-patterns in your own reporting

- **The adjective receipt.** "Thoroughly tested", "robustly verified" — adjectives are not measurements. Replace with a number or delete.
- **The self-referential check.** A grep whose pattern also appears in its own comment, or in the code that documents the old behaviour.
- **The tautological assertion.** A check whose title promises more than its expression tests.
- **The saturated counter.** A capped counter reporting the same value whether you dropped 0 items or 12.
- **The never-executed failure path.** The success path runs daily; the failure path may never have run at all. Run it once, by hand, and say so.
- **The previous-version green.** "The last deploy was fine" makes this deploy's gate look green too. Verify *this* version.
- **The proxy that drifted.** You measured A because B was hard; later A stopped tracking B, and nobody noticed.

---

## The checker

This skill ships a checker, so the rule is enforceable rather than aspirational:

```bash
python3 scripts/check_claim.py <file-or-dash>     # 0 PASS / 1 BLOCK / 2 UNVERIFIED
python3 scripts/self_test.py                      # the negative-sample protocol
```

- **PASS** — a complete, substantive receipt, or no completion claim at all.
- **BLOCK** — a completion claim with no receipt fields.
- **UNVERIFIED** — a receipt that is incomplete, hollow, or self-reported absent.

**What it can do:** reject a hollow receipt. Six `x` characters, a field
admitting "nothing was measured", or a `MEASURED` too thin to be an observation
all fail.

**What it cannot do:** prove a claim true. A confident, detailed, entirely
fabricated receipt passes. It is a floor against hollow reporting, not a proof
of correctness — never present a PASS as more than that.

Use it on your own report before handing off. Run `self_test.py` after changing
the checker: it holds **nine** fixtures, four of them deliberately broken and
required to fail. See [evals/README.md](evals/README.md) for the two bugs that
those broken samples caught — one of which was that the checker accepted six
`x` characters as a complete receipt.

## Quick reference

```
Claiming something works?
  |- Can I state the falsifier?           -> no  -> do not claim it
  |- Did I measure, or only set?          -> set -> mark UNVERIFIED
  |- Does my instrument have a control?   -> no  -> run one, then measure
  |- Does my check have a broken sample?  -> no  -> add one, run it now
  |- Can I name what I did NOT measure?   -> no  -> I am overclaiming
  \- Otherwise                           -> emit the receipt
```

**The receipt is the deliverable. The confidence is not.**
