# python back end of the control bar of the widget. Front end is define in widgets.ts in the src folder. The code is based on the exemple of label.py.

from xmlrpc.client import Boolean
import ipywidgets
import traitlets
from ._frontend import module_name, module_version
from typing import Dict

class ControlBarWidget(ipywidgets.Widget):

    _model_name = traitlets.Unicode("ControlBarModel").tag(sync=True)
    _model_module = traitlets.Unicode(module_name).tag(sync=True)
    _model_module_version = traitlets.Unicode(module_version).tag(sync=True)
    _view_name = traitlets.Unicode("ControlBarView").tag(sync=True)
    _view_module = traitlets.Unicode(module_name).tag(sync=True)
    _view_module_version = traitlets.Unicode(module_version).tag(sync=True)

    playing = traitlets.Bool(False).tag(sync=True)


    def __init__(self):
        super().__init__()


    @traitlets.observe("playing")
    def playing_has_changed(self, change: Boolean):
        pass