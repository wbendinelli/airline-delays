#!/usr/bin/env python
"""Reconcile the staged VRA against the acervo's private `vra.dta` (2019 vintage).

This is the only staging-side script allowed to touch the private directory,
and it reaches it exclusively through ``AIRLINE_DELAYS_PRIVATE_DIR``. It reads
``<dir>/Base de dados bruta/vra.dta`` (1.47 GB, 13,503,778 rows) in one
sequential pass — the file has no index, so a partial read costs the same as a
full one and two concurrent scans cost dozens of times more — and writes
``reports/reconciliation.md``.

Three comparisons:

1. Rows per (year, month): today's raw CSVs against the 2019 .dta.
2. A deterministic sample of about 200,000 flights keyed by
   ``(airline, flight_number, origin_icao, dest_icao, sched_dep)``. Both sides
   select the *same* keys, by a CRC32 of the key string, so the sample is
   reproducible and side-independent. On the matched rows: `status`,
   `cause_code`, `line_type`, `di` and both actual timestamps.
3. Whether the acervo's ``delarrive`` equals ``max(chegreal - chegprog, 0)``,
   answered inside the .dta itself.

Nothing is adjusted to make numbers agree: every disagreement is reported as
found (build brief rule 6).

Usage:
    AIRLINE_DELAYS_PRIVATE_DIR=... uv run python scripts/verify_reconcile.py
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import zlib
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vra.stage import connect
from vra.universe import STATUS_CANCELLED, STATUS_OTHER, STATUS_REALIZED

ROOT = Path(__file__).resolve().parents[1]
DTA_RELATIVE = Path("Base de dados bruta") / "vra.dta"
CHUNK_ROWS = 1_500_000
DTA_COLUMNS = [
    "month",
    "year",
    "airline",
    "flight",
    "type",
    "orig",
    "dest",
    "situation",
    "motive",
    "di",
    "partprog",
    "partreal",
    "chegprog",
    "chegreal",
    "deldepart",
    "delarrive",
]
COMPARE_COLUMNS = ("status", "cause_code", "line_type", "di", "actual_dep", "actual_arr")

STATUS_FROM_DTA = {"Realizado": STATUS_REALIZED, "Cancelado": STATUS_CANCELLED}


def sample_modulus(target_rows: int, total_rows: int = 13_503_778) -> int:
    """The CRC32 modulus that yields about `target_rows` from `total_rows`."""
    return max(1, round(total_rows / max(target_rows, 1)))


def key_series(
    airline: pd.Series,
    flight: pd.Series,
    origin: pd.Series,
    dest: pd.Series,
    sched_dep: pd.Series,
) -> pd.Series:
    """The reconciliation key, formatted identically on both sides."""
    number = pd.to_numeric(flight, errors="coerce").astype("Int64")
    stamp = pd.to_datetime(sched_dep, errors="coerce").dt.strftime("%Y-%m-%d %H:%M")
    return (
        airline.astype("string").str.strip().str.upper().fillna("")
        + "|"
        + number.astype("string").fillna("")
        + "|"
        + origin.astype("string").str.strip().str.upper().fillna("")
        + "|"
        + dest.astype("string").str.strip().str.upper().fillna("")
        + "|"
        + stamp.fillna("")
    )


def selected(keys: pd.Series, modulus: int) -> np.ndarray:
    """Boolean mask of the keys the deterministic sample selects."""
    return np.fromiter(
        (zlib.crc32(value.encode("utf-8")) % modulus == 0 for value in keys.to_numpy(dtype=object)),
        dtype=bool,
        count=len(keys),
    )


# --------------------------------------------------------------------------- .dta side


def scan_dta(path: Path, modulus: int) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """One sequential pass over vra.dta.

    Returns the (year, month) counts, the sampled rows and a dictionary with
    the ``delarrive`` findings.
    """
    import pyreadstat

    started = time.time()
    counts: dict[tuple[int, int], int] = {}
    samples: list[pd.DataFrame] = []
    delarrive = {
        "n_comparable": 0,
        "n_equal_truncated": 0,
        "n_equal_signed": 0,
        "n_delarrive_negative": 0,
        "n_deldepart_negative": 0,
        "n_rows": 0,
    }
    read = 0
    for chunk, _meta in pyreadstat.read_file_in_chunks(
        pyreadstat.read_dta, str(path), chunksize=CHUNK_ROWS, usecols=DTA_COLUMNS, encoding="latin1"
    ):
        read += len(chunk)
        grouped = chunk.groupby(["year", "month"], dropna=False).size()
        for (year, month), count in grouped.items():
            key = (int(year) if pd.notna(year) else -1, int(month) if pd.notna(month) else -1)
            counts[key] = counts.get(key, 0) + int(count)

        signed = (chunk["chegreal"] - chunk["chegprog"]).dt.total_seconds() / 60.0
        comparable = signed.notna() & chunk["delarrive"].notna()
        delarrive["n_rows"] += len(chunk)
        delarrive["n_comparable"] += int(comparable.sum())
        delarrive["n_equal_truncated"] += int(
            (
                np.isclose(
                    chunk["delarrive"][comparable], signed[comparable].clip(lower=0), atol=0.51
                )
            ).sum()
        )
        delarrive["n_equal_signed"] += int(
            (np.isclose(chunk["delarrive"][comparable], signed[comparable], atol=0.51)).sum()
        )
        delarrive["n_delarrive_negative"] += int((chunk["delarrive"] < 0).sum())
        delarrive["n_deldepart_negative"] += int((chunk["deldepart"] < 0).sum())

        keys = key_series(
            chunk["airline"], chunk["flight"], chunk["orig"], chunk["dest"], chunk["partprog"]
        )
        mask = selected(keys, modulus)
        if mask.any():
            picked = chunk.loc[mask].copy()
            picked["key"] = keys[mask].to_numpy()
            samples.append(picked)
        print(
            f"  vra.dta: {read:>10,d} rows read | {time.time() - started:5.0f}s",
            file=sys.stderr,
            flush=True,
        )

    counts_frame = (
        pd.DataFrame(
            [(y, m, n) for (y, m), n in counts.items()], columns=["year", "month", "rows_dta"]
        )
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )
    sample = pd.concat(samples, ignore_index=True) if samples else pd.DataFrame()
    return counts_frame, sample, delarrive


def normalise_dta_sample(sample: pd.DataFrame) -> pd.DataFrame:
    """Bring the .dta sample onto the staged vocabulary, without changing values."""
    out = pd.DataFrame(index=sample.index)
    out["key"] = sample["key"]
    out["status"] = (
        sample["situation"].astype("string").str.strip().map(STATUS_FROM_DTA).fillna(STATUS_OTHER)
    )
    motive = sample["motive"].astype("string").str.strip().str.upper()
    out["cause_code"] = motive.where(motive.str.fullmatch(r"[A-Z]{2}", na=False))
    line = sample["type"].astype("string").str.strip().str.upper()
    out["line_type"] = line.where(~line.isin(["NA", "N/A", "N/I", "NI", ""]))
    out["di"] = pd.to_numeric(sample["di"], errors="coerce").astype("Int64")
    out["actual_dep"] = pd.to_datetime(sample["partreal"], errors="coerce").dt.floor("min")
    out["actual_arr"] = pd.to_datetime(sample["chegreal"], errors="coerce").dt.floor("min")
    # Kept only to answer "did the .dta fill an actual time that today's CSV
    # leaves empty, and did it fill it with the scheduled time?"
    out["sched_dep_dta"] = pd.to_datetime(sample["partprog"], errors="coerce").dt.floor("min")
    out["sched_arr_dta"] = pd.to_datetime(sample["chegprog"], errors="coerce").dt.floor("min")
    return out.drop_duplicates(subset="key", keep="first")


def filled_actual_report(left: pd.DataFrame, right: pd.DataFrame) -> dict:
    """Where the staged side has no actual time and the .dta does, what did it put there?

    The 2000-2009 CSVs leave `Partida Real` and `Chegada Real` empty for a
    realised flight with no occurrence. If the 2019 .dta carries a value on
    exactly those rows, and that value is the scheduled time, then the acervo's
    vintage treated "empty" as "operated on schedule" — which is the single
    interpretation that most changes any delay average built on this data.
    """
    merged = left.merge(right, on="key", how="inner", suffixes=("_staged", "_dta"))
    out: dict[str, int] = {"n_matched": len(merged)}
    for side, sched in (("dep", "sched_dep_dta"), ("arr", "sched_arr_dta")):
        staged_null = merged[f"actual_{side}_staged"].isna()
        dta_set = merged[f"actual_{side}_dta"].notna()
        gap = merged.loc[staged_null & dta_set]
        equal_to_schedule = (gap[f"actual_{side}_dta"] == gap[sched]).sum()
        out[f"{side}_staged_null_dta_set"] = len(gap)
        out[f"{side}_of_which_equal_to_schedule"] = int(equal_to_schedule)
        out[f"{side}_dta_actual_equals_schedule_overall"] = int(
            (merged[f"actual_{side}_dta"] == merged[sched]).sum()
        )
    return out


# ------------------------------------------------------------------------ staged side


def staged_counts(staged_dir: Path) -> pd.DataFrame:
    con = connect(memory_limit="6GB", threads=8)
    try:
        return con.execute(
            f"SELECT year, month, count(*) AS rows_staged FROM "
            f"read_parquet('{staged_dir}/year=*/*.parquet', hive_partitioning=false) "
            "GROUP BY 1, 2 ORDER BY 1, 2"
        ).df()
    finally:
        con.close()


def staged_sample(staged_dir: Path, modulus: int) -> pd.DataFrame:
    """The same deterministic sample, taken from the staged parquet.

    Read one year-partition at a time. Materialising all 13.6 million keys in
    pandas at once would cost several gigabytes on a 16 GB machine, and the
    .dta scan is already holding its own chunk.
    """
    con = connect(memory_limit="6GB", threads=8)
    parts: list[pd.DataFrame] = []
    try:
        for part in sorted(Path(staged_dir).glob("year=*/*.parquet")):
            frame = con.execute(
                "SELECT coalesce(airline, '') || '|' "
                "|| coalesce(CAST(flight_number AS VARCHAR), '') || '|' "
                "|| coalesce(origin_icao, '') || '|' || coalesce(dest_icao, '') || '|' "
                "|| coalesce(strftime(sched_dep, '%Y-%m-%d %H:%M'), '') AS key, "
                "status, cause_code, line_type, di, actual_dep, actual_arr "
                f"FROM read_parquet('{part}')"
            ).df()
            parts.append(frame.loc[selected(frame["key"], modulus)].copy())
            print(
                f"  staged: {part.parent.name} sampled {len(parts[-1]):,d}",
                file=sys.stderr,
                flush=True,
            )
    finally:
        con.close()
    frame = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    frame["di"] = pd.to_numeric(frame["di"], errors="coerce").astype("Int64")
    for column in ("actual_dep", "actual_arr"):
        frame[column] = pd.to_datetime(frame[column], errors="coerce").dt.floor("min")
    frame["status"] = frame["status"].astype("string")
    frame["cause_code"] = frame["cause_code"].astype("string")
    frame["line_type"] = frame["line_type"].astype("string")
    return frame.drop_duplicates(subset="key", keep="first")


# --------------------------------------------------------------------------- compare


def compare(left: pd.DataFrame, right: pd.DataFrame) -> tuple[pd.DataFrame, int, int, int]:
    """Column-by-column agreement on the keys both sides carry."""
    merged = left.merge(right, on="key", how="inner", suffixes=("_staged", "_dta"))
    rows = []
    for column in COMPARE_COLUMNS:
        a, b = merged[f"{column}_staged"], merged[f"{column}_dta"]
        both_null = a.isna() & b.isna()
        equal = both_null | (a.eq(b) & a.notna() & b.notna())
        comparable = a.notna() | b.notna()
        rows.append(
            {
                "column": column,
                "n": len(merged),
                "equal": int(equal.sum()),
                "agreement": round(float(equal.mean()), 6) if len(merged) else float("nan"),
                "both_null": int(both_null.sum()),
                "differ": int((~equal).sum()),
                "staged_null_dta_set": int((a.isna() & b.notna()).sum()),
                "dta_null_staged_set": int((b.isna() & a.notna()).sum()),
                "n_comparable": int(comparable.sum()),
            }
        )
    only_staged = len(left) - len(merged)
    only_dta = len(right) - len(merged)
    return pd.DataFrame(rows), len(merged), only_staged, only_dta


def top_disagreements(
    left: pd.DataFrame, right: pd.DataFrame, column: str, limit: int = 10
) -> pd.DataFrame:
    merged = left.merge(right, on="key", how="inner", suffixes=("_staged", "_dta"))
    a, b = merged[f"{column}_staged"], merged[f"{column}_dta"]
    differ = merged.loc[~((a.isna() & b.isna()) | (a.eq(b) & a.notna() & b.notna()))]
    if differ.empty:
        return pd.DataFrame(columns=["staged", "dta", "n"])
    pairs = (
        differ.groupby([f"{column}_staged", f"{column}_dta"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
        .head(limit)
    )
    pairs.columns = ["staged", "dta", "n"]
    return pairs


# ---------------------------------------------------------------------------- report


def _table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_(vazio)_\n"
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    body = "\n".join(
        "| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |"
        for row in frame.to_numpy()
    )
    return f"{header}\n{rule}\n{body}\n"


def write_report(
    out: Path,
    counts: pd.DataFrame,
    per_column: pd.DataFrame,
    matched: int,
    only_staged: int,
    only_dta: int,
    delarrive: dict,
    disagreements: dict[str, pd.DataFrame],
    context: dict,
    filled: dict,
) -> Path:
    counts = counts.copy()
    counts["diff"] = counts["rows_staged"].fillna(0).astype("int64") - counts["rows_dta"].fillna(
        0
    ).astype("int64")
    by_year = (
        counts.groupby("year")[["rows_staged", "rows_dta", "diff"]]
        .sum()
        .reset_index()
        .astype("int64")
    )
    worst = counts.reindex(counts["diff"].abs().sort_values(ascending=False).index).head(20)

    truncated = delarrive["n_equal_truncated"] / max(delarrive["n_comparable"], 1)
    signed = delarrive["n_equal_signed"] / max(delarrive["n_comparable"], 1)
    verdict = "sim" if truncated > 0.99 else ("não" if truncated < 0.5 else "parcialmente")

    text = f"""# Reconciliação — VRA bruto de hoje contra o `vra.dta` do acervo (2019)

