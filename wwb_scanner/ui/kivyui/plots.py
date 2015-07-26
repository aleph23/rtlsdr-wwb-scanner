import numpy as np

#from kivy.garden.graph import Graph, MeshLinePlot
from kivy.garden.tickline import Tickline, Tick, LabellessTick, DataListTick
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.properties import (
    ListProperty, 
    DictProperty, 
    NumericProperty, 
    AliasProperty, 
    BooleanProperty, 
    StringProperty, 
    ObjectProperty, 
)

from wwb_scanner.core import JSONMixin
from wwb_scanner.scan_objects import Spectrum

class TickContainer(FloatLayout):
    def do_layout(self, *args, **kwargs):
        super(TickContainer, self).do_layout(*args, **kwargs)
        print 'container: ', self.pos, self.size
        for c in self.children:
            if isinstance(c, Tickline):
                c.redraw()
            print c, c.pos, c.size
    
class SpectrumGraph(RelativeLayout, JSONMixin):
    scan_controls = ObjectProperty(None)
    plot_params = DictProperty()
    x_min = NumericProperty(0.)
    x_max = NumericProperty(1.)
    auto_scale_x = BooleanProperty(True)
    auto_scale_y = BooleanProperty(True)
    selected = ObjectProperty(None)
    tick_container = ObjectProperty(None)
    x_tick_line = ObjectProperty(None)
    y_tick_line = ObjectProperty(None)
    x_tick_data = ListProperty()
    y_tick_data = ListProperty()
    def get_x_size(self):
        return self.x_max - self.x_min
    def set_x_size(self, value):
        pass
    x_size = AliasProperty(get_x_size, set_x_size, bind=('x_min', 'x_max'))
    y_min = NumericProperty(-100.)
    y_max = NumericProperty(0.)
    def get_y_size(self):
        return self.y_max - self.y_min
    def set_y_size(self, value):
        pass
    y_size = AliasProperty(get_y_size, set_y_size, bind=('y_min', 'y_max'))
    def __init__(self, **kwargs):
        super(SpectrumGraph, self).__init__(**kwargs)
    def on_tick_container(self, *args):
        if self.tick_container is None:
            return
        self.build_ticklines()
    def on_x_min(self, instance, value):
        self.plot_params['x_min'] = value
        self.build_tick_data()
    def on_x_max(self, instance, value):
        self.plot_params['x_max'] = value
        self.build_tick_data()
    def on_y_min(self, instance, value):
        self.plot_params['y_min'] = value
        self.build_tick_data()
    def on_y_max(self, instance, value):
        self.plot_params['y_max'] = value
        self.build_tick_data()
    def on_scan_controls(self, *args):
        if self.scan_controls is None:
            return
        scan_range = self.scan_controls.scan_range
        self.x_min = scan_range[0]
        self.x_max = scan_range[1]
    def add_plot(self, **kwargs):
        plot = kwargs.get('plot')
        if plot is None:
            if self.selected is None:
                kwargs['selected'] = True
            plot = SpectrumPlot(**kwargs)
        plot.bind(selected=self.on_plot_selected)
        self.add_widget(plot)
        self.calc_plot_scale()
        if plot.selected:
            self.selected = plot
        return plot
    def on_plot_selected(self, instance, value):
        if not value:
            return
        self.selected = instance
    def calc_plot_scale(self):
        auto_x = self.auto_scale_x
        auto_y = self.auto_scale_y
        if not auto_x and not auto_y:
            return
        d = {}
        for w in self.children:
            if not isinstance(w, SpectrumPlot):
                continue
            if not w.enabled:
                continue
            pscale = w.calc_plot_scale()
            for key, val in pscale.items():
                if key not in d:
                    d[key] = val
                    continue
                if 'min' in key:
                    if val < d[key]:
                        d[key] = val
                elif 'max' in key:
                    if val > d[key]:
                        d[key] = val
        for attr, val in d.items():
            if not auto_x and attr.split('_')[0] == 'x':
                continue
            if not auto_y and attr.split('_')[0] == 'y':
                continue
            setattr(self, attr, val)
        if self.x_tick_line is None:
            self.build_ticklines()
    def build_tick_data(self):
        x = np.linspace(self.x_min, self.x_max, 10)
        y = np.linspace(self.y_min, self.y_max, 10)
        self.x_tick_data = x.tolist()
        self.y_tick_data = y.tolist()
        if self.x_tick_line is not None:
            self.x_tick_line.ticks[1].data = self.x_tick_data
            self.y_tick_line.ticks[1].data = self.y_tick_data
    def build_ticklines(self):
        self.x_ticks = dict(
            #minor=LabellessTick(tick_size=[1, 4], scale_factor=25.), 
            #major=Tick(tick_size=[2, 10], scale_factor=5.), 
            #label=DataListTick(
        )
        self.y_ticks = dict(
            #minor=LabellessTick(tick_size=[1, 4], scale_factor=25.), 
            #major=Tick(tick_size=[2, 10], scale_factor=5.), 
            #label=DataListTick(
        )
        #keys = ['major', 'minor']
        #x_tick_list = [self.x_ticks[key] for key in keys]
        #y_tick_list = [self.y_ticks[key] for key in keys]
        self.build_tick_data()
        print self.x_tick_data, self.y_tick_data
        self.x_tick_line = Tickline(cover_background=False, background_color=(0.,0.,0.,0.), draw_line=False,#size_hint=[1., 1.], pos_hint={'x':0., 'y':0.}, 
                                    orientation='horizontal', 
                                    ticks=[Tick(), DataListTick(data=self.x_tick_data, scale_factor=10., valign='line_top')])
        self.y_tick_line = Tickline(cover_background=False, background_color=(0.,0.,0.,0.), draw_line=False,#size_hint=[1., 1.], pos_hint={'x':0., 'y':0.}, 
                                    orientation='vertical', 
                                    ticks=[Tick(), DataListTick(data=self.y_tick_data, scale_factor=10., halign='line_left')])
        self.tick_container.add_widget(self.x_tick_line)
        self.tick_container.add_widget(self.y_tick_line)
        
    def freq_to_x(self, freq):
        x = (freq - self.x_min) / self.x_size
        return x * self.width
    def db_to_y(self, db):
        y = (db - self.y_min) / self.y_size
        return y * self.height
    def _serialize(self):
        attrs = ['x_max', 'x_min', 'y_max', 'y_min', 
                 'auto_scale_x', 'auto_scale_y']
        d = {attr:getattr(self, attr) for attr in attrs}
        d['plots'] = []
        for plot in self.children:
            if not isinstance(plot, SpectrumPlot):
                continue
            d['plots'].append(plot._serialize())
        return d
    def _deserialize(self, **kwargs):
        for c in self.children[:]:
            if isinstance(c, SpectrumPlot):
                self.remove_widget(c)
        for key, val in kwargs.items():
            if key == 'plots':
                for pldata in val:
                    plot = SpectrumPlot.from_json(pldata)
                    self.add_plot(plot=plot)
                    self.parent.tool_panel.add_plot(plot)
            else:
                setattr(self, key, val)
        
