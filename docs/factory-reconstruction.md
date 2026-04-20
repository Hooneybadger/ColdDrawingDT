# Factory reconstruction

Terms: [glossary](glossary.md).

Source files:

- [config/factory_layout.yaml](../config/factory_layout.yaml)
- [config/asset_registry.yaml](../config/asset_registry.yaml)

This picture is generated from those files. Drawing 4 is the thick box.

![Main factory floor plan](images/factory-layout.svg)

Rebuild:

```bash
python scripts/render_factory_layout.py
```

## Coordinates

```text
Origin: south-west floor corner of the main hall
X+: hall length
Y+: hall width
Z+: up
Unit: meter
```

## Hall

```text
Length X: 96.00 m
Width Y: 41.13 m
Floor area: about 3948.5 m2
Maximum building height: 14.20 m
```

Grid X: `0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96`

Grid Y: `0, 13.71, 27.42, 41.13`

Halls:

- Bay A: Y 0.00 to 13.71
- Bay B: Y 13.71 to 27.42
- Bay C: Y 27.42 to 41.13

