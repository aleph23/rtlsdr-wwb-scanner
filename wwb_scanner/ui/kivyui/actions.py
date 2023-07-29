import os
import datetime

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.garden.filebrowser import FileBrowser
from kivy.properties import (
    ObjectProperty,
    DictProperty,
    NumericProperty,
    StringProperty,
    ColorProperty,
    AliasProperty,
)

from wwb_scanner.utils.color import Color
from wwb_scanner.utils.dbstore import db_store
from wwb_scanner.file_handlers import BaseImporter
from wwb_scanner.scan_objects import Spectrum

from wwb_scanner.ui.kivyui.treeutils import SortableTreeView, SortableNode

class Action(object):
    _instances = {}
    def __init__(self, **kwargs):
        if not hasattr(self, 'name'):
            self.name = kwargs.get('name')
        self.callback = kwargs.get('callback')
        Action._instances[self.name] = self
    @classmethod
    def build_from_subclasses(cls):
        for _cls in Action.__subclasses__():
            _cls()
    @classmethod
    def trigger_by_name(cls, name, app):
        action = Action._instances.get(name)
        return action(app)
    def __call__(self, app):
        cb = self.callback
        return cb(action=self, app=app) if cb is not None else self.do_action(app)

class FileQuit(Action):
    name = 'file.quit'
    def do_action(self, app):
        app.stop()

class FileAction(object):
    @property
    def last_path(self):
        return self.get_last_path()
    def get_last_path(self):
        p = getattr(self, '_last_path', None)
        if p is None:
            p = os.getcwd()
        return p
    def get_select_string(self):
        return getattr(self, 'select_string', '')
    def get_title(self):
        return getattr(self, 'title', '')
    def get_filters(self):
        return getattr(self, 'filters', [])
    def build_browser(self, **kwargs):
        kwargs.setdefault('select_string', self.get_select_string())
        kwargs.setdefault('path', self.last_path)
        kwargs.setdefault('filters', self.get_filters())
        return FileBrowser(**kwargs)
    def do_action(self, app):
        self.app = app
        title = self.get_title()
        browser = self.build_browser()
        browser.bind(on_success=self.on_browser_success)
        browser.bind(on_canceled=self.on_browser_canceled)
        app.root.show_popup(title=title, content=browser,
                            size_hint=(.9, .9), auto_dismiss=False)
    def dismiss(self):
        self.app.root.close_popup()
    def on_browser_success(self, instance):
        self.dismiss()
    def on_browser_canceled(self, instance):
        self.dismiss()

class FileSaveAs(Action, FileAction):
    name = 'file.save_as'
    select_string = 'Save As'
    title = 'Save Session As'
    filters = ['*.json', '*.JSON']
    def on_browser_success(self, instance):
        filename = instance.filename
        if not len(filename):
            self.app.root.show_message(message='Please enter a filename')
            return
        _fn, ext = os.path.splitext(filename)
        if not len(ext):
            filename = os.path.extsep.join([_fn, 'json'])
        #elif '*.%s' % (ext) not in self.filters:
        #    self.app.root.show_message(message='Only "json" files are currently supported')
        #    return
        filename = os.path.join(instance.path, filename)
        self.dismiss()
        s = self.app.root.to_json(indent=2)
        with open(filename, 'w') as f:
            f.write(s)
        self.app.root.current_filename = filename
        self.app.root.show_message(title='Success', message='File saved as\n%s' % (filename))

class FileSave(Action):
    name = 'file.save'
    def do_action(self, app):
        filename = app.root.current_filename
        if not filename:
            Action.trigger_by_name('file.save_as', app)
            return
        s = app.root.to_json(indent=2)
        with open(filename, 'w') as f:
            f.write(s)
        app.root.status_bar.message_text = 'File saved'

class FileOpen(Action, FileAction):
    name = 'file.open'
    select_string = 'Open'
    title = 'Open Session'
    filters = ['*.json', '*.JSON']
    def on_browser_success(self, instance):
        filename = os.path.join(instance.path, instance.filename)
        with open(filename, 'r') as f:
            s = f.read()
        self.dismiss()
        self.app.root.instance_from_json(s)
        self.app.root.current_filename = filename

