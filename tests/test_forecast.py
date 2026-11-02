from decimal import Decimal

import pytest

from app.services.forecast import critical_ratio, recommended_quantity, z_score


@pytest.mark.parametrize("d, sd, c, p, s, ratio, quantity", [
    (150, 30, 10, 15, 2, 0.3846, 141),  # Case 3 from the lecture: CR < 0.5, bake fewer than average
    (150, 30, 20, 30, 5, 0.4000, 142),  # slide 9 numbers
    (150, 30, 10, 25, 2, 0.6522, 162),  # high margin: CR > 0.5, bake more than average
    (150, 0, 10, 15, 2, 0.3846, 150),   # no variability: bake the average
    (150, 30, 10, 18, 2, 0.5000, 150),  # Cu = Co: bake the average
])
def test_lecture_examples(d, sd, c, p, s, ratio, quantity):
    cr = critical_ratio(c, p, s)
    assert cr == pytest.approx(ratio, abs=1e-4)
    assert recommended_quantity(d, sd, cr) == quantity


def test_critical_ratio_accepts_decimals():
    # The database stores money as Decimal
    assert critical_ratio(Decimal("10.00"), Decimal("15.00"), Decimal("2.00")) == pytest.approx(5 / 13)


def test_z_score():
    assert z_score(0.5) == pytest.approx(0)
    assert z_score(0.975) == pytest.approx(1.96, abs=1e-3)
    assert z_score(5 / 13) == pytest.approx(-0.2934, abs=1e-4)


def test_quantity_is_never_negative():
    # Very low CR with a large deviation would give a negative quantity
    assert recommended_quantity(5, 100, 0.01) == 0
