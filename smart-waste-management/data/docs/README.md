# Smart Waste Management — Revised Dataset

The prediction target now represents natural future accumulation, not the
post-collection sensor state. This prevents future collection interventions
from being silently embedded in the ML label.

Pipeline:
current state -> predicted natural fill -> overflow risk -> priority ->
collection scheduling -> route optimization -> fuel/distance impact.

Future collection events remain in collection_logs.csv for the operational
layer and are not used to create target_fill_level_* values.
