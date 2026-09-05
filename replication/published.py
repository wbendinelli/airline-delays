"""Parse the published Tables 2-7 out of the article text into ``published.json``.

The comparison target of this phase is the printed article: Bendinelli, Bettini
and Oliveira (2016), *Airline delays, congestion internalization and non-price
spillover effects of low cost carrier entry*, Transportation Research Part A 85,
39-52, `10.1016/j.tra.2016.01.001 <https://doi.org/10.1016/j.tra.2016.01.001>`_.
Typing those numbers by hand would put ~700 unversioned figures into the
repository, so they are parsed **once** from the article's text layer and
committed as ``replication/published.json``; every comparison downstream reads
that file. The text layer itself is not redistributed here (it is the
publisher's copyrighted typesetting); point ``--source-text`` at your own copy,
or set ``AIRLINE_DELAYS_SOURCE_TEXT``.

Run::

    uv run python -m replication.published --source-text /path/to/airline.txt

The parser is positional, not token-order based: a coefficient row may leave
cells blank (Table 4 omits regressors column by column), so each numeric token
is assigned to the nearest column anchor taken from the table's ``(1) (2) ...``
header line. Standard errors sit on the line below their coefficients, in
brackets. Significance stars are stripped into a separate ``stars`` field.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PUBLISHED_JSON = HERE / "published.json"
SOURCE_TEXT_VAR = "AIRLINE_DELAYS_SOURCE_TEXT"

CITATION = {
    "authors": "Bendinelli, W. E.; Bettini, H. F. A. J.; Oliveira, A. V. M.",
    "title": (
        "Airline delays, congestion internalization and non-price spillover "
        "effects of low cost carrier entry"
    ),
    "journal": "Transportation Research Part A: Policy and Practice",
    "volume": "85",
    "pages": "39-52",
    "year": 2016,
    "doi": "10.1016/j.tra.2016.01.001",
}

#: Article row label -> the variable name used throughout ``replication/``.
COEFFICIENT_ROWS: dict[str, str] = {
    "nr flights in congested hours": "dailyflcong",
    "nr flights in uncongested hours": "dailyflncong",
    "prop flights with bad weather": "prwheather",
    "prop flights with incidents": "princident",
    "prop flights held for late connections": "pr_connc",
    "max prop city delayed flights": "maxprdel",
    "codeshare agreement": "cshare",
    "hhi city-pair": "rthhi",
    "hhi max endpoint cities": "maxcthhi",
    "lcc presence city-pair": "lcc",
    "lcc presence max endpoint cities": "maxalccfu",
}

#: Article statistics-row label -> key in the parsed ``stats`` mapping.
STAT_ROWS: dict[str, str] = {
    "adj. r-squared": "adj_r2",
    "rmse statistic": "rmse",
    "f statistic": "f_stat",
    "kp statistic": "kp_lm",
    "kp p-value": "kp_p",
    "j statistic": "j_stat",
    "j p-value": "j_p",
    "weak cd statistic": "weak_cd_f",
    "weak kp statistic": "weak_kp_f",
    "nr observations": "n_obs",
}

#: The 13 variables of Table 2, in the order the article numbers them.
TABLE2_VARIABLES: tuple[str, ...] = (
    "dailyflcong",
    "dailyflncong",
    "prwheather",
    "princident",
    "pr_connc",
    "maxprdel",
    "cshare",
    "rthhi",
    "maxcthhi",
    "lcc",
    "maxalccfu",
    "fsc_oddsarr",
    "fsc_minsarr",
)
TABLE2_STATS: dict[str, str] = {
    "mean": "mean",
    "standard deviation": "sd",
    "minimum": "min",
    "maximum": "max",
}

_MINUS = "−"  # the article's typographic minus sign
_NUMBER = re.compile(r"[−\-]?\d+(?:[.,]\d+)*\*{0,3}")
_BRACKETED = re.compile(r"\[\s*([−\-]?\d+(?:\.\d+)?)\s*\]")
_ANCHOR = re.compile(r"\((\d{1,2})\)")


def _clean_label(text: str) -> str:
    """Normalise a row label: lowercase, single spaces, no stars, no trailing punctuation."""
    text = text.replace("*", " ").replace(_MINUS, "-")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text.rstrip(" .:")


def _to_float(token: str) -> tuple[float, str]:
    """A numeric token to ``(value, stars)``; handles the typographic minus and thousands commas."""
    stars = "*" * token.count("*")
    body = token.replace("*", "").replace(_MINUS, "-").replace(",", "")
    return float(body), stars


@dataclass(frozen=True)
class _Table:
    """One raw table block: its header anchors and the lines that follow."""

    number: int
    caption: str
    anchors: list[int]
    header_line: str
    lines: list[str]


def _split_tables(text: str) -> dict[int, _Table]:
    """Cut the article text into the blocks that start at a ``Table N`` line."""
    lines = text.splitlines()
    starts: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"\s*Table\s+(\d)\s*", line)
        if match and index + 1 < len(lines):
            starts.append((index, int(match.group(1)), lines[index + 1].strip()))
    tables: dict[int, _Table] = {}
    for position, (index, number, caption) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        block = lines[index:end]
        header_index = next(
            (i for i, line in enumerate(block) if len(_ANCHOR.findall(line)) >= 6),
            None,
        )
        if header_index is None:
            continue
        header = block[header_index]
        anchors = [match.start() for match in _ANCHOR.finditer(header)]
        tables[number] = _Table(number, caption, anchors, header, block[header_index + 1 :])
    return tables


def _cells(line: str, anchors: list[int], *, bracketed: bool) -> dict[int, str]:
    """Assign every numeric token on `line` to the column whose anchor is nearest."""
    pattern = _BRACKETED if bracketed else _NUMBER
    out: dict[int, str] = {}
    for match in pattern.finditer(line):
        start = match.start()
        column = min(range(len(anchors)), key=lambda i: abs(anchors[i] - start))
        out[column] = match.group(1) if bracketed else match.group(0)
    return out


def _parse_regression_table(table: _Table, n_columns: int) -> dict[str, Any]:
    """Tables 3-7: coefficients with bracketed standard errors, then the statistics rows."""
    columns: dict[str, dict[str, Any]] = {
        str(i + 1): {"regressand": None, "b": {}, "se": {}, "stars": {}, "stats": {}}
        for i in range(n_columns)
    }
    anchors = table.anchors[:n_columns]
    lines = table.lines

    # The regressand names sit on the first line after the header.
    for line in lines:
        tokens = [token for token in re.split(r"\s{2,}", line.strip()) if token]
        if tokens and all(re.fullmatch(r"(ODDS|MINS)D?(\s*>\s*15)?", t) for t in tokens):
            positions = [m.start() for m in re.finditer(r"(ODDS|MINS)D?", line)]
            for token, start in zip(tokens, positions, strict=False):
                column = min(range(len(anchors)), key=lambda i: abs(anchors[i] - start))
                columns[str(column + 1)]["regressand"] = re.sub(r"\s+", " ", token)
            break

    for index, line in enumerate(lines):
        label_end = min((m.start() for m in _NUMBER.finditer(line)), default=len(line))
        label = _clean_label(line[:label_end])
        if label in COEFFICIENT_ROWS:
            variable = COEFFICIENT_ROWS[label]
            for column, token in _cells(line, anchors, bracketed=False).items():
                value, stars = _to_float(token)
                columns[str(column + 1)]["b"][variable] = value
                columns[str(column + 1)]["stars"][variable] = stars
            following = lines[index + 1] if index + 1 < len(lines) else ""
            if "[" in following:
                for column, token in _cells(following, anchors, bracketed=True).items():
                    columns[str(column + 1)]["se"][variable] = _to_float(token)[0]
        elif label in STAT_ROWS:
            key = STAT_ROWS[label]
            for column, token in _cells(line, anchors, bracketed=False).items():
                value = _to_float(token)[0]
                columns[str(column + 1)]["stats"][key] = int(value) if key == "n_obs" else value

    return {"caption": table.caption, "n_columns": n_columns, "columns": columns}


def _parse_table2(table: _Table) -> dict[str, Any]:
    """Table 2: the 13x13 Pearson correlation triangle plus the four univariate rows."""
    correlation: dict[str, dict[str, float]] = {}
    univariate: dict[str, dict[str, float]] = {}
    current: str | None = None
    section = "correlation"
    for line in table.lines:
        stripped = line.strip()
        if not stripped:
            continue
        lowered = _clean_label(stripped)
        if lowered.startswith("univariate statistics"):
            section = "univariate"
            continue
        if lowered.startswith("pearson correlation"):
            section = "correlation"
            continue
        if section == "correlation":
            marker = _ANCHOR.search(line)
            if marker and marker.start() > 5:
                index = int(marker.group(1))
                if not 1 <= index <= len(TABLE2_VARIABLES):
                    continue
                current = TABLE2_VARIABLES[index - 1]
                values = [_to_float(m.group(0))[0] for m in _NUMBER.finditer(line[marker.end() :])]
                correlation[current] = {
                    TABLE2_VARIABLES[position]: value for position, value in enumerate(values)
                }
            elif current is None:
                continue
        else:
            for label, key in TABLE2_STATS.items():
                if lowered.startswith(label):
                    values = [_to_float(m.group(0))[0] for m in _NUMBER.finditer(line)]
                    univariate[key] = dict(zip(TABLE2_VARIABLES, values, strict=False))
    return {
        "caption": table.caption,
        "variables": list(TABLE2_VARIABLES),
        "correlation": correlation,
        "univariate": univariate,
    }


def parse(source_text: Path) -> dict[str, Any]:
    """Parse Tables 2-7 out of the article's text layer."""
    tables = _split_tables(source_text.read_text(encoding="utf-8", errors="replace"))
    missing = [number for number in (2, 3, 4, 5, 6, 7) if number not in tables]
    if missing:
        raise ValueError(f"{source_text}: could not locate published table(s) {missing}")
    return {
        "source": {
            "citation": CITATION,
            "parsed_from": source_text.name,
            "parser": "replication/published.py",
        },
        "table2": _parse_table2(tables[2]),
        "table3": _parse_regression_table(tables[3], 6),
        "table4": _parse_regression_table(tables[4], 7),
        "table5": _parse_regression_table(tables[5], 6),
        "table6": _parse_regression_table(tables[6], 6),
        "table7": _parse_regression_table(tables[7], 6),
    }


def load(path: Path = PUBLISHED_JSON) -> dict[str, Any]:
    """The committed published numbers. Raises with a usable message if absent."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist -- regenerate it with "
            f"`uv run python -m replication.published --source-text <airline.txt>`"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_source_text(argument: str | None) -> Path:
    candidate = argument or os.environ.get(SOURCE_TEXT_VAR)
    if not candidate:
        raise SystemExit(
            "the article text layer is not redistributed with this repository; pass "
            f"--source-text /path/to/airline.txt or set {SOURCE_TEXT_VAR}"
        )
    path = Path(candidate).expanduser()
    if not path.exists():
        raise SystemExit(f"{path} does not exist")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-text", default=None, help="text layer of the published article")
    parser.add_argument("--out", default=str(PUBLISHED_JSON), help="where to write the JSON")
    args = parser.parse_args(argv)
    parsed = parse(_resolve_source_text(args.source_text))
    out = Path(args.out)
    out.write_text(json.dumps(parsed, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = {
        name: len(block.get("columns", {})) for name, block in parsed.items() if name != "source"
    }
    print(f"wrote {out} -- columns per table: {counts}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
