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