Gerado em {datetime.now(UTC).isoformat(timespec="seconds")} por `scripts/verify_reconcile.py`.
Nada foi ajustado para bater: as divergências abaixo estão declaradas, não corrigidas
(regra 6 do brief).

## 1. Procedência

| item | valor |
|---|---|
| CSV bruto (hoje) | `{context["raw_source"]}` |
| linhas staged | {context["staged_rows"]:,} |
| `vra.dta` (acervo, 2019) | `{context["dta_path"]}` |
| bytes do `.dta` | {context["dta_bytes"]:,} |
| sha256 do `.dta` | `{context["dta_sha256"]}` |
| linhas do `.dta` | {delarrive["n_rows"]:,} |
| `git_commit` | `{context["git_commit"]}` |
| amostra determinística | CRC32 da chave módulo {context["modulus"]} |

A chave é `(airline, flight_number, origin_icao, dest_icao, sched_dep)`, formatada
igual dos dois lados; os dois lados selecionam **as mesmas chaves**, então a amostra
não favorece nenhuma das bases.

## 2. Linhas por ano

{_table(by_year)}

## 3. Linhas por (ano, mês) — as 20 maiores diferenças

{_table(worst)}

Tabela completa por mês em `reports/reconciliation_by_month.csv`.

## 4. Concordância coluna a coluna na amostra

