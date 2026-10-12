#!/usr/bin/env python3
'''
check_translations.py -- prove a translation did not silently drop or alter content.

A translation can look complete and still be missing a case, a number, a table
row, or a whole code block. Reading it will not tell you. This compares
structure and machine-copyable content, not prose.

Usage:
    python3 scripts/check_translations.py <source.md> <translation.md> [...]
    python3 scripts/check_translations.py --self-test

Exit codes:
    0 = PASS   every pair matched on all checked properties
    1 = FAIL   at least one pair disagreed
    2 = ERROR  a file could not be read

What this cannot check: prose quality. A translation can pass every check here
and still read badly or invert a meaning. This is a structural net, not proof.

Why this was rewritten: version 1 compared numbers one-way (source minus
translation), so a translation that INVENTED a number passed. It also compared
only the COUNT of code fences, which cannot detect an altered code block. An
adversarial review found the first; a translator found the second. Both now
carry negative samples in --self-test.
'''

import os
import re
import sys

FIELDS = ['DONE', 'MEASURED', 'INSTRUMENT', 'NEGATIVE', 'BLIND', 'FALSIFIER']
TICK = chr(96)
FENCE = TICK * 3
NL = chr(10)
BS = chr(92)
SP = chr(32)


def code_blocks(text):
    '''Return the contents of fenced code blocks, verbatim.

    Code must survive translation untouched: it is commands, file names, and
    sample receipts, not prose.
    '''
    pattern = '^' + FENCE + '[^' + NL + ']*' + NL + '(.*?)^' + FENCE + '[' + SP + BS + 't]*$'
    return re.findall(pattern, text, re.MULTILINE | re.DOTALL)


def inline_code(text):
    '''Return the contents of inline code spans, verbatim.'''
    return re.findall(TICK + '([^' + TICK + NL + ']+)' + TICK, text)


def profile(path):
    '''Structural and machine-copyable fingerprint of a markdown file.'''
    with open(path, 'r', encoding='utf-8') as fh:
        text = fh.read()
    return {
        'fences': len(re.findall('^' + FENCE, text, re.MULTILINE)),
        'headings': len(re.findall('^#{1,6} ', text, re.MULTILINE)),
        'table_rows': len(re.findall('^' + BS + '|', text, re.MULTILINE)),
        'numbers': set(re.findall(BS + 'd+(?:' + BS + '.' + BS + 'd+)?', text)),
        'fields': set(f for f in FIELDS
                      if re.search('^[' + SP + BS + 't]*' + f + BS + 'b',
                                   text, re.MULTILINE)),
        'blocks': code_blocks(text),
        'inline': inline_code(text),
        'lines': text.count(NL) + 1,
    }


def compare(src_path, dst_path):
    '''Return (problems, src_profile, dst_profile); empty problems = consistent.'''
    a = profile(src_path)
    b = profile(dst_path)
    problems = []

    for key in ('fences', 'headings', 'table_rows'):
        if a[key] != b[key]:
            problems.append('%s: source has %d, translation has %d'
                            % (key, a[key], b[key]))

    missing_fields = sorted(a['fields'] - b['fields'])
    if missing_fields:
        problems.append('receipt fields dropped: ' + ', '.join(missing_fields))

    # TWO-WAY. A dropped number usually means a dropped case or a changed
    # measurement. An ADDED number usually means invented content.
    dropped = sorted(a['numbers'] - b['numbers'])
    added = sorted(b['numbers'] - a['numbers'])
    if dropped:
        problems.append('numbers dropped: ' + ', '.join(dropped))
    if added:
        problems.append('numbers added: ' + ', '.join(added))

    if len(a['blocks']) != len(b['blocks']):
        problems.append('code blocks: source has %d, translation has %d'
                        % (len(a['blocks']), len(b['blocks'])))
    else:
        for i, (x, y) in enumerate(zip(a['blocks'], b['blocks']), 1):
            if x != y:
                problems.append('code block %d differs from source' % i)

    if len(a['inline']) != len(b['inline']):
        problems.append('inline code spans: source has %d, translation has %d'
                        % (len(a['inline']), len(b['inline'])))
    else:
        changed = sorted(set(x for x, y in zip(a['inline'], b['inline']) if x != y))
        if changed:
            problems.append('inline code altered: ' + ', '.join(changed[:5]))

    return problems, a, b


