"""Spectral efficiency, CQI/MCS tables (data, not if-chains), TBS TS 38.214 §5.1.3.2."""

from __future__ import annotations

import math
from typing import Any

# Each row: cqi, modulation, code_rate_x1024, efficiency
# TS 38.214 Table 5.2.2.1-2 (64QAM), 5.2.2.1-3 (256QAM), 5.2.2.1-4 (1024QAM Rel-17).
CQI_TABLES: dict[int, tuple[tuple[int, str, int, float], ...]] = {
    1: (
        (1, "QPSK", 78, 0.1523),
        (2, "QPSK", 120, 0.2344),
        (3, "QPSK", 193, 0.3770),
        (4, "QPSK", 308, 0.6016),
        (5, "QPSK", 449, 0.8770),
        (6, "QPSK", 602, 1.1758),
        (7, "16QAM", 378, 1.4766),
        (8, "16QAM", 490, 1.9141),
        (9, "16QAM", 616, 2.4063),
        (10, "64QAM", 466, 2.7305),
        (11, "64QAM", 567, 3.3223),
        (12, "64QAM", 666, 3.9023),
        (13, "64QAM", 772, 4.5234),
        (14, "64QAM", 873, 5.1152),
        (15, "64QAM", 948, 5.5547),
    ),
    2: (
        (1, "QPSK", 78, 0.1523),
        (2, "QPSK", 193, 0.3770),
        (3, "QPSK", 449, 0.8770),
        (4, "16QAM", 378, 1.4766),
        (5, "16QAM", 490, 1.9141),
        (6, "16QAM", 616, 2.4063),
        (7, "64QAM", 466, 2.7305),
        (8, "64QAM", 567, 3.3223),
        (9, "64QAM", 666, 3.9023),
        (10, "64QAM", 772, 4.5234),
        (11, "64QAM", 873, 5.1152),
        (12, "256QAM", 711, 5.5547),
        (13, "256QAM", 797, 6.2266),
        (14, "256QAM", 885, 6.9141),
        (15, "256QAM", 948, 7.4063),
    ),
    3: (
        (1, "QPSK", 78, 0.1523),
        (2, "QPSK", 193, 0.3770),
        (3, "QPSK", 449, 0.8770),
        (4, "16QAM", 378, 1.4766),
        (5, "16QAM", 490, 1.9141),
        (6, "16QAM", 616, 2.4063),
        (7, "64QAM", 466, 2.7305),
        (8, "64QAM", 567, 3.3223),
        (9, "64QAM", 666, 3.9023),
        (10, "64QAM", 772, 4.5234),
        (11, "64QAM", 873, 5.1152),
        (12, "256QAM", 711, 5.5547),
        (13, "256QAM", 797, 6.2266),
        (14, "256QAM", 885, 6.9141),
        (15, "1024QAM", 805, 7.8613),
    ),
}

# TS 38.214 Table 5.1.3.1-1 (64QAM). mcs, modulation, code_rate_x1024, efficiency
MCS_TABLE_1: tuple[tuple[int, str, int, float], ...] = (
    (0, "QPSK", 120, 0.2344),
    (1, "QPSK", 157, 0.3066),
    (2, "QPSK", 193, 0.3770),
    (3, "QPSK", 251, 0.4902),
    (4, "QPSK", 308, 0.6016),
    (5, "QPSK", 379, 0.7402),
    (6, "QPSK", 449, 0.8770),
    (7, "QPSK", 526, 1.0273),
    (8, "QPSK", 602, 1.1758),
    (9, "QPSK", 679, 1.3262),
    (10, "16QAM", 340, 1.3281),
    (11, "16QAM", 378, 1.4766),
    (12, "16QAM", 434, 1.6953),
    (13, "16QAM", 490, 1.9141),
    (14, "16QAM", 553, 2.1602),
    (15, "16QAM", 616, 2.4063),
    (16, "16QAM", 658, 2.5703),
    (17, "64QAM", 438, 2.5664),
    (18, "64QAM", 466, 2.7305),
    (19, "64QAM", 517, 3.0293),
    (20, "64QAM", 567, 3.3223),
    (21, "64QAM", 616, 3.6094),
    (22, "64QAM", 666, 3.9023),
    (23, "64QAM", 719, 4.2129),
    (24, "64QAM", 772, 4.5234),
    (25, "64QAM", 822, 4.8164),
    (26, "64QAM", 873, 5.1152),
    (27, "64QAM", 910, 5.3320),
    (28, "64QAM", 948, 5.5547),
)

