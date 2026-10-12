#!/usr/bin/env python3
"""
check_claim.py -- verify that a completion claim carries a SUBSTANTIVE receipt.

Usage:
    python3 scripts/check_claim.py <file>... [--json]
    python3 scripts/check_claim.py -            # read stdin

Exit codes:
    0 = PASS        a complete, substantive receipt, or no claim at all
    1 = BLOCK       a completion claim with no receipt
    2 = UNVERIFIED  a receipt that is incomplete, hollow, or self-reported absent

## What this checker CANNOT do -- read this before trusting it

It validates SUBSTANCE, not TRUTH. A confident, detailed, entirely fabricated
receipt passes. This is a floor against hollow reporting, not proof of
correctness. Never present a PASS here as evidence that a claim is true.

## Why this was rewritten

Version 1 checked only that each field was non-empty. It then passed
    "DONE x / MEASURED x / INSTRUMENT x / NEGATIVE x / BLIND x / FALSIFIER x"
with exit 0, and also passed a receipt whose BLIND field admitted the entire
claim was unverified. That made the checker exactly what SKILL.md warns about:
a gate that does not gate. An adversarial review found it; evals/README.md
records it.
"""

import argparse
import json
import re
import sys

FIELDS = ['DONE', 'MEASURED', 'INSTRUMENT', 'NEGATIVE', 'BLIND', 'FALSIFIER']

# A completion assertion. Deliberately NARROWER than version 1.
# Version 1 matched a bare \b(works|fixed|done)\b, so it flagged ordinary
# prose such as 'The caching layer works by hashing the key.' -- a wrong gate,
# which SKILL.md itself forbids firing on exploration. Claim context is now
# required.
CLAIM_PATTERNS = [
    r"\b(?:i|we)\s+(?:have\s+|had\s+|already\s+)?(?:fixed|finished|completed|implemented|resolved|patched|merged|deployed|shipped)\b",
    r"\bit(?:'s| is| was)\s+(?:now\s+)?(?:done|fixed|ready|working|deployed|shipped|live|green|passing)\b",
    r"\b(?:is|are|was|were)\s+(?:now\s+)?(?:fixed|deployed|shipped|live|passing|green)\b",
    r"\bworks\s+(?:now|again|correctly|as expected|as intended)\b",
    r"\b(?:all\s+)?(?:the\s+)?(?:tests?|checks?|suites?)\s+(?:now\s+)?pass(?:es|ed)?\b",
    r"\bci\s+is\s+green\b",
    r"\b(?:i|we)\s+(?:have\s+)?(?:verified|confirmed|validated)\b",
    r"\b(?:verified|confirmed|proven|validated)\s+(?:working|correct|fixed|done)\b",
    r"\bno\s+(?:known\s+)?(?:issues?|problems?|errors?)\b",
    r"\bshould\s+(?:be\s+)?(?:fine|work|be\s+ok(?:ay)?)\b",
    r"\bdeployed\s+to\s+(?:prod|production|staging)\b",
    r"\b(?:ready|good)\s+to\s+(?:ship|go|merge|deploy)\b",
    r"\bthe\s+bug\s+is\s+(?:fixed|gone|resolved)\b",
]

# Content-free values. Never substantive, whatever the field.
FILLER_VALUES = {
    'x', 'xx', 'xxx', 'xxxx', 'y', 'yy', 'yyy', 'z', 'zz', 'foo', 'bar', 'baz',
    'test', 'asdf', 'qwerty', 'tbd', 'tba', 'todo', 'fixme', 'pass', 'passed',
    'ok', 'okay', 'fine', 'good', 'yes', 'no', 'same', 'see above', 'as above',
    'none', 'n/a', 'na', 'nil', 'null', 'undefined', 'nothing', 'whatever',
    '-', '--', '.', '..', '...', '?', '??', '???', '!', '!!',
}

# Values that ADMIT no observation was made. A receipt containing one is honest,
# and therefore UNVERIFIED -- never PASS. SKILL.md says exactly this.
# Version 1 treated these as valid content, which is how a receipt stating
# 'Nothing was measured' earned a green light.
ABSENCE_PATTERNS = [
    r'^none\b',
    r'^n/?a\b',
    r'\bnothing\s+was\s+measured\b',
    r'\bnot\s+measured\b',
    r'\bno\s+measurement\b',
    r'\bno\s+evidence\b',
    r'\bcould\s+not\s+reproduce\b',
    r"\bcouldn['\u2019]?t\s+reproduce\b",
    r'\bdid\s+not\s+measure\b',
    r"\bdidn['\u2019]?t\s+measure\b",
    r'\bunable\s+to\s+(?:measure|verify|reproduce)\b',
    r'^everything\b',
    r'^the\s+entire\s+claim\b',
    r'\bno\s+verification\s+was\b',
]

# A self-declaration that this claim is not verified. This MUST change the
# verdict. In version 1 it did not: both branches returned UNVERIFIED, making
# the marker dead code -- an adversarial review caught it.
UNVERIFIED_MARKERS = [
    r'^\s*status\s*:?[ \t]*unverified\s*$',
    r'^\s*unverified\s*$',
]


