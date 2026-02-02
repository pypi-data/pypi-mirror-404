import logging
import numpy as np
from scipy.stats import linregress
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)


class CurveFit:
    def __init__(self, name, params):
        self.name = name
        self._params = params

    def fit(self, t, v):
        raise NotImplementedError

    def evaluate(self, t):
        raise NotImplementedError

    def params(self):
        return {k: getattr(self, k) for k in self._params}

    def set_params(self, params):
        for k in self._params:
            if k in params:
                setattr(self, k, params[k])


class LinearCurveFit(CurveFit):
    """
    y = Ax + B
    """
    def __init__(self):
        super().__init__("linear", "ab")
        self.a = 0.0
        self.b = 0.0

    def fit(self, t, v):
        r = linregress(t, v)
        self.a = r.slope
        self.b = r.intercept

    def evaluate(self, t):
        return t*self.a + self.b


class SinusoidalCurveFit(CurveFit):
    """
    y = A sin(2πBx + C) + D
    """
    def __init__(self):
        super().__init__("sinusoidal", "abcd")
        self.a = 0.0
        self.b = 0.0
        self.c = 0.0
        self.d = 0.0

    def fit(self, t, v):
        if len(t) < 2:
            logger.warning("Cannot autofit with fewer than 2 points of data")
            return

        # Make initial guess at parameters
        t = np.array(t)
        v = np.array(v)
        a = np.std(v) * np.sqrt(2)
        freqs = np.fft.rfftfreq(t.size, t[1] - t[0])
        fft = np.abs(np.fft.rfft(v))
        b = freqs[np.argmax(fft[1:]) + 1]
        c = 0.0
        d = np.mean(v)
        p0 = a, b, c, d

        # Run optimiser
        def f(x, a, b, c, d):
            return a * np.sin(2.0 * np.pi * b * x + c) + d
        bounds = (
            (0, 0, 0, -np.inf),
            (np.inf, np.inf, 2*np.pi, np.inf),
        )
        try:
            popt, _ = curve_fit(f, t, v, p0, bounds=bounds)
        except RuntimeError as e:
            logger.warning("Error fitting curve: %s", e)
        else:
            self.a, self.b, self.c, self.d = popt

    def evaluate(self, t):
        w = 2.0 * np.pi * self.b
        return self.a * np.sin(w * t + self.c) + self.d


class ExponentialCurveFit(CurveFit):
    """
    y = A exp(Bx - C) + D
    """
    def __init__(self):
        super().__init__("exponential", "abc")
        self.a = 0.0
        self.b = 0.0
        self.c = 0.0
        self.d = 0.0

    def fit(self, t, v):
        if len(v) < 2:
            logger.warning("Cannot autofit with fewer than 2 points of data")
            return
        self.c = -t[0]
        t = np.array(t)
        v = np.array(v)
        p0 = v[0], 0.0, 0.0

        def f(x, a, b, d):
            return a * np.exp(b * x) + d
        try:
            popt, _ = curve_fit(f, t + self.c, v, p0)
        except RuntimeError as e:
            logger.warning("Error fitting curve: %s", e)
        else:
            self.a, self.b, self.d = popt

    def evaluate(self, t):
        return self.a * np.exp(self.b * (t + self.c)) + self.d