MODULATION_QM = {"QPSK": 2, "16QAM": 4, "64QAM": 6, "256QAM": 8, "1024QAM": 10}

# TS 38.214 Table 5.1.3.2-1
TBS_TABLE_51321: tuple[int, ...] = (
    24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152,
    160, 168, 176, 184, 192, 208, 224, 240, 256, 272, 288, 304, 320, 336, 352,
    368, 384, 408, 432, 456, 480, 504, 528, 552, 576, 608, 640, 672, 704, 736,
    768, 808, 848, 888, 928, 984, 1032, 1064, 1128, 1160, 1192, 1224, 1256,
    1288, 1320, 1352, 1416, 1480, 1544, 1608, 1672, 1736, 1800, 1864, 1928,
    2024, 2088, 2152, 2216, 2280, 2408, 2472, 2536, 2600, 2664, 2728, 2792,
    2856, 2976, 3104, 3240, 3368, 3496, 3624, 3752, 3824,
)


def shannon_se(sinr_db: float) -> float:
    return math.log2(1.0 + 10.0 ** (sinr_db / 10.0))


def lookup_cqi(table_id: int, cqi: int) -> dict[str, Any]:
    rows = CQI_TABLES.get(table_id)
    if rows is None:
        raise KeyError(f"unknown CQI table {table_id}")
    for row in rows:
        if row[0] == cqi:
            return {
                "cqi": row[0],
                "modulation": row[1],
                "code_rate_x1024": row[2],
                "efficiency": row[3],
                "qm": MODULATION_QM[row[1]],
            }
    raise KeyError(f"CQI {cqi} not in table {table_id}")


def lookup_mcs(mcs: int) -> dict[str, Any]:
    for row in MCS_TABLE_1:
        if row[0] == mcs:
            return {
                "mcs": row[0],
                "modulation": row[1],
                "code_rate_x1024": row[2],
                "efficiency": row[3],
                "qm": MODULATION_QM[row[1]],
            }
    raise KeyError(f"MCS {mcs} not in Table 5.1.3.1-1")


def cqi_from_sinr_approx(sinr_db: float, table_id: int = 1) -> int:
    """Highest CQI whose tabulated efficiency <= Shannon SE(SINR).

    APPROXIMATION: 3GPP does not specify a unique SINR→CQI mapping (UE impl).
    This piecewise-threshold on Shannon efficiency is documented in
    docs/metrics-formulas.md and must not be presented as a radio measurement.
    """
    se = shannon_se(sinr_db)
    chosen = 0
    for row in CQI_TABLES[table_id]:
        if row[3] <= se:
            chosen = row[0]
        else:
            break
    return chosen


def tbs_from_n_info_prime_small(n_info_prime: int) -> int:
    """Closest TBS in Table 5.1.3.2-1 that is not less than N_info'."""
    for tbs in TBS_TABLE_51321:
        if tbs >= n_info_prime:
            return tbs
    return TBS_TABLE_51321[-1]


def transport_block_size(
    n_re: int,
    code_rate: float,
    qm: int,
    layers: int = 1,
) -> int:
    """TS 38.214 §5.1.3.2 exact procedure."""
    if n_re <= 0 or qm <= 0 or layers <= 0:
        raise ValueError("N_RE, Qm, layers must be > 0")
    if not (0.0 < code_rate <= 1.0):
        raise ValueError("code rate must be in (0, 1]")
    n_info = n_re * code_rate * qm * layers
    if n_info <= 3824:
        n = max(3, math.floor(math.log2(n_info)) - 6)
        n_info_p = max(24, (2**n) * math.floor(n_info / (2**n)))
        return tbs_from_n_info_prime_small(int(n_info_p))
    n = math.floor(math.log2(n_info - 24)) - 5
    n_info_p = max(3840, (2**n) * round((n_info - 24) / (2**n)))
    if code_rate <= 0.25:
        c = math.ceil((n_info_p + 24) / 3816)
        return int(8 * c * math.ceil((n_info_p + 24) / (8 * c)) - 24)
    if n_info_p > 8424:
        c = math.ceil((n_info_p + 24) / 8424)
        return int(8 * c * math.ceil((n_info_p + 24) / (8 * c)) - 24)
    return int(8 * math.ceil((n_info_p + 24) / 8) - 24)


def mcs_for_cqi(cqi_row: dict[str, Any]) -> int:
    """Pick MCS from table 1 with efficiency closest not exceeding CQI efficiency."""
    target = cqi_row["efficiency"]
    chosen = 0
    for row in MCS_TABLE_1:
        if row[3] <= target:
            chosen = row[0]
        else:
            break
    return chosen
