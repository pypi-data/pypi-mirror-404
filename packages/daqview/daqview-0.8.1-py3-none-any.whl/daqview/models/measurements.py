import logging
import numpy as np

logger = logging.getLogger(__name__)

# Each Measurement class must have these class attributes:
#
# KEY: short label used to refer to this measurement
# NAME: human-readable name used in menus
# LABEL: human-readable short label for display in measurements box
# TIME: if present and True, this measurement may be used on the virtual
#       time channel, in which case `values` passed to `measure()` will
#       be the same as the `times` argument.
#
# Furthermore, each class must implement a `measure()` class method,
# which takes (cls, channel, times, values) arguments and returns a
# MeasurementResult object with a string-formatted value and optional
# vertical or horizontal lines to draw when the measurement is hovered.


class MeasurementResult:
    """
    Returned from a Measurement's `measure` method.

    * `value`: formatted string to display for this measurement
    * `raw_value`: Unformatted raw value for this measurement
    * `vlines`: t-positions of any vertical lines to draw when highlighted
    * `hlines`: v-positions of any horizonal lines to draw when highlighted
    * `targets`: (t, v)-positions of any targets to draw when highlighted
    """
    def __init__(
        self,
        value="---",
        raw_value=np.nan,
        vlines=None,
        hlines=None,
        targets=None
    ):
        self.value = value
        self.raw_value = raw_value
        if vlines is not None:
            self.vlines = vlines
        else:
            self.vlines = []
        if hlines is not None:
            self.hlines = hlines
        else:
            self.hlines = []
        if targets is not None:
            self.targets = targets
        else:
            self.targets = []


class LeftMeasurement:
    KEY = "left"
    NAME = "Left"
    LABEL = "◀"
    TIME = True

    @classmethod
    def measure(cls, channel, times, values):
        if len(values) == 0:
            return MeasurementResult()
        v = values[0]
        targets = [(times[0], v)] if times is not values else []
        f = channel.formatted_value(value=v)
        return MeasurementResult(f, v, targets=targets)


class RightMeasurement:
    KEY = "right"
    NAME = "Right"
    LABEL = "▶"
    TIME = True

    @classmethod
    def measure(cls, channel, times, values):
        if len(values) == 0:
            return MeasurementResult()
        v = values[-1]
        targets = [(times[-1], v)] if times is not values else []
        f = channel.formatted_value(value=v)
        return MeasurementResult(f, v, targets=targets)


class DeltaMeasurement:
    KEY = "delta"
    NAME = "Delta"
    LABEL = "Δ"
    TIME = True

    @classmethod
    def measure(cls, channel, times, values):
        if len(values) < 2:
            return MeasurementResult()
        v = values[-1] - values[0]
        targets = [(times[0], values[0]), (times[-1], values[-1])]
        hlines = [values[0], values[-1]]
        if times is values:
            targets = hlines = []
        f = channel.formatted_value(value=v)
        return MeasurementResult(f, v, hlines=hlines, targets=targets)


class GradientMeasurement:
    KEY = "gradient"
    NAME = "Gradient"
    LABEL = "Δ/Δt"
    TIME = True

    @classmethod
    def measure(cls, channel, times, values):
        if len(values) < 2:
            return MeasurementResult()
        d = values[-1] - values[0]
        dt = times[-1] - times[0]
        d_dt = d/dt
        if times is values:
            # When t==v we're processing the time row, so show 1/dt instead.
            f = f"{1/dt:.02g}"
            v = 1/dt
        else:
            f = f"{d_dt:.02g}"
            v = d_dt
        return MeasurementResult(f, v)


class MeanMeasurement:
    KEY = "mean"
    NAME = "Mean"
    LABEL = "µ"

    @classmethod
    def measure(cls, channel, times, values):
        if len(values) == 0:
            return MeasurementResult()
        v = np.nanmean(values)
        f = channel.formatted_value(value=v)
        return MeasurementResult(f, v, hlines=[v])


class MinMeasurement:
    KEY = "min"
    NAME = "Min"
    LABEL = "Min"

    @classmethod
    def measure(cls, channel, times, values):
        try:
            amin = np.nanargmin(values)
            v = values[amin]
            t = times[amin]
            hlines = [v]
            targets = [(t, v)]
        except ValueError:
            return MeasurementResult()
        else:
            f = channel.formatted_value(value=v)
            return MeasurementResult(f, v, hlines=hlines, targets=targets)


class MaxMeasurement:
    KEY = "max"
    NAME = "Max"
    LABEL = "Max"

    @classmethod
    def measure(cls, channel, times, values):
        try:
            amax = np.nanargmax(values)
            v = values[amax]
            t = times[amax]
            hlines = [v]
            targets = [(t, v)]
        except ValueError:
            return MeasurementResult()
        else:
            f = channel.formatted_value(value=v)
            return MeasurementResult(f, v, hlines=hlines, targets=targets)


