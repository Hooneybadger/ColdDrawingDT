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

## Major envelopes

Sizes in meters. These are bounding boxes, not CAD.

| Asset | L | W | H | Job |
|---|---:|---:|---:|---|
| Drawing 2 | 35.5 | 5.5 | 2.8 | cold drawing |
| Drawing 4 | 35.5 | 5.5 | 2.8 | cold drawing |
| Pilger | 34.0 | 5.4 | 2.6 | cold pilger |
| Heat treatment 1 | 36.8 | 4.0 | 3.5 | heat and cool |
| Heat treatment 2 | 36.8 | 4.0 | 3.5 | heat and cool |
| Straightening | 17.0 | 3.3 | 2.3 | straighten |
| Cutting | 11.0 | 3.2 | 2.2 | cut |
| ECT | 16.0 | 3.0 | 2.2 | eddy-current inspect |
| Hydro test | 12.0 | 3.5 | 2.2 | pressure inspect |
| Dimension | 8.0 | 3.0 | 2.2 | size inspect |
| Washing | 12.0 | 4.0 | 2.5 | clean |