class ScrolledTree(BoxLayout):
    app = ObjectProperty(None)
    tree = ObjectProperty(None)
    sort_header = ObjectProperty(None)
    __events__ = ['on_cancel', 'on_load']
    def on_cancel(self, *args):
        self.app.root.close_popup()
    def on_load(self, *args):
        node = self.tree.selected_node
        if node is None:
            return
        spectrum = Spectrum.from_dbstore(eid=node.eid)
        self.app.root.plot_container.add_plot(spectrum=spectrum)
        self.app.root.close_popup()
    def on_sort_header(self, *args):
        self.sort_header.bind(active_cell=self.on_sort_cell, descending=self.on_sort_descending)
    def on_sort_cell(self, instance, cell):
        if cell is None:
            self.tree.root.sort_property_name = '__index__'
        else:
            self.tree.root.sort_property_name = cell.sort_property
    def on_sort_descending(self, instance, value):
        self.tree.root.descending = value

class ScrolledTreeView(SortableTreeView):
    def __init__(self, **kwargs):
        kwargs['root_options'] = {'sort_property_name':'datetime'}
        super(ScrolledTreeView, self).__init__(**kwargs)
        self.bind(minimum_height=self.setter('height'))
        scan_data = db_store.get_all_scans()
        for eid, scan in scan_data.items():
            scan_node = self.add_node(ScrolledTreeNode(eid=eid, scan_data=scan))


class ScrolledTreeNode(BoxLayout, SortableNode):
    eid = NumericProperty()
    name = StringProperty()
    datetime = ObjectProperty()
    scan_color = ColorProperty([0,0,0,0])
    scan_data = DictProperty()
    def __init__(self, **kwargs):
        super(ScrolledTreeNode, self).__init__(**kwargs)
        self.name = str(self.scan_data.get('name'))
        self.datetime = datetime.datetime.fromtimestamp(self.scan_data['timestamp_utc'])
        c = Color(**self.scan_data['color'])
        self.scan_color = c.to_list()

class SquareTexture(Widget):
    def get_rect_size(self):
        w, h = self.size
        size = [h, h] if h < w else [w, w]
        return size
    def set_rect_size(self, value):
        pass
    rect_size = AliasProperty(get_rect_size, set_rect_size, bind=['size'])
    def get_rect_pos(self):
        w, h = self.rect_size
        x = self.center_x - w/2.
        y = self.center_y - h/2.
        return [x, y]
    def set_rect_pos(self, value):
        pass
    rect_pos = AliasProperty(get_rect_pos, set_rect_pos, bind=['pos', 'rect_size'])

class ColorBox(SquareTexture):
    scan_color = ColorProperty([0,0,0,0])


class PlotsLoadRecent(Action):
    name = 'plots.load_recent'
    def do_action(self, app):
        self.app = app
        scroll_view = ScrolledTree()
        app.root.show_popup(title='Load Scan', content=scroll_view, size_hint=(.9, .9))

class PlotsImport(Action, FileAction):
    name = 'plots.import'
    select_string = 'Import'
    title = 'Import Plot'
    def get_filters(self):
        exts = ['csv', 'sdb2']
        filters = ['.'.join(['*', ext]) for ext in exts]
        filters.extend(['.'.join(['*', ext.upper()]) for ext in exts])
        return filters
    def on_browser_success(self, instance):
        filename = instance.selection[0]
        self.dismiss()
        spectrum = BaseImporter.import_file(filename)
        self.app.root.plot_container.add_plot(spectrum=spectrum, filename=filename)

class PlotsExport(Action, FileAction):
    name = 'plots.export'
    select_string = 'Export'
    title = 'Export Selected Plot'
    def get_filters(self):
        exts = ['csv', 'sdb2']
        filters = ['.'.join(['*', ext]) for ext in exts]
        filters.extend(['.'.join(['*', ext.upper()]) for ext in exts])
        return filters
    def do_action(self, app):
        self.plot = app.root.plot_container.spectrum_graph.selected
        if self.plot is None:
            app.root.show_message(message='There is not plot to export')
            return
        super(PlotsExport, self).do_action(app)
    def on_browser_success(self, instance):
        filters = self.get_filters()
        filename = instance.filename
        if not len(filename):
            self.app.root.show_message(message='Please enter a filename')
            return
        _fn, ext = os.path.splitext(filename)
        if not len(ext):
            filename = os.path.extsep.join([_fn, 'csv'])
        elif f"*.{ext.lstrip('.')}" not in filters:
            self.app.root.show_message(
                message='Only "csv" and "sdb2" files are currently supported',
            )
            return
        filename = os.path.join(instance.path, filename)
        self.dismiss()
        self.plot.spectrum.export_to_file(filename=filename)
        self.app.root.show_message(title='Success', message='File exported to\n%s' % (filename))


Action.build_from_subclasses()