class PkPkMeasurement:
    KEY = "pkpk"
    NAME = "Peak-to-Peak"
    LABEL = "p-p"

    @classmethod
    def measure(cls, channel, times, values):
        try:
            amin = np.nanargmin(values)
            amax = np.nanargmax(values)
            vmin, vmax = values[amin], values[amax]
            tmin, tmax = times[amin], times[amax]
            ptp = vmax - vmin
            hlines = [vmin, vmax]
            targets = [(tmin, vmin), (tmax, vmax)]
        except ValueError:
            return MeasurementResult()
        else:
            f = channel.formatted_value(value=ptp)
            return MeasurementResult(f, ptp, hlines=hlines, targets=targets)


class IntegrateMeasurement:
    KEY = "integ"
    NAME = "Integrate"
    LABEL = "Σ"

    @classmethod
    def measure(cls, channel, times, values):
        if len(values) == 0:
            return MeasurementResult()
        v = np.trapezoid(values, times)
        f = channel.formatted_value(value=v)
        return MeasurementResult(f, v)


class StdMeasurement:
    KEY = "std"
    NAME = "Standard Deviation"
    LABEL = "σ"

    @classmethod
    def measure(cls, channel, times, values):
        if len(values) == 0:
            return MeasurementResult()
        v = np.std(values)
        u = np.mean(values)
        if np.isfinite(v) and np.isfinite(u):
            hlines = [u-v, u, u+v]
        else:
            hlines = []
        f = channel.formatted_value(value=v)
        return MeasurementResult(f, v, hlines=hlines)


class VarMeasurement:
    KEY = "var"
    NAME = "Variance"
    LABEL = "σ²"

    @classmethod
    def measure(cls, channel, times, values):
        if len(values) == 0:
            return MeasurementResult()
        v = np.var(values)
        f = channel.formatted_value(value=v)
        return MeasurementResult(f, v)


class RmsMeasurement:
    KEY = "rms"
    NAME = "RMS"
    LABEL = "RMS"

    @classmethod
    def measure(cls, channel, times, values):
        if len(values) == 0:
            return MeasurementResult()
        v = np.sqrt(np.mean(np.square(values)))
        f = channel.formatted_value(value=v)
        return MeasurementResult(f, v)


class PeriodMeasurement:
    KEY = "period"
    NAME = "Period"
    LABEL = "Period"

    @classmethod
    def measure(cls, channel, times, values):
        result = cls._measure(channel, times, values)
        if result is None:
            return MeasurementResult()
        period, vlines, targets = result
        return MeasurementResult(
            f"{period:.04g}",
            period,
            vlines=vlines,
            targets=targets
        )

    @classmethod
    def _measure(cls, channel, times, values):
        """
        Perform detection of edges and thus period.

        Split into separate _measure class to allow sharing with
        FrequencyMeasurement.
        """
        if len(values) < 2:
            return None

        # Find thresholds for rising and falling edges by using the std.dev.
        # to give a small hysteresis around the mean.
        u = np.mean(values)
        s = np.std(values)
        lower = u - 0.1 * s
        higher = u + 0.1 * s

        # Detect the indicies where the samples just cross the threshold.
        v0 = values[:-1]
        v1 = values[1:]
        rising = list(np.flatnonzero((v0 < lower) & (v1 > lower)) + 1)
        falling = list(np.flatnonzero((v0 > higher) & (v1 < higher)) + 1)

        # Quit early if not enough edges found
        if min(len(falling), len(rising)) == 0:
            return None
        if max(len(falling), len(rising)) < 2:
            return None

        # Select first and second edge
        if rising[0] < falling[0]:
            first, second = rising, falling
            threshold = lower
        else:
            first, second = falling, rising
            threshold = higher

        # Prune consecutive edges in the same direction
        i = 0
        while i < min(len(first), len(second)) - 1:
            while i < len(first) - 1 and first[i+1] < second[i]:
                del first[i+1]
            if i > len(first) - 2:
                break
            while i < len(second) - 2 and second[i+1] < first[i+1]:
                del second[i+1]
            i += 1
        if len(second) > len(first):
            del second[-1]

        # Estimate periods from all pairs of first edges
        periods = []
        for a, b in zip(first[:-1], first[1:]):
            periods.append(times[b] - times[a])
        period = np.mean(periods)

        # Put a target on each detected edge point.
        targets = [(times[i], threshold) for i in first]

        # Put a line at each average period from the first period.
        vlines = [times[first[0]]]
        for i in first[1:]:
            vlines.append(vlines[-1] + period)

        return period, vlines, targets


class FrequencyMeasurement(PeriodMeasurement):
    KEY = "freq"
    NAME = "Frequency"
    LABEL = "Freq"

    @classmethod
    def measure(cls, channel, times, values):
        result = cls._measure(channel, times, values)
        if result is None:
            return MeasurementResult()
        period, vlines, targets = result
        freq = 1.0 / period
        return MeasurementResult(f"{freq:.04g}", freq, vlines=vlines, targets=targets)


MEASUREMENTS = [
    LeftMeasurement,
    RightMeasurement,
    DeltaMeasurement,
    GradientMeasurement,
    MeanMeasurement,
    MinMeasurement,
    MaxMeasurement,
    PkPkMeasurement,
    IntegrateMeasurement,
    StdMeasurement,
    VarMeasurement,
    RmsMeasurement,
    PeriodMeasurement,
    FrequencyMeasurement,
]
