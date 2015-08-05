import time
import numbers

from wwb_scanner.core import JSONMixin

class Sample(JSONMixin):
    __slots__ = ('spectrum', '_frequency', '_magnitude', '_serialization_attrs')
    _serialization_attrs = ['frequency', 'magnitude']
    def __init__(self, **kwargs):
        self.spectrum = kwargs.get('spectrum')
        self.frequency = kwargs.get('frequency')
        self.magnitude = kwargs.get('magnitude')
    @property
    def frequency(self):
        return getattr(self, '_frequency', None)
    @frequency.setter
    def frequency(self, value):
        if not isinstance(value, numbers.Number):
            return
        if self.frequency == value:
            return
        if not isinstance(value, float):
            value = float(value)
        self._frequency = value
    @property
    def magnitude(self):
        return getattr(self, '_magnitude', None)
    @magnitude.setter
    def magnitude(self, value):
        if not isinstance(value, numbers.Number):
            return
        old = self.magnitude
        if old == value:
            return
        if not isinstance(value, float):
            value = float(value)
        self._magnitude = value
        self.spectrum.on_sample_change(sample=self, magnitude=value, old=old)
    @property
    def formatted_frequency(self):
        return '%07.4f' % (self.frequency)
    @property
    def formatted_magnitude(self):
        return '%03.1f' % (self.magnitude)
    def __repr__(self):
        return str(self)
    def __str__(self):
        return '%s (%s dB)' % (self.formatted_frequency, self.magnitude)
        
class TimeBasedSample(Sample):
    __slots__ = ('timestamp')
    def __init__(self, **kwargs):
        ts = kwargs.get('timestamp')
        if ts is None:
            ts = time.time()
        self.timestamp = ts
        super(TimeBasedSample, self).__init__(**kwargs)
        
