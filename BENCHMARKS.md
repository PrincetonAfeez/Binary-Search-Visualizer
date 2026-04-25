# Benchmarks

Generate fresh benchmark output with:

```powershell
bsviz bench --sizes 100,1000,10000,100000
```

Typical comparison counts for a failed classic search are logarithmic:

| Size | Comparisons |
| ---: | ---: |
| 100 | 7 |
| 1,000 | 10 |
| 10,000 | 14 |
| 100,000 | 17 |

The exact elapsed time depends on the machine, but comparison counts grow with
`log2(n)` rather than with `n`.

