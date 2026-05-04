# ADR 0002 - OPC UA at the machine boundary

## Context

Machine state must enter the Digital Twin with industrial timestamps, quality flags, and a clear OT/IT split.

## Decision

Use an OPC UA adapter as the main machine interface. Keep a site-adapter interface for other customer protocols.

## Rejected default

Do not insert MQTT unless independent publish/subscribe fan-out becomes a real need.
