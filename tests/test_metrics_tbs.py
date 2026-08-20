from __future__ import annotations

from metrics.phy import TBS_TABLE_51321, tbs_from_n_info_prime_small, transport_block_size


def test_tbs_table_known_3gpp_values():
    assert tbs_from_n_info_prime_small(24) == 24
    assert tbs_from_n_info_prime_small(50) == 56
    assert tbs_from_n_info_prime_small(100) == 104
    assert tbs_from_n_info_prime_small(3824) == 3824
    assert 3824 in TBS_TABLE_51321
    assert TBS_TABLE_51321 == tuple(sorted(TBS_TABLE_51321))


def test_tbs_small_info_quantization():
    # n_info = 100 → n=3, N_info' = 96 → TBS 96 (Table 5.1.3.2-1)
    assert transport_block_size(n_re=100, code_rate=0.5, qm=2, layers=1) == 96


def test_tbs_large_is_8_aligned():
    tbs = transport_block_size(n_re=20000, code_rate=0.5, qm=6, layers=2)
    assert tbs > 3824
    assert (tbs + 24) % 8 == 0
