#!/usr/bin/env python3
'''
verify.py -- run every check in this repository, in CI or by hand.

Usage:
    python3 scripts/verify.py
    python3 scripts/verify.py --quiet

Exit codes:
    0 = every check passed
    1 = at least one check failed

Why this exists:
    SKILL.md warns about failure mode 8 -- a gate nobody runs is not a gate.
    Before this file existed, claimproof was itself that: its checkers were
    correct and nothing invoked them. An adversarial review pointed this out.
    This script is wired into .github/workflows/verify.yml.

Note: passing this script proves the checks discriminate. It does not prove
    the skill changes agent behaviour. That remains untested.
'''

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PAIRS = [
    ('SKILL.md', 'i18n/zh-Hant/SKILL.md'),
    ('SKILL.md', 'i18n/zh-Hans/SKILL.md'),
    ('references/failure-modes.md', 'i18n/zh-Hant/references/failure-modes.md'),
    ('references/failure-modes.md', 'i18n/zh-Hans/references/failure-modes.md'),
    ('references/instrument.md', 'i18n/zh-Hant/references/instrument.md'),
    ('references/instrument.md', 'i18n/zh-Hans/references/instrument.md'),
    ('references/negative-samples.md', 'i18n/zh-Hant/references/negative-samples.md'),
    ('references/negative-samples.md', 'i18n/zh-Hans/references/negative-samples.md'),
    ('README.md', 'README.zh-Hant.md'),
    ('README.md', 'README.zh-Hans.md'),
]


def run(label, args, quiet=False):
    proc = subprocess.run([sys.executable] + args, cwd=ROOT,
                          capture_output=True, text=True)
    ok = (proc.returncode == 0)
    print(('  PASS  ' if ok else '  FAIL  ') + label)
    if not ok or not quiet:
        for line in (proc.stdout + proc.stderr).strip().splitlines()[-6:]:
            print('          ' + line)
    return ok


def main(argv):
    quiet = '--quiet' in argv
    failures = []

    print('negative-sample protocols (must be able to fail)')
    if not run('check_claim.py / self_test.py',
               ['scripts/self_test.py'], quiet):
        failures.append('receipt self-test')
    if not run('check_translations.py --self-test',
               ['scripts/check_translations.py', '--self-test'], quiet):
        failures.append('translation self-test')

    print('translation consistency')
    for src, dst in PAIRS:
        sp, dp = os.path.join(ROOT, src), os.path.join(ROOT, dst)
        label = os.path.basename(dst)
        if not os.path.isfile(sp) or not os.path.isfile(dp):
            print('  FAIL  ' + label + '  (missing file)')
            failures.append(label)
            continue
        if not run(label, ["scripts/check_translations.py", sp, dp], quiet):
            failures.append(label)

    print()
    if failures:
        print(str(len(failures)) + ' check(s) failed: ' + ', '.join(failures))
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
