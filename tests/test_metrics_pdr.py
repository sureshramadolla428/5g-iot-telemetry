from __future__ import annotations

import pytest

from metrics.goodput import SequenceStats


def test_sequence_gaps_duplicates_reorders_separate():
    s = SequenceStats()
    s.observe(1)
    s.observe(2)
    s.observe(4)
    s.observe(4)
    s.observe(3)
    assert s.gaps == 1
    assert s.duplicates == 1
    assert s.reorders == 1
    assert s.pdr() == pytest.approx(1.0)
    assert s.plr() == pytest.approx(0.0)
