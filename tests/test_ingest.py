"""Layout description, discovery patterns and manifest bookkeeping.

Nothing here touches the network: `list_year` is exercised through its parser
and its fallback, not through a request.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from airline_delays import ingest
from airline_delays.ingest import download


class TestLayouts:
    def test_every_year_2000_2013_has_a_layout(self) -> None:
        for year in range(2000, 2014):
            assert ingest.layout_for(year).name in {"legacy_12col", "wide_20col"}

    def test_the_two_layouts_split_at_2010(self) -> None:
        assert ingest.layout_for(2009) is ingest.LAYOUT_LEGACY
        assert ingest.layout_for(2010) is ingest.LAYOUT_2010

    def test_unknown_year_raises(self) -> None:
        with pytest.raises(ValueError, match="no known raw layout"):
            ingest.layout_for(1999)

    def test_declared_column_counts_match_the_declared_columns(self) -> None:
        for layout in ingest.LAYOUTS:
            assert len(layout.columns) == layout.n_columns

    def test_legacy_keeps_the_source_typo(self) -> None:
        # "Aeródromoo" with two o's is what ANAC publishes; renaming it here
        # would hide the fact that the file is what it is.
        assert "ICAO Aeródromoo Destino" in ingest.LAYOUT_LEGACY.columns

    def test_only_the_legacy_layout_carries_the_cause_as_a_code(self) -> None:
        assert ingest.LAYOUT_LEGACY.cause_is_code
        assert not ingest.LAYOUT_2010.cause_is_code


class TestMeasuredAgainstDeclared:
    """The layout constants must describe the real fixture bytes."""

    @pytest.mark.parametrize("year", [2002, 2012])
    def test_measured_layout_matches_the_declaration(self, request, year: int) -> None:
        path: Path = request.getfixturevalue(f"raw_{year}")
        measured = ingest.inspect_file(path)
        declared = ingest.layout_for(year)
        assert measured["separator"] == declared.separator
        assert measured["encoding"] == declared.encoding
        assert measured["n_columns"] == declared.n_columns
        assert measured["line_ending"] == declared.line_ending
        assert not measured["has_quotes"]

    def test_the_two_layouts_differ_in_line_ending(self, raw_2002: Path, raw_2012: Path) -> None:
        # Measured on the bytes of the files this test reads, not assumed: the
        # legacy files are CRLF and the 2010-2013 files are LF. Declaring CRLF
        # for both was wrong.
        assert ingest.LAYOUT_LEGACY.line_ending == "crlf"
        assert ingest.LAYOUT_2010.line_ending == "lf"
        assert b"\r\n" in raw_2002.read_bytes()
        assert b"\r\n" not in raw_2012.read_bytes()


class TestFixtureBytes:
    """The fixtures must reach the test as bytes, not as git's idea of them.

    `tests/fixtures/vra_raw_sample_*.csv` are cut byte for byte from the
    published ANAC files precisely so that `src/airline_delays/ingest/layouts.py`'s declared layout is
    checked against a real file. A `text`/`eol` attribute in `.gitattributes`
    rewrites line endings on checkout, which silently turns the 2002 sample
    into an LF file in every fresh clone and makes
    `TestMeasuredAgainstDeclared` fail there while passing in the author's tree
    (audit 2026-09-05, B-1). These two tests exist to name that cause instead
    of letting the failure look like a bug in the layout constants.
    """

    NORMALISED = (
        "{path} arrived with {found} line endings but the layout declares "
        "{declared}: git normalised the fixture. `.gitattributes` must keep "
        "`tests/fixtures/vra_raw_sample_*.csv -text` so these bytes survive "
        "checkout -- see audit finding B-1 in "
        "docs/audit/2026-09-05-pre-publication.md."
    )

    @pytest.mark.parametrize("year", [2002, 2012])
    def test_the_fixture_is_not_eol_normalised(self, request, year: int) -> None:
        path: Path = request.getfixturevalue(f"raw_{year}")
        declared = ingest.layout_for(year).line_ending
        found = "crlf" if b"\r\n" in path.read_bytes() else "lf"
        assert found == declared, self.NORMALISED.format(
            path=path.name, found=found, declared=declared
        )

    def test_gitattributes_exempts_the_raw_fixtures_from_eol_normalisation(self) -> None:
        rule = "tests/fixtures/vra_raw_sample_*.csv -text"
        attributes = Path(__file__).resolve().parents[1] / ".gitattributes"
        assert rule in attributes.read_text(encoding="utf-8").splitlines(), (
            f"`.gitattributes` no longer carries `{rule}`; without it the "
            "`*.csv text eol=lf` rule above rewrites the 2002 sample's CRLF on "
            "checkout and every fresh clone fails TestMeasuredAgainstDeclared "
            "-- see audit finding B-1 in docs/audit/2026-09-05-pre-publication.md."
        )

    @pytest.mark.parametrize("year", [2002, 2012])
    def test_header_reads_back_as_the_declared_columns(self, request, year: int) -> None:
        path: Path = request.getfixturevalue(f"raw_{year}")
        assert (
            tuple(ingest.read_header(path, ingest.layout_for(year)))
            == ingest.layout_for(year).columns
        )

    def test_every_data_row_has_the_declared_field_count(
        self, raw_2002: Path, raw_2012: Path
    ) -> None:
        for path, year in ((raw_2002, 2002), (raw_2012, 2012)):
            measured = ingest.inspect_file(path)
            expected = ingest.layout_for(year).n_columns
            assert set(measured["field_count_histogram"]) == {expected}, measured[
                "field_count_histogram"
            ]


class TestNaming:
    def test_the_two_known_name_patterns(self) -> None:
        assert ingest.expected_names(2007)[0] == "VRA_20071.csv"
        assert ingest.expected_names(2007)[11] == "VRA_200712.csv"
        assert ingest.expected_names(2012)[0] == "VRA_2012_01.csv"
        assert ingest.expected_names(2012)[11] == "VRA_2012_12.csv"

    def test_the_month_pattern_reads_both_shapes(self) -> None:
        assert download._MONTH_RE.search("VRA_20071.csv").groups() == ("2007", "1")
        assert download._MONTH_RE.search("VRA_2012_01.csv").groups() == ("2012", "01")

    def test_the_listing_parser_finds_hrefs(self) -> None:
        html = (
            '<pre><A HREF="/siros/registros/diversos/vra/">[To Parent Directory]</A><br>'
            '<A HREF="/siros/registros/diversos/vra/2007/VRA_20071.csv">VRA_20071.csv</A><br>'
            '<A HREF="/siros/registros/diversos/vra/2007/VRA_200710.csv">VRA_200710.csv</A></pre>'
        )
        names = sorted(Path(href).name for href in download._HREF_RE.findall(html))
        assert names == ["VRA_20071.csv", "VRA_200710.csv"]
        # The parent-directory link must not be mistaken for a data file.
        assert all(name.endswith(".csv") for name in names)


class TestManifest:
    def test_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "manifest.json"
        manifest = ingest.Manifest(path=path)
        manifest.entries["data/raw/vra/2002/VRA_20021.csv"] = ingest.ManifestEntry(
            url="https://example.invalid/VRA_20021.csv",
            file="data/raw/vra/2002/VRA_20021.csv",
            bytes=123,
            sha256="0" * 64,
            retrieved_at="2026-09-05T00:00:00+00:00",
            http_status=200,
            year=2002,
            month=1,
        )
        manifest.save()
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["n_files"] == 1
        assert document["total_bytes"] == 123
        assert set(document["files"][0]) >= {
            "url",
            "file",
            "bytes",
            "sha256",
            "retrieved_at",
            "http_status",
        }
        assert ingest.Manifest.load(path).entries.keys() == manifest.entries.keys()

    def test_sha256_of_a_known_string(self, tmp_path: Path) -> None:
        path = tmp_path / "x.txt"
        path.write_bytes(b"abc")
        assert ingest.sha256_file(path) == (
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )
