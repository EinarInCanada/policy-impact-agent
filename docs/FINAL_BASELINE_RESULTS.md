# First frozen final baseline: observed limitations

At implementation commit `8e1a75197be52bb879b5168918f53ea3fb0fd70e`, the offline final baseline completed all eight cases with zero model calls. Mean required-evidence recall over complete retrieved contexts was **0.9083**. See the [per-case compact report](results/final-baseline-01.json) and [reproduction commands](FINAL_RUN.md).

This is not answer accuracy. The pipeline includes all changed policy clauses plus bounded lexical searches; this metric is not comparable to the earlier search-only recall@3 as an improvement estimate. The corpora and denominators differ too.

Three cases missed reference evidence:

- **Cadence:** the classification definition was absent from the retrieved context (5/6 expected passages).
- **Already aligned:** the exception and revised procedure's cadence were absent (3/5). A model can still produce a convincing-looking answer without seeing both essential passages; exact citation validation alone does not prevent that semantic failure.
- **Injection/scope:** the policy's scope passage was absent (5/6). Retrieving an injection-test passage does not establish resistance to following its instructions; no model executed in this run.

The remaining five cases retrieved all annotated evidence, which still does not prove their conclusions would be correct. In particular, finding the missing-schedule clause means finding a statement that information is absent, not obtaining the missing schedule.

No retrieval/prompt tuning was performed after observing these results. Fixed-RAG and agent outcomes, costs and semantic quality remain unmeasured. The live study must report whether additional agent investigation actually recovers missing context and whether that improves adjudicated findings at an acceptable extra cost. Negative results will remain part of the report.