class SpectrumPlot(Widget, JSONMixin):
    name = StringProperty('')
    points = ListProperty([])
    color = ListProperty([0., 1., 0., .8])
    enabled = BooleanProperty(True)
    selected = BooleanProperty(False)
    def __init__(self, **kwargs):
        super(SpectrumPlot, self).__init__(**kwargs)
        self.spectrum = kwargs.get('spectrum')
        if self.spectrum is not None:
            self.build_data()
        if self.parent is not None:
            self.parent.bind(plot_params=self._trigger_update)
            self.parent.calc_plot_scale()
        self.bind(parent=self.on_parent_set)
        self.bind(pos=self._trigger_update, size=self._trigger_update)
    def on_parent_set(self, *args, **kwargs):
        if self.parent is None:
            return
        self.parent.bind(plot_params=self._trigger_update)
        self.parent.calc_plot_scale()
    def on_enabled(self, instance, value):
        if value:
            self._trigger_update()
        else:
            self.points = []
    def _trigger_update(self, *args, **kwargs):
        self.draw_plot()
    def draw_plot(self):
        if self.parent is None:
            return
        freq_to_x = self.parent.freq_to_x
        db_to_y = self.parent.db_to_y
        self.points = []
        if not self.enabled:
            return
        xy_data = self.xy_data
        for freq, db in zip(xy_data['x'], xy_data['y']):
            xy = [freq_to_x(freq), db_to_y(db)]
            self.points.extend(xy)
    def update_data(self):
        if not self.spectrum.data_updated.is_set():
            return
        self.build_data()
        self.parent.calc_plot_scale()
        self.draw_plot()
    def build_data(self):
        spectrum = self.spectrum
        dtype = np.dtype(float)
        with spectrum.data_update_lock:
            x = np.fromiter(spectrum.iter_frequencies(), dtype)
            y = np.fromiter((s.magnitude for s in spectrum.iter_samples()), dtype)
            self.xy_data = {'x':x, 'y':y}
            spectrum.data_updated.clear()
    def calc_plot_scale(self):
        d = {}
        for key, data in self.xy_data.items():
            for mkey in ['min', 'max']:
                _key = '_'.join([key, mkey])
                m = getattr(data, mkey)
                val = float(m())
                if mkey == 'min':
                    val -= 1
                else:
                    val += 1
                d[_key] = val
        return d
    def _serialize(self):
        attrs = ['name', 'color', 'enabled', 'selected']
        d = {attr: getattr(self, attr) for attr in attrs}
        d['spectrum_data'] = self.spectrum._serialize()
        return d
    def _deserialize(self, **kwargs):
        spdata = kwargs.get('spectrum_data')
        self.spectrum = Spectrum.from_json(spdata)
        self.build_data()

