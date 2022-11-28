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

import ipywidgets
import traitlets
from ._frontend import module_name, module_version
from itertools import cycle
from typing import Dict

COLORS = [
    "#ffd700",
    "#00ffff",
    "#ff00ff",
    "#00ff00",
    "#9932cc",
    "#00bfff",
    "#ff7f50",
    "#66cdaa",
]

class LabelsWidget(ipywidgets.Widget):
    """Labels widget

    Usage
    -----
    widget = LabelsWidget()

    Traitlets
    ---------
    labels : str -> human-readable
    colors : str -> color

    """

    _model_name = traitlets.Unicode("LabelsModel").tag(sync=True)
    _model_module = traitlets.Unicode(module_name).tag(sync=True)
    _model_module_version = traitlets.Unicode(module_version).tag(sync=True)
    _view_name = traitlets.Unicode("LabelsView").tag(sync=True)
    _view_module = traitlets.Unicode(module_name).tag(sync=True)
    _view_module_version = traitlets.Unicode(module_version).tag(sync=True)

    labels = traitlets.Dict().tag(sync=True)
    active_label = traitlets.Unicode("a").tag(sync=True)
    colors = traitlets.Dict().tag(sync=True)

    def __init__(self):
        super().__init__()
        self._color_pool = cycle(COLORS)

    @traitlets.observe("labels")
    def labels_has_changed(self, change: Dict):
        """Update label-to-color mapping when `labels` changes"""

        old_labels = change["old"]
        new_labels = change["new"]
        
        if not new_labels:
            self.colors = dict()

        added_labels = set(new_labels) - set(old_labels)
        if added_labels:
            new_colors = dict(self.colors)
            for label in added_labels:
                new_colors[label] = next(self._color_pool)
            self.colors = new_colors
