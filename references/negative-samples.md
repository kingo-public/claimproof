# Negative Samples

A negative sample is **a deliberately-broken input fed to a working check, to
prove the check can go red.**

Without one, you cannot distinguish two very different worlds:

| World | What you observe | What is true |
| --- | --- | --- |
| A | the check passes | the subject is correct |
| B | the check passes | **the check is not looking at anything** |

A and B produce **identical output**. Only a negative sample separates them.

## Contents

- [1. The core claim](#1-the-core-claim)
- [2. What counts as a negative sample](#2-what-counts-as-a-negative-sample)
- [3. The four-state protocol](#3-the-four-state-protocol)
- [4. Special case: assertions that cannot fail](#4-special-case-assertions-that-cannot-fail)
- [5. Relaxing a check without deleting it](#5-relaxing-a-check-without-deleting-it)
- [6. Common mistakes](#6-common-mistakes)

---

## 1. The core claim

> **A check that has never failed has not been shown to check anything.**

This is not a philosophical point. A check is a filter. A filter that passes
everything is indistinguishable from no filter. The negative sample is how you
demonstrate the filter has a cutoff.

Three real shapes that violate this:

1. **The tautology.** An assertion comparing a value to itself, or to a
   constant that makes it true by construction. Reported PASS for weeks.
2. **The self-referential search.** A text search whose pattern also appears in
   its own comment, or in the documentation describing the old behaviour. It
   matches the description, not the thing.
3. **The absent-feature check.** A refactor deletes feature X. The check only
   asserted "X is not present", so it stays green — and now it passes for the
   wrong reason forever.

## 2. What counts as a negative sample

A negative sample is any input that **should** make the check fail. Good ones:

- **Emptied content.** Replace the real title with an empty string.
- **Reversed ordering.** Give the check values in the wrong order.
- **Wrong identifier.** Feed a similar-but-different key.
- **Removed element.** Delete the thing the check claims to find.
- **Corrupted value.** Introduce a subtle syntax error.
- **Boundary input.** Off-by-one, empty collection, single element.

Bad negative samples (these prove nothing):

- Something so broken the check fails for an unrelated reason (a crash, a
  missing file) — you have proven the check errors, not that it discriminates.
- A sample run in a *different session* than the real one.
- A sample you wrote but never executed.

## 3. The four-state protocol

Run all four **in the same invocation**, and print all four outcomes:

```
STATE                EXPECTED   PURPOSE
product as-is        PASS       the real case
negative sample 1    FAIL       proves the check discriminates
negative sample 2    FAIL       proves it is not keyed to one property
restore product      PASS       proves the negative did not corrupt state
```

The fourth state matters more than people expect: it proves the failure you
observed came from your sample and not from a side effect of running the check.

### Example: a check that a page title contains keywords

```
input                        expected   observed
wc -c <<< "$title"  > 0      PASS       PASS      (real)
title=""                     FAIL       FAIL      (empty)
title="wrong text"           FAIL       FAIL      (no keywords)
title back to original       PASS       PASS      (restored)
```

Before this protocol existed, the check reported PASS on row 2 as well — which
was the finding.

## 4. Special case: assertions that cannot fail

These are the highest-value negative samples, because these assertions look
healthy. Symptoms:

- the same boolean constant appears on both sides of a comparison;
- the searched string appears in the code performing the search;
- the check tests a property that the code sets unconditionally;
- the counter is capped, so it reports the same value whether you dropped 0 or
  12 items;
- the assertion title promises more than the expression tests.

**A mismatch between an assertion's title and its expression is itself a bug.**
The title is what humans read; if it overclaims, the check is documentation that
lies.

## 5. Relaxing a check without deleting it

When a check cries wolf, the tempting fix is to loosen it. Done carelessly,
"loosened" and "deleted" become the same thing.

**Every relaxation requires an escape-hatch sample**: a deliberately-broken
input proving the *relaxed* rule still catches the real violation.

```
RULE (old, false-positive on legitimate work)   -> relax
REAL VIOLATION (must still fail)               -> proves the rule survives
FALSE POSITIVE (must now pass)                 -> proves the noise is gone
```

If you cannot construct the "real violation" row, you have not relaxed the rule;
you have removed it. Say so explicitly rather than leaving a check that appears
to work.

## 6. Common mistakes

- **Proving it once, in a previous run.** A control established last week is a
  claim about last week. Re-run it in the same session as the claim.
- **A negative sample that shares the bug.** If your broken sample is broken in
  the same way the real input would be, it proves nothing new.
- **Testing the mock.** Confirming that your test double behaves as written,
  rather than that the real integration works.
- **Confusing "the check failed" with "the check works".** The check must fail
  on the broken input *and pass on the good one*. One without the other is
  half a protocol.
- **Silent skip.** A check skipped due to a missing dependency reports nothing,
  and nothing looks like success. Make skips loud.

---

## The rule

> **Every check ships with a deliberately-broken sample, run in the same
> invocation, and the result printed.**

If a check cannot have one, say so and mark it **UNVERIFIED** — do not let it
report PASS as if it had been tested.