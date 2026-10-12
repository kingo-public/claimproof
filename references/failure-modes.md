# The Nine Failure Modes

Every mode below produced a **confident, wrong report** that passed every
existing check. They are grouped by shape, not by domain — the same shape
reappears in tests, deploys, CSS, config, and prose.

Each entry: *the shape*, *how it appears*, and *a real occurrence with numbers*.

---

## 1. Setting is not measuring

**Shape.** A configuration value, environment variable, or declared intent is
read back as if it were an observation of behaviour.

**How it appears.**
- "Timeout is set to 5s" reported as "requests time out at 5s"
- Config says the feature is off, reported as "the feature is off"
- A variable named `currentVersion` is trusted as the served version

**Real occurrence — the config that was never loaded.**
> A soak test wrote its target directory into the config as `SOAK_DIR`.
> The report read the build identifier from that config and concluded the run
> exercised the intended build. The browser was in fact loading the *official*
> release. All **71** observed failures were measurements of the wrong artifact.
> The fix was to compare the **hash of the served content**, not the setting
> that was supposed to produce it.

**The repair.** Replace "I set X" with "I observed Y, and Y is derived from
the thing I care about." Where possible, make the setting and the measurement
*the same object*: derive a cache-busting token from the file hash instead of
maintaining a version number by hand. Then there is no number left to forget.

---

## 2. No positive control

**Shape.** A detector reports a clean result, but has never been shown to
detect a dirty one.

**How it appears.**
- A zero-packet capture is read as "nothing was sent"
- A monitor printing nothing is read as "no problems"
- A probe returning `null` is read as "the risky path was avoided"

**Real occurrence A — the filter that missed IPv6.**
> A packet capture filtered on an address list that omitted an IPv6 range.
> `curl https://google.com` succeeded, and the capture reported
> **0 packets**. The conclusion "no traffic left the machine" was nearly drawn
> from a filter that was structurally blind to the traffic in question. A
> positive control — capturing a request known to traverse that network — would
> have exposed it immediately.

**Real occurrence B — the probe with the wrong global.**
> A probe checked `window.__uploadConsent` to decide whether a consent
> gate was active. The real global had a different name, so the lookup was
> always `undefined`. The probe reported "consent gate not enforced" —
> an alarm about the product, caused entirely by the instrument.

**The repair.** Before trusting any negative result, run the instrument against
a case whose answer you already know. **A `0` without a positive control
is not evidence.**

---

## 3. No negative sample

**Shape.** A check exists and passes. Nothing has ever made it fail. You cannot
tell "it looked and found nothing wrong" apart from "it is not looking."

> "Without it, I would only know that *the check passed*. I would not know
> whether *the check was looking*."

**Real occurrence — the assertion that could never fire.**
> A gate promised to verify that a page title contained certain keywords. Its
> expression compared a value in a way that was true by construction. It
> reported PASS in every run, including runs where the title had been
> deliberately emptied. The gate had been green for weeks and had never tested
> anything.

**The repair.** Every check ships with a deliberately-broken sample, run in the
same invocation. Four states is a good default:

```
product currently    -> PASS   (the real case)
title emptied        -> FAIL   (broken sample 1)
keyword removed      -> FAIL   (broken sample 2)
wrong attribute used -> FAIL   (broken sample 3)
```

**A check that passes only because nothing broke it is a check you have not run.**

---

## 4. Green light is not correctness

**Shape.** A signal proves one property and is read as proving another.

| Signal | Actually proves | Often read as |
| --- | --- | --- |
| `HTTP 200` | the server is reachable | the right content was served |
| `syntax OK` | the file parses | the code does its job |
| `deploy exited 0` | the copy command ran | users now get the new version |
| `tests passed` | something asserted successfully | the right thing was tested |
| `file exists` | a path is occupied | the content is what you wrote |