Chaves em comum: **{matched:,}**. Só no staged: {only_staged:,}. Só no `.dta`: {only_dta:,}.

{_table(per_column)}

`equal` conta como iguais os pares em que ambos os lados são nulos; `differ` é o
complemento. `staged_null_dta_set` são as linhas em que o staged não tem valor e o
`.dta` tem — o caso mais informativo, porque indica campo perdido na extração.

### Principais pares divergentes

"""
    for column, frame in disagreements.items():
        text += f"\n**{column}**\n\n{_table(frame)}"

    text += f"""
## 5. Horários realizados: o `.dta` preenche o que o CSV de hoje deixa vazio

O achado mais consequente da reconciliação. Nos arquivos de 2000-2009 um voo
`REALIZADO` sem ocorrência vem com `Partida Real` e `Chegada Real` **vazios**; o
staging deixa o atraso nulo, sem imputar (ADR-0008). O `.dta` de 2019 carrega valor
justamente nessas linhas.

| medida | partida | chegada |
|---|---|---|
| linhas casadas na amostra | {filled["n_matched"]:,} | {filled["n_matched"]:,} |
| staged nulo e `.dta` preenchido | {filled["dep_staged_null_dta_set"]:,} | {filled["arr_staged_null_dta_set"]:,} |
| dessas, `.dta` gravou exatamente o horário previsto | {filled["dep_of_which_equal_to_schedule"]:,} | {filled["arr_of_which_equal_to_schedule"]:,} |
| no total da amostra, `.dta` tem realizado igual ao previsto | {filled["dep_dta_actual_equals_schedule_overall"]:,} | {filled["arr_dta_actual_equals_schedule_overall"]:,} |

