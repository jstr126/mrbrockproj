# Model comparison

Bolts: share still recognised as bolts, and share fully right (size + head type).
Non-bolts: share rejected, and share wrongly put in a size bin.
Right-bin precision: fraction of size-bin assignments correct. Coverage: correct size-bin assignments / all bolts.
Rejection counts actual REJECT routing; a missing board is REVIEW. All bolts, including board failures, remain in denominators.
Bolts photographed at an angle (no known length) count toward recognition only.

| Test set | Model | Bolts recognised | Bolts fully right | Non-bolts rejected | Non-bolts in a size bin | Right-bin precision | Right-bin coverage | Sent to REVIEW |
|---|---|---|---|---|---|---|---|---|
| test_catalog_normal | boltnet_v3 | 96% | 64% | 96% | 0% | 84% | 41% | 41% |
| test_catalog_normal | boltnet_v3_refined | 96% | 68% | 96% | 0% | 88% | 39% | 44% |
| test_catalog_normal | boltnet_v3_ft | 95% | 66% | 96% | 0% | 83% | 43% | 38% |
| test_catalog_heavy | boltnet_v3 | 86% | 23% | 86% | 0% | 55% | 8% | 68% |
| test_catalog_heavy | boltnet_v3_refined | 86% | 25% | 86% | 0% | 53% | 7% | 68% |
| test_catalog_heavy | boltnet_v3_ft | 86% | 21% | 88% | 0% | 53% | 11% | 63% |
| test_junk_normal | boltnet_v3 | - | - | 74% | 2% | 0% | - | 23% |
| test_junk_normal | boltnet_v3_refined | - | - | 74% | 3% | 0% | - | 22% |
| test_junk_normal | boltnet_v3_ft | - | - | 76% | 4% | 0% | - | 20% |
| test_junk_heavy | boltnet_v3 | - | - | 40% | 2% | 0% | - | 57% |
| test_junk_heavy | boltnet_v3_refined | - | - | 40% | 2% | 0% | - | 58% |
| test_junk_heavy | boltnet_v3_ft | - | - | 44% | 2% | 0% | - | 54% |
| test_ai_normal | boltnet_v3 | - | - | 67% | 0% | - | - | 33% |
| test_ai_normal | boltnet_v3_refined | - | - | 67% | 0% | - | - | 33% |
| test_ai_normal | boltnet_v3_ft | - | - | 73% | 0% | - | - | 27% |
| test_ai_heavy | boltnet_v3 | - | - | 33% | 0% | - | - | 67% |
| test_ai_heavy | boltnet_v3_refined | - | - | 33% | 0% | - | - | 67% |
| test_ai_heavy | boltnet_v3_ft | - | - | 60% | 0% | - | - | 40% |
| test_webhold_normal | boltnet_v3 | 78% | 23% | 70% | 0% | 25% | 2% | 43% |
| test_webhold_normal | boltnet_v3_refined | 78% | 25% | 70% | 0% | 20% | 1% | 44% |
| test_webhold_normal | boltnet_v3_ft | 70% | 25% | 78% | 1% | 40% | 5% | 33% |
| test_webhold_heavy | boltnet_v3 | 77% | 8% | 62% | 0% | 0% | 0% | 52% |
| test_webhold_heavy | boltnet_v3_refined | 77% | 6% | 62% | 0% | - | 0% | 52% |
| test_webhold_heavy | boltnet_v3_ft | 60% | 8% | 67% | 1% | 18% | 2% | 40% |
| v3_fresh_normal | boltnet_v3 | 96% | 65% | 93% | 0% | 84% | 34% | 46% |
| v3_fresh_normal | boltnet_v3_refined | 96% | 69% | 93% | 0% | 91% | 37% | 46% |
| v3_fresh_normal | boltnet_v3_ft | 95% | 65% | 93% | 0% | 78% | 38% | 38% |
| v3_fresh_heavy | boltnet_v3 | 85% | 25% | 72% | 0% | 62% | 8% | 70% |
| v3_fresh_heavy | boltnet_v3_refined | 85% | 32% | 72% | 0% | 82% | 8% | 72% |
| v3_fresh_heavy | boltnet_v3_ft | 86% | 22% | 76% | 0% | 45% | 6% | 67% |
