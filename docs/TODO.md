# Documentation TODO - esgprep v3.0

## Pending Items

### 1. Performance Guidelines
**Impact:** MEDIUM - Optimization

**Topics to document:**

#### Hardware Recommendations
- Minimum: 4 GB RAM, 2 cores
- Recommended: 16 GB RAM, 8+ cores for large datasets
- Storage: SSD vs HDD considerations

#### Dataset Size Guidelines
```
Small (<1000 files, <100 GB):
  - Default settings work well
  - Estimated time: minutes

Medium (1000-10000 files, 100 GB - 1 TB):
  - Use --max-processes 4-8
  - Estimated time: 30 min - 2 hours

Large (>10000 files, >1 TB):
  - Use --checksums-from with pre-calculated values
  - Consider processing in batches
```

#### Benchmarks
Provide realistic timings for reference hardware.

**Status:** Waiting for real metrics

---

## Maintenance Tasks

### Documentation Updates Needed

1. **Update mapfile format documentation**
   - `concepts.rst` and `getting_started.rst` mention transition from `#YYYYMMDD` to `.vYYYYMMDD`
   - Code now uses `.vYYYYMMDD` format - update docs to reflect this as the current format
   - Remove references to `#` format as "legacy"

2. **Verify all code examples work**
   - Test commands in getting_started.rst
   - Ensure output matches current tool behavior

3. **Keep esgvoc references current**
   - Update links to esgvoc documentation
   - Verify `esgvoc install` instructions are accurate

---

*See `DONE.md` for completed items.*

*Last Updated: 2025-01-20*
