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

