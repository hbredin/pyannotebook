# python back end of the control bar of the widget. Front end is define in widgets.ts in the src folder. The code is based on the exemple of label.py.

from xmlrpc.client import Boolean
import ipywidgets
import traitlets
from ._frontend import module_name, module_version
from typing import Dict

# liste des "play_command" possibles
#    "fast_backward"
#    "backward"
#    "play"
#    "forward"
#    "fast_forward"
#    "none"

# liste des "control_bar" possibles
#    "insert"
#    "cut"
#    "delete"
#    "none"


class ControlBarWidget(ipywidgets.Widget):

    _model_name = traitlets.Unicode("ControlBarModel").tag(sync=True)
    _model_module = traitlets.Unicode(module_name).tag(sync=True)
    _model_module_version = traitlets.Unicode(module_version).tag(sync=True)
    _view_name = traitlets.Unicode("ControlBarView").tag(sync=True)
    _view_module = traitlets.Unicode(module_name).tag(sync=True)
    _view_module_version = traitlets.Unicode(module_version).tag(sync=True)

    play_command = traitlets.Unicode("none").tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
    control_bar = traitlets.Unicode("none").tag(sync=True)

    def __init__(self):
        super().__init__()


    @traitlets.observe("play_command")
    def play_command_has_changed(self, change: Dict):
        pass

    @traitlets.observe("control_bar")
    def control_bar_has_changed(self, change: Dict):
        pass