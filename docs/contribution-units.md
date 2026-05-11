# Branches and commits

This repository lands work on `main` from short-lived topic branches.

## Sources

- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow): one short-lived branch per related change; each commit is an isolated, complete change.
- [Google Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html): one self-contained change; about 100 lines is often enough; about 1000 lines is usually too large; related tests stay with the change; refactorings stay separate; the tree must keep working after each land.
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/): `type(scope): summary`. If a change fits more than one type, make more than one commit.

