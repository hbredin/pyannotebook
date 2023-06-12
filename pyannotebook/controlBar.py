# MIT License
#
# Copyright (c) 2022- CNRS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


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