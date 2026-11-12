# Model comparison

Bolts: share still recognised as bolts, and share fully right (size + head type).
Non-bolts: share rejected, and share wrongly put in a size bin.
Right-bin precision: fraction of size-bin assignments correct. Coverage: correct size-bin assignments / all bolts.
Rejection counts actual REJECT routing; a missing board is REVIEW. All bolts, including board failures, remain in denominators.

| Test set | Model | Bolts recognised | Bolts fully right | Non-bolts rejected | Non-bolts in a size bin | Right-bin precision | Right-bin coverage | Sent to REVIEW |
|---|---|---|---|---|---|---|---|---|
| test_catalog_normal | boltnet_v3 | 96% | 64% | 96% | 0% | 84% | 41% | 41% |
| test_catalog_normal | boltnet_v3_refined | 96% | 68% | 96% | 0% | 88% | 39% | 44% |
| test_catalog_heavy | boltnet_v3 | 86% | 23% | 86% | 0% | 55% | 8% | 68% |
| test_catalog_heavy | boltnet_v3_refined | 86% | 25% | 86% | 0% | 53% | 7% | 68% |
| test_junk_normal | boltnet_v3 | - | - | 74% | 2% | 0% | - | 23% |
| test_junk_normal | boltnet_v3_refined | - | - | 74% | 3% | 0% | - | 22% |
| test_junk_heavy | boltnet_v3 | - | - | 40% | 2% | 0% | - | 57% |
| test_junk_heavy | boltnet_v3_refined | - | - | 40% | 2% | 0% | - | 58% |
| test_ai_normal | boltnet_v3 | - | - | 67% | 0% | - | - | 33% |
| test_ai_normal | boltnet_v3_refined | - | - | 67% | 0% | - | - | 33% |
| test_ai_heavy | boltnet_v3 | - | - | 33% | 0% | - | - | 67% |
| test_ai_heavy | boltnet_v3_refined | - | - | 33% | 0% | - | - | 67% |
| test_webhold_normal | boltnet_v3 | 80% | 1% | 83% | 0% | 0% | 0% | 43% |
| test_webhold_normal | boltnet_v3_refined | 80% | 2% | 83% | 0% | 0% | 0% | 43% |
| test_webhold_heavy | boltnet_v3 | 72% | 1% | 73% | 0% | 0% | 0% | 51% |
| test_webhold_heavy | boltnet_v3_refined | 72% | 2% | 73% | 0% | 0% | 0% | 51% |
| v3_fresh_normal | boltnet_v3 | 96% | 65% | 93% | 0% | 84% | 34% | 46% |
| v3_fresh_normal | boltnet_v3_refined | 96% | 69% | 93% | 0% | 91% | 37% | 46% |
| v3_fresh_heavy | boltnet_v3 | 85% | 25% | 72% | 0% | 62% | 8% | 70% |
| v3_fresh_heavy | boltnet_v3_refined | 85% | 32% | 72% | 0% | 82% | 8% | 72% |
