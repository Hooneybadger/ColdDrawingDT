# ADR 0006 - OpenUSD and Omniverse Kit

## Context

Senior engineers need a detailed whole-factory view. Operators need a smaller task view on limited client hardware.

## Decision

Use OpenUSD as the one spatial source of truth. Use Omniverse Kit apps for both roles. Use payload, proxy, and render purposes for detail. Stream from an on-site RTX host over WebRTC for low-spec clients.

## Rejected

Do not keep a second Unity asset pipeline.
