import json
import numpy as np
from scipy.signal import welch, resample

def next_2_to_pow(val):
    val -= 1
    val |= val >> 1
    val |= val >> 2
    val |= val >> 4
    val |= val >> 8
    val |= val >> 16
    return val + 1

def calc_num_samples(sample_rate):
    return next_2_to_pow(int(sample_rate * .125))

class SampleSet(object):
    __slots__ = ('scanner', 'center_frequency', 'samples',
                 'raw', 'frequencies', 'powers', 'collection')
    def __init__(self, **kwargs):
        for key in self.__slots__:
            setattr(self, key, kwargs.get(key))
        if self.scanner is None and self.collection is not None:
            self.scanner = self.collection.scanner
        if 'from_json' in kwargs or self.raw is None:
            self.read_samples()
    @classmethod
    def from_json(cls, scanner, data):
        if isinstance(data, basestring):
            data = json.loads(data)
        obj = cls(scanner, data['center_frequency'], from_json=True)
        np_keys = ['samples', 'frequencies', 'raw', 'powers']
        for key, val in data.items():
            if key in np_keys:
                val = np.array(val)
            setattr(obj, key, val)
        return obj
    def read_samples_crapily(self):
        scanner = self.scanner
        freq = self.center_frequency
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        samples = self.samples = sdr.read_samples(scanner.samples_per_scan)
        mag = np.fft.fft(samples, n=int(scanner.sample_segment_length))
        mag_size = mag.size
        is_even = mag_size % 2 == 0
        f = np.fft.fftfreq(mag.size, d=1/scanner.sample_rate)
        f = np.fft.fftshift(f)
        f += freq
        f /= 1e6
        if is_even:
            mag = mag[1:]
            f = f[1:]
        self.raw = mag
        self.frequencies = f
        self.powers = 20. * np.log10(mag)
    def read_samples(self):
        scanner = self.scanner
        freq = self.center_frequency
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        samples = self.samples = sdr.read_samples(scanner.samples_per_scan)
        f, powers = welch(samples, fs=scanner.sample_rate, nfft=scanner.fft_size)#, nperseg=scanner.sample_segment_length)#, scaling='spectrum')
        #powers, f = resample(powers, 128, t=f)
        f = np.fft.fftshift(f)
        f += freq
        f /= 1e6
        #f = f[4:-4]
        #powers = powers[4:-4]
        self.frequencies = f
        self.raw = powers.copy()
        self.powers = 10. * np.log10(powers)

    def _serialize(self):
        d = {}
        for key in self.__slots__:
            if key == 'scanner':
                continue
            val = getattr(self, key)
            if isinstance(val, np.ndarray):
                val = val.tolist()
            d[key] = val
        return d

class SampleCollection(object):
    def __init__(self, **kwargs):
        self.scanner = kwargs.get('scanner')
        self.sample_sets = {}
    def add_sample_set(self, sample_set):
        self.sample_sets[sample_set.center_frequency] = sample_set
    def scan_freq(self, freq):
        sample_set = SampleSet(collection=self, center_frequency=freq)
        self.add_sample_set(sample_set)
        return sample_set
