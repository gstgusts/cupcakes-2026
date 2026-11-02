"""Newsvendor calculation: how many cupcakes to bake for one day.

Daily demand is assumed to be normally distributed with mean d and standard deviation σ.
The best quantity Q is the one where P(demand <= Q) equals the critical ratio
CR = Cu / (Cu + Co), with underage cost Cu = p - c and overage cost Co = c - s.
"""
from statistics import NormalDist


def critical_ratio(cost, price, salvage):
    """CR = Cu / (Cu + Co). Requires salvage < cost < price, so that 0 < CR < 1."""
    underage = price - cost
    overage = cost - salvage
    return float(underage / (underage + overage))


def z_score(ratio):
    """How many standard deviations the quantity is above (+) or below (-) the average demand."""
    return NormalDist().inv_cdf(ratio)


def recommended_quantity(mean, std_dev, ratio):
    """Whole number of cupcakes Q = d + z·σ, never negative."""
    if std_dev == 0:
        # No variability: demand is always the average (NormalDist does not accept σ = 0)
        return max(0, round(mean))
    return max(0, round(mean + z_score(ratio) * std_dev))