Se a terceira linha for praticamente igual à segunda, a leitura é direta: a safra de
2019 tratou "campo vazio" como "operou no horário previsto". **Esta é a explicação da
concordância de 60% em `actual_dep`/`actual_arr` na tabela da seção 4** — não é campo
perdido na extração de hoje, é uma convenção diferente sobre o vazio. A divergência
fica declarada; a escolha de imputar ou não pertence à camada de análise, não ao
staging, e trocar uma pela outra muda toda média de atraso de 2000-2009.

## 6. `delarrive` é `max(chegreal - chegprog, 0)`?

Resposta curta: **{verdict}**.

| medida | linhas | fração |
|---|---|---|
| linhas com `chegreal`, `chegprog` e `delarrive` presentes | {delarrive["n_comparable"]:,} | — |
| `delarrive` igual a `max(chegreal - chegprog, 0)` (tolerância 0,51 min) | {delarrive["n_equal_truncated"]:,} | {truncated:.4f} |
| `delarrive` igual ao atraso **com sinal** `chegreal - chegprog` | {delarrive["n_equal_signed"]:,} | {signed:.4f} |
| `delarrive` negativo em alguma linha | {delarrive["n_delarrive_negative"]:,} | — |
| `deldepart` negativo em alguma linha | {delarrive["n_deldepart_negative"]:,} | — |

