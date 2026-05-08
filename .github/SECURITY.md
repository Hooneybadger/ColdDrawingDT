# Reporting security issues

This project takes security reports seriously. Please disclose findings privately.

This policy follows GitHub's security advisory flow. GitHub Docs cites [Electron's SECURITY.md](https://github.com/electron/electron/blob/main/SECURITY.md) as a real example. This file uses the same private advisory path, without Electron-specific escalation.

## How to report

Use GitHub Security Advisories:

https://github.com/Hooneybadger/ColdDrawingDT/security/advisories/new

Do not open a public issue for a vulnerability.

Please include:

- Affected files or contracts
- What you observed
- How to reproduce if you can
- Impact you expect

We will reply with next steps. After that we will keep you informed about a fix and any public note.

## Scope for this version

This repository currently holds documentation, YAML contracts, JSON Schema, and CI scripts. There is no production API yet. Reports about leaked secrets, unsafe examples, or CI supply-chain issues are still in scope.

Report bugs in third-party tools (OpenRadioss, BaSyx, PINN files, GitHub Actions) to the maintainers of those projects.

## Questions that are not security issues

See [SUPPORT.md](SUPPORT.md) and the [README](../README.md).
