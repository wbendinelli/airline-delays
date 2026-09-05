# Test fixtures

Deterministic, small slices of repository data, committed so the test suite
never needs the network, `data/raw/`, or `AIRLINE_DELAYS_PRIVATE_DIR`.

Three files, all cut from the real series by `scripts/make_fixture.py`
(`uv run airline-delays fixture`), committed once and never regenerated at test time:

- `vra_raw_sample_2002.csv` — up to 3,000 rows of the legacy 12-column
  layout (comma, latin-1, CRLF endings preserved byte for byte; the
  `.gitattributes` rule `-text` keeps git from normalising them).
- `vra_raw_sample_2012.csv` — the same for the 20-column layout
  (semicolon, UTF-8).
- `vra_sample.parquet` — staged rows for the routes SBAR-SBBR, MRSP-MRRJ
  and SBCT-MRSP cut from the 2004, 2009 and 2012 files (about 20,000
  legs; a few are dated in the following January, the ADR-0016 case, kept
  on purpose). It is what the `src/vra/` unit tests build the analysis
  layer from and what `just demo` runs end to end in about a second — an
  explicit exception to `data/staged/` being git-ignored, since this copy
  is small and stable by construction.

Nothing under this directory is generated from `data/raw/` or
`data/private/` at test time — only checked in, once, by the script that
built it.