def extract_fields(text):
    """Return {field: value} for each receipt field present.

    Uses [ \\t] rather than \\s for intra-line whitespace on purpose: \\s also
    matches newlines, which silently lets an empty field absorb the NEXT line's
    label as its value. That exact bug shipped in version 1 and reported PASS on
    an empty MEASURED field. See evals/README.md.
    """
    out = {}
    for f in FIELDS:
        m = re.search(r'^[ \t]*' + f + r'[ \t]*:?[ \t]*(.*)$', text,
                      re.MULTILINE | re.IGNORECASE)
        if m:
            out[f] = m.group(1).strip()
    return out


def is_claim(text):
    return any(re.search(p, text, re.IGNORECASE) for p in CLAIM_PATTERNS)


def is_unverified_declared(text):
    return any(re.search(p, text, re.MULTILINE | re.IGNORECASE)
               for p in UNVERIFIED_MARKERS)


def classify_value(value):
    """Return 'empty' | 'filler' | 'absence' | 'ok' for one field value."""
    v = value.strip()
    if not v:
        return 'empty'
    low = v.lower().strip(' .;:!')
    if low in FILLER_VALUES:
        return 'filler'
    # One or two characters is never an observation.
    if len(re.sub(r'\s', '', low)) <= 2:
        return 'filler'
    # A value made of a single repeated character.
    if len(set(re.sub(r'\s', '', low))) <= 1:
        return 'filler'
    for p in ABSENCE_PATTERNS:
        if re.search(p, v, re.IGNORECASE):
            return 'absence'
    return 'ok'


def measurement_is_substantive(value):
    """A measurement should look like a reading, not a word.

    Accept a digit, a code-like token, or at least four words. This is a floor,
    not a proof -- a smooth talker clears it easily. Stated so nobody mistakes
    this gate for a truth check.
    """
    v = value.strip()
    if re.search(r'\d', v):
        return True
    if re.search(r'`[^`]+`', v):
        return True
    if re.search(r'\b[0-9a-f]{6,}\b', v, re.IGNORECASE):
        return True
    return len(re.findall(r'\S+', v)) >= 4


def evaluate(text):
    fields = extract_fields(text)
    claim = is_claim(text)
    declared_unverified = is_unverified_declared(text)

    present = [f for f in FIELDS if f in fields]
    missing = [f for f in FIELDS if f not in fields]
    empty = [f for f in present if not fields[f].strip()]

    verdicts = {f: classify_value(fields[f]) for f in present}
    filler = sorted(f for f, v in verdicts.items() if v == 'filler')
    absence = sorted(f for f, v in verdicts.items() if v == 'absence')

    base = dict(present=present, missing=missing, empty=empty,
                filler=filler, absence=absence)

    # No receipt at all.
    if not present:
        if claim:
            return dict(status='BLOCK',
                        reason='a completion claim with no receipt fields',
                        **base)
        return dict(status='PASS',
                    reason='no completion claim found; nothing to receipt',
                    **base)

    # A receipt is present. Grade it on content, not on the tags existing.
    reasons = []
    if declared_unverified:
        reasons.append('explicitly marked UNVERIFIED')
    if empty:
        reasons.append('empty field(s): ' + ', '.join(empty))
    if filler:
        reasons.append('content-free field(s): ' + ', '.join(filler))
    if absence:
        reasons.append('field(s) admitting no observation: ' + ', '.join(absence))
    if missing:
        reasons.append('missing field(s): ' + ', '.join(missing))

    if not reasons and not measurement_is_substantive(fields['MEASURED']):
        return dict(status='UNVERIFIED',
                    reason='MEASURED is too thin to be an observation',
                    hint='name a number, an exact output, or a specific observed'
                         ' change',
                    **base)

    if reasons:
        return dict(status='UNVERIFIED', reason='; '.join(reasons), **base)

    return dict(status='PASS',
                reason='complete, substantive receipt covering all six fields',
                caveat='validates substantiveness, NOT truth',
                **base)


def render(res):
    lines = [res['status'] + ': ' + res['reason']]
    if res.get('caveat'):
        lines.append('  caveat:  ' + res['caveat'])
    if res.get('hint'):
        lines.append('  hint:    ' + res['hint'])
    for key in ('present', 'missing', 'empty', 'filler', 'absence'):
        vals = res.get(key) or []
        if vals:
            lines.append('  %-9s %s' % (key + ':', ', '.join(vals)))
    return '\n'.join(lines)


def check_one(path):
    if path == '-':
        return evaluate(sys.stdin.read()), '-'
    with open(path, 'r', encoding='utf-8') as fh:
        return evaluate(fh.read()), path


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Verify a completion claim carries a substantive receipt.')
    ap.add_argument('paths', nargs='+', help='file(s) to check, or - for stdin')
    ap.add_argument('--json', action='store_true', help='machine-readable output')
    args = ap.parse_args(argv)

    worst = 0
    results = []
    for path in args.paths:
        try:
            res, name = check_one(path)
        except OSError as e:
            print('cannot read ' + path + ': ' + str(e), file=sys.stderr)
            return 2
        code = {'PASS': 0, 'BLOCK': 1, 'UNVERIFIED': 2}[res['status']]
        worst = max(worst, code)
        results.append(dict(path=name, **res))

    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0],
                         ensure_ascii=False, indent=2))
    else:
        for res in results:
            if len(results) > 1:
                print('== ' + res['path'])
            print(render(res))
    return worst


if __name__ == '__main__':
    sys.exit(main())
