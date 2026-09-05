# data/staged/

The canonical flight table, one partition per year:
`year=YYYY/part-0.parquet`, zstd level 9, tight types (see the staged flight
schema in the build brief and `src/vra/io.py`/`stage.py`). Produced by
`just stage` from `data/raw/` plus `data/external/`.

Git-ignored except for this README (see `.gitignore`): this table is
250-290 MB across the full 2000-2013 range, regenerated locally by
`just stage`, and deposited to Zenodo once the licence confirmation closes
(`DECISIONS.md` ADR-0000, `ROADMAP.md` phase 7) rather than committed here.
