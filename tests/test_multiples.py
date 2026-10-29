"""Offline tests: a tiny fixture shaped like https://exitvalue.ai/data/multiples.json."""

from exitvalue_mcp import multiples as m

DS = {
    "min_cell_n": 10,
    "source_window": "2018-2026",
    "data": {
        "dental-practice": {
            "5m_25m_ev": {"ev_ebitda": {"n": 10, "p25": 6.5, "p50": 7.0, "p75": 8.3}},
            "25m_100m_ev": {"ev_ebitda": {"n": 9, "p25": 8.0, "p50": 9.0, "p75": 10.0}},  # below min_cell_n
        },
        "it-services": {"5m_25m_ev": {"ev_revenue": {"n": 28, "p25": 0.35, "p50": 0.89, "p75": 1.36}}},
    },
}


def test_aliases_resolve():
    assert m.resolve("dentist") == ("sv", "dental-practice")
    assert m.resolve("Dental practices") == ("sv", "dental-practice")
    assert m.resolve("plumber") == ("sv", "hvac")
    assert m.resolve("med spa") == ("sv", "other-healthcare")
    assert m.resolve("healthcare") == ("industry", "healthcare")


def test_withholds_small_cells_and_links_calculator():
    out = m.get_valuation_multiples(DS, "dentist")
    assert "EV/EBITDA median 7.0x (middle 50%: 6.5x-8.3x), n=10" in out
    assert "9.0x" not in out  # n=9 < min_cell_n is withheld
    assert "SEC EDGAR filings and verified press releases" in out
    assert out.rstrip().endswith("https://exitvalue.ai/valuate?src=mcp-oss&industry=dental-practice")


def test_no_data_is_honest():
    out = m.get_valuation_multiples(DS, "landscaping")
    assert "no median is published" in out
    assert "median " not in out.split("no median")[0]


def test_parent_category_and_bracket():
    out = m.get_valuation_multiples(DS, "msp", "5m_25m_ev")
    assert "IT services" in out and "0.89x" in out


def test_dataset_cache_fetches_once():
    calls = []
    ds = m.Dataset(fetch=lambda: calls.append(1) or DS, ttl=3600)
    ds.get(), ds.get()
    assert len(calls) == 1
