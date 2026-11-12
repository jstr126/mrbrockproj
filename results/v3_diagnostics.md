# Model comparison

Bolts: share still recognised as bolts, and share fully right (size + head type).
Non-bolts: share rejected, and share wrongly put in a size bin.
Right-bin precision: fraction of size-bin assignments correct. Coverage: correct size-bin assignments / all bolts.
Rejection counts actual REJECT routing; a missing board is REVIEW. All bolts, including board failures, remain in denominators.

| Test set | Model | Bolts recognised | Bolts fully right | Non-bolts rejected | Non-bolts in a size bin | Right-bin precision | Right-bin coverage | Sent to REVIEW |
|---|---|---|---|---|---|---|---|---|
| test_catalog_normal | boltnet_v3 | 96% | 64% | 98% | 0% | 83% | 40% | 40% |
| test_catalog_heavy | boltnet_v3 | 87% | 23% | 82% | 0% | 59% | 8% | 70% |
| test_junk_normal | boltnet_v3 | - | - | 74% | 2% | 0% | - | 24% |
| test_junk_heavy | boltnet_v3 | - | - | 40% | 2% | 0% | - | 58% |
| test_ai_normal | boltnet_v3 | - | - | 67% | 0% | - | - | 33% |
| test_ai_heavy | boltnet_v3 | - | - | 33% | 0% | - | - | 67% |
| test_webhold_normal | boltnet_v3 | 77% | 1% | 82% | 0% | 0% | 0% | 44% |
| test_webhold_heavy | boltnet_v3 | 78% | 1% | 71% | 0% | 0% | 0% | 52% |
