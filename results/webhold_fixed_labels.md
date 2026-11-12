# Model comparison

Bolts: share still recognised as bolts, and share fully right (size + head type).
Non-bolts: share rejected, and share wrongly put in a size bin.
Right-bin precision: fraction of size-bin assignments correct. Coverage: correct size-bin assignments / all bolts.
Rejection counts actual REJECT routing; a missing board is REVIEW. All bolts, including board failures, remain in denominators.
Bolts photographed at an angle (no known length) count toward recognition only.

| Test set | Model | Bolts recognised | Bolts fully right | Non-bolts rejected | Non-bolts in a size bin | Right-bin precision | Right-bin coverage | Sent to REVIEW |
|---|---|---|---|---|---|---|---|---|
| test_webhold_normal | boltnet | 31% | 7% | 84% | 2% | 15% | 2% | 19% |
| test_webhold_normal | boltnet_v3 | 78% | 23% | 70% | 0% | 25% | 2% | 43% |
| test_webhold_normal | boltnet_v3_refined | 78% | 25% | 70% | 0% | 20% | 1% | 44% |
| test_webhold_heavy | boltnet | 46% | 1% | 71% | 1% | 0% | 0% | 36% |
| test_webhold_heavy | boltnet_v3 | 77% | 8% | 62% | 0% | 0% | 0% | 52% |
| test_webhold_heavy | boltnet_v3_refined | 77% | 6% | 62% | 0% | - | 0% | 52% |