def self_test():
    '''Every check must have a negative sample proving it can fail.'''
    import tempfile

    tick = TICK
    src = ('# Title' + NL + NL +
           'Text with 298 and 291.' + NL + NL +
           FENCE + 'bash' + NL + 'grep -c X || echo 0' + NL + FENCE + NL + NL +
           'Inline ' + tick + 'grep -q' + tick + ' here.' + NL + NL +
           '| a | b |' + NL + '| --- | --- |' + NL + '| 1 | 2 |' + NL + NL +
           'DONE       something observed here' + NL +
           'MEASURED   a reading' + NL +
           'INSTRUMENT curl' + NL +
           'NEGATIVE   reverted it' + NL +
           'BLIND      staging only' + NL +
           'FALSIFIER  a user reports it' + NL)

    cases = [
        ('faithful copy',         src,                                    False, 'baseline'),
        ('number dropped',        src.replace('298 and 291', '298'),      True,  'numbers'),
        ('number invented',       src.replace('298 and', '298 and 9 and'), True, 'numbers'),
        ('heading dropped',       src.replace('# Title', ''),             True,  'headings'),
        ('table row dropped',     src.replace('| 1 | 2 |', ''),           True,  'table_rows'),
        ('receipt field dropped', src.replace('FALSIFIER', ''),           True,  'fields'),
        ('code block altered',    src.replace('grep -c X', 'grep -c Y'),  True,  'blocks'),
        ('inline code altered',   src.replace(tick + 'grep -q' + tick,
                                               tick + 'grep -qx' + tick), True, 'inline'),
    ]

    failed = []
    with tempfile.TemporaryDirectory() as td:
        s = os.path.join(td, 'src.md')
        with open(s, 'w', encoding='utf-8') as fh:
            fh.write(src)
        print('%-26s %-9s %-9s %s' % ('negative sample', 'expected', 'observed', 'check'))
        print('-' * 62)
        for label, content, should_fail, which in cases:
            d = os.path.join(td, 'dst.md')
            with open(d, 'w', encoding='utf-8') as fh:
                fh.write(content)
            problems, _, _ = compare(s, d)
            got = bool(problems)
            ok = (got == should_fail)
            if not ok:
                failed.append((label, should_fail, problems, got))
            print('%-26s %-9s %-9s %s' % (
                label, 'FAIL' if should_fail else 'PASS',
                'FAIL' if got else 'PASS', which))

    print('-' * 62)
    if failed:
        for label, want, problems, got in failed:
            print('MISMATCH: ' + label)
            print('  expected failure: ' + str(want) + ', observed: ' + str(got))
            print('  problems: ' + str(problems))
        return 1
    print('all ' + str(len(cases)) + ' negative samples behaved as required')
    return 0


def main(argv):
    if '--self-test' in argv:
        print('self-test: does every check here have a sample that makes it fail?')
        print()
        return self_test()

    args = [a for a in argv[1:] if not a.startswith('--')]
    if len(args) < 2 or len(args) % 2 != 0:
        print('usage: check_translations.py <source.md> <translation.md> [...]',
              file=sys.stderr)
        print('       check_translations.py --self-test', file=sys.stderr)
        return 2

    all_problems = []
    pairs = 0
    for i in range(0, len(args), 2):
        src_path, dst_path = args[i], args[i + 1]
        label = os.path.basename(dst_path)
        for p in (src_path, dst_path):
            if not os.path.isfile(p):
                print('cannot read ' + p, file=sys.stderr)
                return 2
        problems, a, b = compare(src_path, dst_path)
        if problems:
            print('FAIL ' + label)
            for pr in problems:
                print('     ' + pr)
            all_problems.append(label)
        else:
            pairs += 1
            print('PASS %s  (%d lines, %d fences, %d headings, %d blocks)'
                  % (label, b['lines'], b['fences'], b['headings'],
                     len(b['blocks'])))

    print()
    if all_problems:
        print(str(len(all_problems)) + ' translation(s) inconsistent: '
              + ', '.join(all_problems))
        return 1
    print(str(pairs) + ' translation(s) structurally consistent')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
