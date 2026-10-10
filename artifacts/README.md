# Runtime research artifacts

The web application reads final scientific outputs from machine-readable artifacts.
These files must be generated or exported from the validated research pipeline; the
web application must not compute replacement metrics or train a model.

Default paths:

- `artifacts/final_metrics.json`
- `artifacts/benchmark.json`

Both paths can be overridden with environment variables:

- `TURKDET_METRICS_PATH`
- `TURKDET_BENCHMARK_PATH`

The production model artifact path is configured separately with
`TURKDET_MODEL_PATH`.

## Suggested `final_metrics.json` shape

```json
{
  "auc": 0.0,
  "f1": 0.0,
  "accuracy": 0.0,
  "precision": 0.0,
  "recall": 0.0,
  "fpr": 0.0,
  "brier": 0.0,
  "log_loss": 0.0,
  "ece": 0.0,
  "confusion_matrix": [[0, 0], [0, 0]],
  "roc": {"fpr": [], "tpr": []}
}
```

The numbers above document the schema only. Do not commit placeholder zeros as if
they were experimental results.