**Real occurrence A — the lint that cannot see inline script.**
> `php -l` validates PHP and is **blind to inline script blocks**. A
> JavaScript syntax error inside inline script meant the entire page's JS was
> dead. The linter was green, the response was `HTTP 200`, the page
> rendered. Nothing was wrong except everything was broken.

**Real occurrence B — the hash match that proved both were stale.**
> A build artifact and its mirror had **identical hashes**. This was reported as
> "the change is live." Content assertions then ran and all three failed. The
> artifact was **32 seconds older** than the edit. The artifact and the mirror
> matched each other *because they had both expired together.* A hash
> comparison **cannot, by construction, detect that both sides are stale** —
> they are the same file.

**Real occurrence C — the version number maintained by hand.**
> A CSS change shipped without bumping a hardcoded version token. Users
> received the new HTML with the old stylesheet. The deploy succeeded by every
> available signal.

**The repair.** Assert the property you actually care about, separately. HTTP
200 **and** the expected bytes. Syntax valid **and** the function still
executes. Deployed **and** the served hash changed.

---

## 5. Weak relation sold as strong

**Shape.** A relationship that answers a weaker question is used where a
stronger one is needed. The weak relation is not merely less precise — on the
opposite input it gives **the opposite answer**.

| Weak relation | Reads as | Cannot see |
| --- | --- | --- |
| `a != b` | "a is newer" | which side is newer |
| `prefix(l, 46)` | "same identifier" | two rows sharing a prefix |
| `substring present` | "the content is there" | content moved elsewhere |
| `timestamp set` | "this is fresh" | freshness |
| `grep found keyword` | "the feature exists" | a comment mentioning it |

**Real occurrence A — the reversed comparison.**
> A staleness check compared three timestamps with `!==`, reporting
> "there is a newer version." `!==` only knows *different*, not
> *newer*. When the new value was in fact **older**, the check confidently
> reported the reverse. Nothing crashed. The page returned 200, the numbers all
> looked plausible, and **no gate lit up.** It was found only by printing the
> three timestamps side by side.
> The single line gated **seven** user-visible outputs. Fixing the *comparison*
> corrected all seven; fixing the *wording* would have needed seven edits and
> left the bug in place.

**Real occurrence B — the prefix collision.**
> Lines were keyed by their first 46 characters to restore a file. Two lines
> from the same path shared a 46-character prefix, so one silently overwrote the
> other. The output proudly reported "restored 30 lines" — which was true, and
> wrong.

**Real occurrence C — the grep that counted comments.**
> `grep -o '!important'` was used to count declarations. It counted
> **298**; the real number was **291**. It was matching occurrences inside source
> comments and documentation. The pattern appears in the code that *describes*
> the pattern.

**The repair.** Ask what the weaker relation does on the *opposite* input. If it
gives a confidently wrong answer rather than no answer, it is the wrong
relation. Use position or full content for identity. Use `>` for
ordering. Match rendered text for content, not source text.

---

## 6. Measuring the wrong object

**Shape.** A property of A is used as a proxy for a property of B. The proxy is
reasonable until it silently stops tracking.

**How it appears.**
- Measuring an element's own box when the clickable area is a pseudo-element
- Measuring a container's bounds when visibility depends on the viewport
- Measuring a file on disk when the question is what the server serves
- Measuring bytes when the label says characters, or the reverse

**Real occurrence A — the clickable area that was not the element.**
> Touch-target size was measured on the anchor element itself. The actual
> clickable region came from an absolutely-positioned pseudo-element covering
> it. The measurement was of the wrong rectangle, and failed accessibility
> checks for a control that actually met them.

**Real occurrence B — the container that was not the viewport.**
> Content was judged "clipped" by comparing element bounds against a *scroll
> container*. The elements were fixed-position and fully visible on screen.
> Measuring the container produced systematic false positives — this was the
> fourth instance that day of "taking A's property to stand for B."

