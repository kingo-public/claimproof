# The Instrument Rule

A measurement is only as trustworthy as the device that produced it. This
document defines what it takes to trust a reading.

## Contents

- [1. What counts as an instrument](#1-what-counts-as-an-instrument)
- [2. The positive control](#2-the-positive-control)
- [3. Why a bare zero proves nothing](#3-why-a-bare-zero-proves-nothing)
- [4. Instrument failure signatures](#4-instrument-failure-signatures)
- [5. When to distrust a clean result](#5-when-to-distrust-a-clean-result)
- [6. Worked protocol](#6-worked-protocol)

---

## 1. What counts as an instrument

Anything that produces a reading you intend to rely on:

- a shell command (`curl`, `grep`, `md5sum`)
- a test runner or linter
- a probe inside a browser or a test harness
- a monitor, a log, a dashboard
- **your own eyes on a screenshot**

Naming the instrument matters, because every one of them can be blind. "It
returned nothing" is a statement about the instrument before it is a statement
about the world.

## 2. The positive control

**The positive control is a case where you already know the answer, run through
the same instrument, in the same session.**

It answers one question: *can this instrument see the thing at all?*

| Situation | Positive control |
| --- | --- |
| Checking that no traffic leaves the machine | send a request you *know* goes to the network; confirm the detector fires |
| Checking that a CSS rule is gone | search for a string you *know* is present; confirm a non-zero hit |
| Checking that a page renders | load a page with a *known* visible element; confirm your probe finds it |
| Checking that a deploy served new bytes | request an unchanged asset; confirm its hash is stable across two reads |
| Checking that a gate can fail | feed it a deliberately broken input; confirm it goes red |

Without a positive control, a clean reading has two indistinguishable causes:

1. the subject is clean, or
2. **the instrument is blind.**

You cannot act on a reading you cannot interpret.

## 3. Why a bare zero proves nothing

A reading of `0`, `null`, `empty`, or `pass` is the most dangerous output an
instrument can produce, because it is also exactly what a broken instrument
produces.

> **An unverified zero is not evidence. It is a filter that might be broken.**

This is the single most common way a confident false report is born. The full
mode list lives in [failure-modes.md](failure-modes.md); modes 2 and 7 are this
one wearing different clothes.

## 4. Instrument failure signatures

Learn these. They all look like good news.

| Signature | What it usually means |
| --- | --- |
| Everything fails, including things that cannot fail | the instrument is broken, not the subject |
| Zero observations in a run that should have produced many | a filter, port, or path is wrong |
| A reading that never varies across runs | the probe is reading something constant, not the subject |
| The same value on valid and broken input | the assertion is true by construction |
| A pass that returns instantly on a slow operation | the work was skipped |
| An error about connections, files, or flakiness | check the instrument before believing the diagnosis |

## 5. When to distrust a clean result

Distrust a clean result — and go run a positive control — whenever:

- it arrived faster than expected;
- it contradicts a human report;
- nobody has seen this check fail recently;
- it is the first time this check has run against this version;
- the subject changed but the reading did not;
- the instrument was recently edited by you or by an agent.

That last one deserves its own rule: **when you change the instrument, you have
not changed the subject. Re-establish the control before reading the result.** A
probe edited five minutes ago is an unvalidated probe.

## 6. Worked protocol

Use this shape for any measurement whose result you intend to report.

```
CLAIM      (what you intend to conclude)

1. INSTRUMENT  name the exact command / probe.
2. CONTROL     run it on a case whose answer is already known;
               record the reading AND that it matched the known answer.
3. SUBJECT     run it on the thing under test.
4. NEGATIVE    if a check is involved, feed a deliberately-broken sample
               and confirm it is rejected.
5. GAP         state what this instrument cannot see.
```

### Concrete example

Claim: *"the frontend no longer calls the production endpoint."*

```
INSTRUMENT  packet capture on the container interface, filtered to the endpoint IP
CONTROL     request the endpoint directly -> capture shows the packets
            (proves the capture can see this traffic at all)
SUBJECT     drive the frontend -> capture shows 0 packets
NEGATIVE    point config at the endpoint temporarily -> packets appear again
            (proves the 0 came from the config, not from the filter)
GAP         covers IPv4 on this interface only; an IPv6 path or a proxy would
            be invisible to this capture
```

Now the version without controls — which is what most reports actually contain:

```
INSTRUMENT  packet capture
SUBJECT     drove the frontend -> 0 packets -> "no traffic left the machine"
```

The second version is not weaker evidence. It is **not evidence at all** — the
same output would appear if the filter were wrong, the interface were wrong, or
the traffic simply took a route the filter never looked at.

---

## The two rules

1. **No reading is trusted until the instrument has been shown to detect a
   known-present thing.**
2. **A zero with no positive control is not evidence.**

Both rules exist because instruments fail silently and confidently. Nobody
reports that their own probe broke — they report that the *system* is clean.