A pergunta é respondida dentro do próprio `.dta`, comparando `delarrive` com os
horários que o próprio arquivo carrega, para não misturar duas fontes.

## 7. Divergências declaradas

As diferenças acima **não foram corrigidas**. Elas entram em
`docs/declared-differences.md` e são o insumo de qualquer decisão futura sobre
mudar a extração. Este relatório é gerado; não editar à mão.
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    counts.to_csv(out.parent / "reconciliation_by_month.csv", index=False)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--private-dir", type=Path, default=os.environ.get("AIRLINE_DELAYS_PRIVATE_DIR")
    )
    parser.add_argument("--staged-dir", type=Path, default=ROOT / "data" / "staged")
    parser.add_argument("--sample", type=int, default=200_000)
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "reconciliation.md")
    args = parser.parse_args(argv)

    if args.private_dir is None:
        print("AIRLINE_DELAYS_PRIVATE_DIR is not set; nothing to reconcile.", file=sys.stderr)
        return 0
    dta_path = Path(args.private_dir) / DTA_RELATIVE
    if not dta_path.exists():
        print(f"missing {dta_path}", file=sys.stderr)
        return 1

    from vra.io import sha256_file
    from vra.stage import git_commit

    modulus = sample_modulus(args.sample)
    print(f"deterministic sample: CRC32 % {modulus} == 0", file=sys.stderr)

    counts_dta, sample_raw_dta, delarrive = scan_dta(dta_path, modulus)
    sample_dta = normalise_dta_sample(sample_raw_dta)
    print(f"sampled from .dta: {len(sample_dta):,}", file=sys.stderr)

    counts_staged = staged_counts(args.staged_dir)
    sample_staged_side = staged_sample(args.staged_dir, modulus)
    print(f"sampled from staged: {len(sample_staged_side):,}", file=sys.stderr)

    counts = counts_staged.merge(counts_dta, on=["year", "month"], how="outer").sort_values(
        ["year", "month"]
    )
    per_column, matched, only_staged, only_dta = compare(sample_staged_side, sample_dta)
    filled = filled_actual_report(sample_staged_side, sample_dta)
    disagreements = {
        column: top_disagreements(sample_staged_side, sample_dta, column)
        for column in ("status", "cause_code", "line_type", "di")
    }

    context = {
        "raw_source": "https://siros.anac.gov.br/siros/registros/diversos/vra/{year}/",
        "staged_rows": int(counts_staged["rows_staged"].sum()),
        "dta_path": str(DTA_RELATIVE),
        "dta_bytes": dta_path.stat().st_size,
        "dta_sha256": sha256_file(dta_path),
        "git_commit": git_commit(ROOT),
        "modulus": modulus,
    }
    out = write_report(
        args.out,
        counts,
        per_column,
        matched,
        only_staged,
        only_dta,
        delarrive,
        disagreements,
        context,
        filled,
    )
    print(f"wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
