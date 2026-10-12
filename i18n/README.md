# Translations

Claimproof ships in three languages.

| Language | README | Skill + references |
| --- | --- | --- |
| English *(canonical)* | [README.md](../README.md) | [SKILL.md](../SKILL.md), [references/](../references/) |
| 繁體中文 | [README.zh-Hant.md](../README.zh-Hant.md) | [zh-Hant/](zh-Hant/) |
| 简体中文 | [README.zh-Hans.md](../README.zh-Hans.md) | [zh-Hans/](zh-Hans/) |

## Which file does DSH load?

**The root `SKILL.md`, always.** DSH discovers skills at
`<root>/<name>/SKILL.md` — exactly one level deep. The files under `i18n/` are
nested deeper than that and are therefore never discovered as skills. They are
translations for humans, not additional skills.

This is deliberate: a second discoverable `SKILL.md` with the same `name` would
create an ambiguous trigger.

## Translating the skill itself

If you want the agent to *operate* in Chinese, keep the root `SKILL.md` as-is
(its `description` is what triggers the skill, and must stay English for
reliable matching) and point your agent at the translated body:

```
Read i18n/zh-Hant/SKILL.md and follow it for this task.
```

A translation is never a substitute for the root file — it is a reading
companion.

## Keeping translations honest

A translation that quietly drops a case is worse than no translation, because
it looks complete. Two guards:

```bash
# structural comparison: fences, headings, table rows, receipt fields, numbers,
# code blocks and inline code spans
python3 scripts/check_translations.py SKILL.md i18n/zh-Hant/SKILL.md

# prove the checker itself can fail
python3 scripts/check_translations.py --self-test
```

The checker compares **numbers two ways** and code **byte for byte**. Every
number in the source must appear in the translation, and every number in the
translation must appear in the source — an invented figure is as suspicious as a
dropped one. A dropped number usually means a dropped case, a changed
measurement, or a silently rounded figure, and those are exactly what this
project is about.

Every check in the checker has a negative sample in `--self-test` proving it can
fail. Currently eight: one faithful copy, plus seven deliberately broken.

## What is not translated

Kept in English in every language, on purpose:

- frontmatter `name` and `description` — these drive skill triggering;
- the six receipt field names — `DONE`, `MEASURED`, `INSTRUMENT`,
  `NEGATIVE`, `BLIND`, `FALSIFIER` — they are an interface, not prose;
- the status values `PASS`, `BLOCK`, `UNVERIFIED` — the checker emits
  these literally;
- **the contents of every code block**, including comments inside them;
- code, commands, paths, filenames, and identifiers.

Translating an interface produces a translation that no longer connects to the
tooling. This is enforced, not just advised: `check_translations.py` fails a
translation whose code blocks are not byte-identical to the source.

## Contributing a translation

1. Copy `SKILL.md` and `references/` into `i18n/<lang>/`.
2. Translate the prose only, per the rules above.
3. Run `check_translations.py` for every file pair.
4. Add the language to the table at the top of this file and to the README.

If a translation cannot pass the checker, say so in the pull request rather than
loosening the checker. A known gap beats a silent one.

## Known limitation

The checker compares structure and machine-copyable content. It cannot judge
**prose quality**: a translation may pass every check and still read badly, or
invert a meaning in a sentence. It is a net, not a proof. Human review is still
required.
