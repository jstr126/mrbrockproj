# Model comparison

Bolts: share still recognised as bolts, and share fully right (size + head type).
Non-bolts: share rejected, and share wrongly put in a size bin.
Size bins: share of everything sent to a size bin that went to the right one.

| Test set | Model | Bolts recognised | Bolts fully right | Non-bolts rejected | Non-bolts in a size bin | Right size bin | Sent to REVIEW |
|---|---|---|---|---|---|---|---|
| test_catalog_normal | boltnet_v1 | 96% | 52% | 98% | 0% | 59% | 16% |
| test_catalog_normal | boltnet | 96% | 58% | 98% | 0% | 66% | 15% |
| test_catalog_heavy | boltnet_v1 | 90% | 13% | 89% | 0% | 24% | 57% |
| test_catalog_heavy | boltnet | 90% | 23% | 88% | 0% | 39% | 57% |
| test_junk_normal | boltnet_v1 | - | - | 18% | 50% | 0% | 36% |
| test_junk_normal | boltnet | - | - | 81% | 10% | 0% | 18% |
| test_junk_heavy | boltnet_v1 | - | - | 24% | 16% | 0% | 71% |
| test_junk_heavy | boltnet | - | - | 53% | 4% | 0% | 56% |
| test_ai_normal | boltnet_v1 | - | - | 4% | 67% | 0% | 33% |
| test_ai_normal | boltnet | - | - | 96% | 2% | 0% | 7% |
| test_ai_heavy | boltnet_v1 | - | - | 40% | 22% | 0% | 47% |
| test_ai_heavy | boltnet | - | - | 87% | 0% | - | 24% |
| test_web_normal | boltnet_v1 | 85% | 2% | 71% | 15% | 1% | 27% |
| test_web_normal | boltnet | 34% | 1% | 94% | 2% | 6% | 16% |
| test_web_heavy | boltnet_v1 | 76% | 0% | 64% | 13% | 0% | 45% |
| test_web_heavy | boltnet | 42% | 0% | 86% | 1% | 0% | 36% |
