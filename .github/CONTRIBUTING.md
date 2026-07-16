# Contributing

Thanks for helping. This repository is contracts and documentation first. There is no application runtime to install yet.

By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

This file follows the shape of [GitHub's own contributing note](https://github.com/github/.github/blob/master/CONTRIBUTING.md), rewritten for this project.

Work size follows [docs/contribution-units.md](../docs/contribution-units.md). Land work from a short-lived branch onto `main`. Do not open GitHub Issues or Pull Requests.

## Before you change anything

1. Read the [root README](../README.md).
2. Use names from [docs/glossary.md](../docs/glossary.md).
3. Describe this version as it is. Do not document a command or threshold that does not exist.

## Branch

From current `main`:

```text
git checkout main
git pull
git checkout -b <type>/<short-slug>
```

Examples: `docs/glossary`, `fix/snapshot-feature-order`.

## Check your change

```bash
python -m pip install -r requirements-ci.txt
python scripts/validate_contracts.py
```

If you edit `config/factory_layout.yaml`, rebuild the picture:

```bash
python scripts/render_factory_layout.py
```

Commit the updated `docs/images/factory-layout.svg` with the YAML that produced it.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```text
type(scope): imperative summary

Why this change is needed.
```

One concern per commit. Related contract files for that slice stay together. Refactors stay separate. Aim under 400 changed lines. Split before 1000.

## Land on main

Merge the branch into `main` locally, then delete the branch.

## Resources

- [How to contribute to open source](https://opensource.guide/how-to-contribute/)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [Google Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
