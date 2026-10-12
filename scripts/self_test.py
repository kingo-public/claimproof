#!/usr/bin/env python3
"""
self_test.py -- the negative-sample protocol for check_claim.py.

This exists because of a rule the skill itself states:
    'A check that has never failed has not been shown to check anything.'

Every fixture below is a regression line. Fixtures 05-08 are the cases an
adversarial review used to break version 1 of the checker, which reported PASS
on a receipt of six 'x' characters. They are kept forever so the same class of
hole cannot return silently.

Run:  python3 scripts/self_test.py
Exit: 0 if every expected state matched, 1 otherwise.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURES = os.path.join(ROOT, 'evals', 'fixtures')
CHECKER = os.path.join(HERE, 'check_claim.py')

# (fixture, expected status, expected exit code, what it guards against)
CASES = [
    ('01_no_receipt.txt',        'BLOCK',      1,
     'a completion claim with no receipt'),
    ('02_full_receipt.txt',      'PASS',       0,
     'the good case'),
    ('03_empty_field.txt',       'UNVERIFIED', 2,
     'an empty MEASURED field'),
    ('04_no_claim.txt',          'PASS',       0,
     'no claim, nothing to receipt'),
    ('05_all_x_fields.txt',      'UNVERIFIED', 2,
     'six x characters -- the v1 hole'),
    ('06_self_admitted_fake.txt','UNVERIFIED', 2,
     'a receipt admitting nothing was measured'),
    ('07_descriptive_prose.txt', 'PASS',       0,
     'does not fire on exploration'),
    ('08_thin_measured.txt',     'UNVERIFIED', 2,
     'a MEASURED field too thin to be a reading'),
    ('09_good_receipt_2.txt',    'PASS',       0,
     'a second good receipt, different domain'),
]


def run(fixture):
    path = os.path.join(FIXTURES, fixture)
    proc = subprocess.run([sys.executable, CHECKER, path],
                          capture_output=True, text=True)
    first = proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else ''
    return first.split(':')[0].strip(), proc.returncode, first


def self_check():
    """Prove this harness can fail: corrupt an expectation and require MISMATCH."""
    fixture, want_status, want_code, _ = CASES[0]
    status, code, _ = run(fixture)
    deliberately_wrong = ('PASS', 0)
    if (status, code) == deliberately_wrong:
        print('  SELF-CHECK FAILED: the first fixture really is',
              status, '-- expectations cannot be validated')
        return False
    print('  self-check ok: fixture 01 is really',
          status, 'so a wrong expectation would be caught')
    return True


def main():
    if not os.path.isdir(FIXTURES):
        print('missing fixtures dir: ' + FIXTURES, file=sys.stderr)
        return 1

    print('self-check: can this harness detect a wrong expectation?')
    if not self_check():
        return 1
    print()

    failures = []
    print('%-28s %-11s %-11s %-5s %-7s %s' % (
        'fixture', 'expected', 'observed', 'exit', 'result', 'guards against'))
    print('-' * 104)
    for fixture, want_status, want_code, purpose in CASES:
        status, code, first = run(fixture)
        ok = (status == want_status and code == want_code)
        if not ok:
            failures.append((fixture, want_status, want_code, status, code, first))
        print('%-28s %-11s %-11s %-5d %-7s %s' % (
            fixture, want_status, status, code, 'ok' if ok else 'MISMATCH', purpose))
    print('-' * 104)

    if failures:
        print()
        for f, ws, wc, gs, gc, first in failures:
            print('MISMATCH ' + f)
            print('  expected: ' + ws + ' (exit ' + str(wc) + ')')
            print('  observed: ' + gs + ' (exit ' + str(gc) + ')')
            print('  stdout:   ' + first)
        print()
        print(str(len(failures)) + ' of ' + str(len(CASES)),
              'fixtures behaved unexpectedly')
        return 1

    print('all ' + str(len(CASES)) + ' states matched')
    return 0


if __name__ == '__main__':
    sys.exit(main())
