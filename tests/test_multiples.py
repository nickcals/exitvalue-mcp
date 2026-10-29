"""Offline tests: a tiny fixture shaped like https://exitvalue.ai/data/multiples.json."""

import re

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


TREND = {
    "min_n_per_cell": 10,
    "year_range": [2018, 2026],
    "data": {
        "saas": {
            "2019": {"ev_revenue": {"n": 46, "p25": 1.98, "p50": 3.58, "p75": 7.74},
                     "ev_ebitda": {"n": 19, "p25": 13.82, "p50": 19.29, "p75": 38.13},
                     "median_deal_value_m": 63.57, "n_deals": 46},
            "2021": {"ev_revenue": {"n": 64, "p25": 2.49, "p50": 5.61, "p75": 10.78},
                     "ev_ebitda": {"n": 9, "p25": 12.0, "p50": 30.5, "p75": 58.0},  # below min n
                     "n_deals": 64},
        },
        "it-services": {"2022": {"ev_revenue": {"n": 25, "p25": 0.79, "p50": 1.92, "p75": 3.41}, "n_deals": 25}},
    },
}


def test_compare_side_by_side_and_insufficient():
    out = m.compare_industries(DS, ["dentist", "landscaping", "zzzzqqq", "healthcare"])
    assert "Dental Practice [dental-practice]: $5M-$25M EV: median 7.0x (middle 50%: 6.5x-8.3x), n=10" in out
    assert "9.0x" not in out  # n=9 withheld here too
    assert "Landscaping [landscaping]: INSUFFICIENT DATA" in out
    assert "'zzzzqqq': no industry matched" in out
    assert "industry group" in out
    assert "SEC EDGAR filings" in out
    assert out.rstrip().endswith("https://exitvalue.ai/valuate?src=mcp-oss")


def test_compare_metric_bracket_and_limits():
    out = m.compare_industries(DS, ["msp", "dental-practice"], "5m_25m_ev", "ev_revenue")
    assert "0.89x" in out and "IT services" in out
    assert "Dental Practice [dental-practice]: INSUFFICIENT DATA" in out and "metric=ev_ebitda" in out
    assert "between 2 and 6" in m.compare_industries(DS, ["hvac"])
    assert "between 2 and 6" in m.compare_industries(DS, list("abcdefg"))
    assert m.compare_industries(DS, ["hvac"]).rstrip().endswith("src=mcp-oss")


def test_trend_respects_min_n_and_reports_gaps():
    out = m.get_multiples_trend(TREND, "software")
    assert "- 2019 (median deal value $64M): EV/EBITDA median 19.3x (middle 50%: 13.8x-38.1x), n=19" in out
    assert "30.5x" not in out  # n=9 withheld, not filled
    assert "2020" in out and "not estimated" in out  # gap year listed, nothing invented for it
    assert "- 2020" not in out
    assert "multiples-by-year.json" in out
    assert out.rstrip().endswith("https://exitvalue.ai/valuate?src=mcp-oss&industry=saas")


def test_trend_metric_parent_and_no_data():
    out = m.get_multiples_trend(TREND, "msp", "ev_revenue")
    assert "IT services" in out and "1.92x" in out and "EV/EBITDA" not in out
    out = m.get_multiples_trend(TREND, "landscaping")
    assert "no year-by-year" in out and not re.search(r"\d\.\d+x", out)
    out = m.get_multiples_trend(TREND, "technology")
    assert "[saas]" in out and "industry group" in out
