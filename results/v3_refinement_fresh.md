# Model comparison

Bolts: share still recognised as bolts, and share fully right (size + head type).
Non-bolts: share rejected, and share wrongly put in a size bin.
Right-bin precision: fraction of size-bin assignments correct. Coverage: correct size-bin assignments / all bolts.
Rejection counts actual REJECT routing; a missing board is REVIEW. All bolts, including board failures, remain in denominators.

| Test set | Model | Bolts recognised | Bolts fully right | Non-bolts rejected | Non-bolts in a size bin | Right-bin precision | Right-bin coverage | Sent to REVIEW |
|---|---|---|---|---|---|---|---|---|
| v3_fresh_normal | boltnet_v3 | 96% | 66% | 92% | 0% | 86% | 35% | 45% |
| v3_fresh_normal | boltnet_v3_refined | 96% | 70% | 92% | 0% | 92% | 36% | 46% |
| v3_fresh_heavy | boltnet_v3 | 85% | 25% | 78% | 0% | 67% | 8% | 67% |
| v3_fresh_heavy | boltnet_v3_refined | 85% | 32% | 78% | 0% | 82% | 8% | 69% |