class PlotToolPanel(GridLayout):
    def add_plot(self, plot_widget):
        self.add_widget(PlotTools(plot=plot_widget))
        
class PlotTools(BoxLayout):
    label_widget = ObjectProperty(None)
    switch_widget = ObjectProperty(None)
    color_btn = ObjectProperty(None)
    plot = ObjectProperty(None)
    root_widget = ObjectProperty(None)
    def on_plot(self, *args, **kwargs):
        if self.plot is None:
            return
        self.plot.bind(parent=self.on_plot_parent)
    def on_plot_parent(self, *args, **kwargs):
        if self.plot is None:
            return
        if self.plot.parent is None:
            self.parent.remove_widget(self)
    def on_color_btn_release(self, *args, **kwargs):
        self.color_picker = PlotColorPicker(color=self.plot.color)
        self.color_picker.bind(on_select=self.on_color_picker_select, 
                               on_cancel=self.on_color_picker_cancel)
        root = self.root_widget
        popup = root.show_popup(title='Choose Color', content=self.color_picker, 
                                size_hint=(.9, .9), auto_dismiss=False)
        popup.bind(on_dismiss=self.on_popup_dismiss)
    def on_color_picker_select(self, *args):
        self.plot.color = self.color_picker.color
        self.root_widget.close_popup()
    def on_color_picker_cancel(self, *args):
        self.root_widget.close_popup()
    def on_popup_dismiss(self, *args, **kwargs):
        self.color_picker = None
        
class PlotColorPicker(BoxLayout):
    color = ListProperty([.8, .8, .8, 1.])
    color_picker = ObjectProperty(None)
    ok_btn = ObjectProperty(None)
    cancel_btn = ObjectProperty(None)
    __events__ = ('on_select', 'on_cancel')
    def on_select(self, *args):
        pass
    def on_cancel(self, *args):
        pass
        
