# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

from daqview.models.units import quantity_for_unit


def test_quantities():
    assert quantity_for_unit("bar(g)") == "Pressure"
    assert quantity_for_unit("km/yr") == "Velocity"
    assert quantity_for_unit("Nm") == "Moment"
    assert quantity_for_unit("kW") == "Power"
    assert quantity_for_unit("????") == "Unknown"
