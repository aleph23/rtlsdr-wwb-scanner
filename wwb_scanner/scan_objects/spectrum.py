import threading
import json
from wwb_scanner.scan_objects import Sample

class Spectrum(object):
    def __init__(self, **kwargs):
        self.step_size = kwargs.get('step_size')
        self.data_updated = threading.Event()
        self.data_update_lock = threading.Lock()
        self.samples = {}
        samples = kwargs.get('samples', {})
        if isinstance(samples, dict):
            for key, data in samples.items():
                if isinstance(data, dict):
                    self.add_sample(**data)
                else:
                    self.add_sample(frequency=key, magnitude=data)
        else:
            for sample_kwargs in samples:
                self.add_sample(**sample_kwargs)
    @classmethod
    def from_json(cls, data):
        if isinstance(data, basestring):
            data = json.loads(data)
        return cls(**data)
    def to_json(self, **kwargs):
        d = self._serialize()
        return json.dumps(d, **kwargs)
    def add_sample(self, **kwargs):
        if kwargs.get('frequency') in self.samples:
            sample = self.samples[kwargs['frequency']]
            sample.magnitude = kwargs.get('magnitude')
            return sample
        kwargs.setdefault('spectrum', self)
        sample = Sample(**kwargs)
        self.samples[sample.frequency] = sample
        self.set_data_updated()
        return sample
    def iter_frequencies(self):
        for key in sorted(self.samples.keys()):
            yield key
    def iter_samples(self):
        for key in self.iter_frequencies():
            yield self.samples[key]
    def on_sample_change(self, **kwargs):
        sample = kwargs.get('sample')
        if sample.frequency not in self.samples:
            return
        self.set_data_updated()
    def set_data_updated(self):
        with self.data_update_lock:
            self.data_updated.set()
    def _serialize(self):
        d = {'step_size':self.step_size}
        samples = self.samples
        d['samples'] = {k: samples[k]._serialize() for k in samples.keys()}
        return d

def compare_spectra(spec1, spec2):
    diff_spec = Spectrum()
    for sample in spec1.iter_samples():
        other_sample = spec2.samples.get(sample.frequency)
        if other_sample is None:
            continue
        magnitude = sample.magnitude - other_sample.magnitude
        diff_spec.add_sample(frequency=sample.frequency, magnitude=magnitude)
    return diff_spec
