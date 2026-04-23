# OpenUSD and Omniverse

Terms: [glossary](glossary.md).

OpenUSD is the spatial source of truth. Omniverse Kit is the 3D app. Neither owns safety rules or process measurements.

This version has layout YAML and a 2D floor picture. It does not have USD files or Kit apps yet.

## Root tree

```text
/World
  BugokFactory
    Buildings
      MainFactory
      Office
      RnD
    Production
      Drawing
      Pilger
      HeatTreatment
      Pointing
      Cleaning
      Straightening
      Cutting
      Packaging
    Inspection
      ECT
      Hydro
      Dimension
      Visual
    MaterialHandling
      Racks
      Cranes
    Utilities
```

Drawing 4 prim: `/World/BugokFactory/Production/Drawing/Drawing_04`

## Asset files

Each important Asset is its own USD file.

```text
assets/drawing/Drawing_04.usd
  proxy
  render
```

Use:

- `payload` for large optional assets
- `proxy` purpose for distant areas
- `render` purpose for the focused machine
- variants for equipment state when useful

## Senior app

- Whole-factory navigation
- Live state overlay
- Status filters
- Timeline of historical Snapshots
- Evaluation Lineage panel
- FEA contour and critical region
- Scenario create and compare

History view must look different from live state.

