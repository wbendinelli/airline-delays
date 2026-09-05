"""The scientific definitions every stage shares, one ADR each.

`nodes` (ADR-0001), `universe` (ADR-0002), `carriers` (ADR-0003, 0011, 0013),
`cause_codes` (ADR-0005), `congestion` (ADR-0007), `delays` (ADR-0008, 0012,
0015), `concentration` and `hubs`. Nothing here reads or writes data; the
stages import these definitions and apply them. Changing one is a decision
recorded in `DECISIONS.md`, never a patch.
"""
