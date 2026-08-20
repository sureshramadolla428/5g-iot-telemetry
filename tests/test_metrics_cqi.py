from __future__ import annotations

from metrics.phy import lookup_cqi, lookup_mcs


def test_cqi_table_lookup_not_if_chain():
    row = lookup_cqi(1, 1)
    assert row["modulation"] == "QPSK"
    assert row["code_rate_x1024"] == 78
    assert row["efficiency"] == 0.1523
    row15 = lookup_cqi(1, 15)
    assert row15["modulation"] == "64QAM"
    assert row15["code_rate_x1024"] == 948
    t2 = lookup_cqi(2, 15)
    assert t2["modulation"] == "256QAM"
    t3 = lookup_cqi(3, 15)
    assert t3["modulation"] == "1024QAM"


def test_mcs_table_1():
    m0 = lookup_mcs(0)
    assert m0["modulation"] == "QPSK"
    m28 = lookup_mcs(28)
    assert m28["code_rate_x1024"] == 948