**Real occurrence C — the frozen animation.**
> A bounding rectangle was measured on an element mid-animation and reported as
> its layout position. Every reading was a moment, not a position. Worse: the
> attempted freeze using a universal selector with `!important` **does
> not work** against an animation that is itself `!important`, because
> the universal selector has specificity (0,0,0) and loses to a class (0,1,0).
> The freeze was asserted as "done" without being verified as "effective."

**The repair.** Before measuring, ask: *does this number correspond to the thing
the user experiences?* State the mapping explicitly. Where two objects are
involved, measure both and report the gap.

---

## 7. Silence read as success

**Shape.** An error is swallowed, so "the instrument is broken" presents as
"everything is fine."

```
// turns "my probe is broken" into "the system is clean"
child.on('error', () => {});
await doThing().catch(() => {});
```

**Real occurrence — the port that was already taken.**
> A test harness bound a **fixed port** and attached an empty error handler. A
> leftover server from a previous run already held the port. The spawn failed
> *silently*; the harness connected to the old server and served the wrong
> directory. The entire run — **71** failing observations — measured an artifact
> that had nothing to do with the code under test.

**The repair.** Never swallow. When a result is "all failures" or "zero
observations," your first question is:

> **Is this zero caused by my instrument, or by the subject?
> If I cannot tell, my instrument is not reporting its own failure — fix the
> instrument.**

---

## 8. A gate nobody runs is not a gate

**Shape.** A check exists in the repository, is correct, and is never invoked.

**How it appears.**
- A script written but never wired into CI or a timer
- A timer defined but whose start path lacks the execute bit
- A "self-test" promised in documentation that does not exist in the code

**Real occurrence — the promise living in the rulebook.**
> A conventions file claimed a checker shipped with "six control cases." The
> checker contained no self-test at all. The claim had been copied into three
> backup files before anyone noticed. **The promise lived on the rule file
> itself** — the document everyone trusted to describe reality.

**The repair.** For each check, answer: *if no one remembers to run it, will it
still run?* If not, it is a comment. Wire static checks to a timer; wire dynamic
checks to the change that makes them relevant. Then verify the wiring by
**waiting for it to fire once** — a declared timer is a setting, not an
observation.

---

## 9. A wrong gate is worse than no gate

**Shape.** A check reports failures for correct work. It trains people to ignore
it, and sends them to fix things that were never broken.

**Real occurrence A — SIGPIPE misread as failure.**
```
set -o pipefail
curl -s "$url" | grep -q "expected"    # reports FAILURE on success
```
> `grep -q` exits as soon as it matches. `curl` receives
> SIGPIPE and dies with exit 141. `pipefail` propagates that as
> failure. The check reports a failure for a page that served exactly the
> expected content. **Fix: write the response to a file first, then grep the
> file. No pipeline, no SIGPIPE.**

**Real occurrence B — the exit code used as a value.**
```
code=$(... | grep -c X || echo 0)     # prints TWO zeroes when not found
[ "$code" = "0" ]                     # fails: two zeroes != one zero
```
> Correct work reported as broken, again. The repair is to separate the value
> from the exit status.

**The repair.** When relaxing a rule to silence a false positive, you must add
an **escape-hatch sample** — a deliberately-broken input proving the relaxed
rule still catches the real violation. **Without it, "relaxed" and "removed"
look identical.**

---

## Cross-cutting: the never-executed failure path

Not a mode of its own, but the reason modes 3, 8 and 9 persist:

> The success path runs every day. The failure path may **never have run at
> all** — and the failure path is the entire reason the check exists.

Run it. Once, by hand, deliberately. Then record that you did.

---

## How to use this document

When you are about to report success, scan the nine shapes:

1. Am I reporting a setting as a measurement?
2. Has my instrument seen a known-positive case?
3. Has my check ever gone red?
4. Does my green signal prove the property I am claiming?
5. Is any comparison weaker than the question it answers?
6. Am I measuring the object the user actually experiences?
7. Is any error being silently swallowed between me and the reading?
8. Will this check run when I am not here?
9. Has this check ever cried wolf?
