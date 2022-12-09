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


from ipywidgets import DOMWidget
from ._frontend import module_name, module_version
import traitlets
from ipyevents import Event
from typing import Dict

from pathlib import Path
from typing import Tuple
import soundfile as sf

import networkx as nx
import numpy as np
import base64
import io
import random
import string

# TODO: use soundfile in place of wavfile to remove one dependency
import scipy.io.wavfile

from .annotation import get_annotation


class WavesurferWidget(DOMWidget):
    """wavesurfer.js widget
    
    Usage
    -----
    widget = WavesurferWidget()
    """

    _model_name = traitlets.Unicode("WavesurferModel").tag(sync=True)
    _model_module = traitlets.Unicode(module_name).tag(sync=True)
    _model_module_version = traitlets.Unicode(module_version).tag(sync=True)
    _view_name = traitlets.Unicode("WavesurferView").tag(sync=True)
    _view_module = traitlets.Unicode(module_name).tag(sync=True)
    _view_module_version = traitlets.Unicode(module_version).tag(sync=True)

    audio = traitlets.Unicode().tag(sync=True)

    labels = traitlets.Dict().tag(sync=True)
    colors = traitlets.Dict().tag(sync=True)
    active_label = traitlets.Unicode("A").tag(sync=True)

    playing = traitlets.Bool(False).tag(sync=True)
    time = traitlets.Float(0.0).tag(sync=True)
    zoom = traitlets.Int(20).tag(sync=True)

    regions = traitlets.List().tag(sync=True)
    active_region = traitlets.Unicode("").tag(sync=True)

    overlap = traitlets.Dict().tag(sync=True)

    def __init__(self, file: Path, precision: Tuple[float, float] = (0.1, 0.5)):
        super().__init__()
        self.file = file
        self.precision = tuple(precision)
        self.sample_rate = 16000
        self.audio = self.to_base64(file)

        # keyboard shortcuts handler
        self._keyboard = Event(source=self, watched_events=["keydown"])
        self._keyboard.on_dom_event(self.keyboard)

    def to_base64(self, file: Path):
        waveform, sample_rate = sf.read(file)
        waveform /= np.max(np.abs(waveform)) + 1e-8
        with io.BytesIO() as content:
            scipy.io.wavfile.write(content, sample_rate, waveform.astype(np.float32))
            content.seek(0)
            b64 = base64.b64encode(content.read()).decode()
            b64 = f"data:audio/x-wav;base64,{b64}"
        return b64

    def get_time(self):
        return self.time

    def set_time(self, time):
        if self.playing:
            raise NotImplementedError("Setting time while playing is not supported.")
        self.time = max(0.0, time)

    t = property(get_time, set_time)

    @traitlets.observe("regions")
    def on_regions_change(self, change: Dict):
        """
        1. reset active region if it no longer exists
        2. update regions overlap layout
        """

        # reset active region if it no longer exists
        if self.active_region not in list(region["id"]for region in change["new"]):
            self.active_region = ""

        # convert regions to pyannote.core.Annotation
        annotation = get_annotation(self.regions, self.labels)

        # compute overlap graph (one node per region, edges between overlapping regions)
        overlap_graph = nx.Graph()
        for (s1, t1), (s2, t2) in annotation.co_iter(annotation):
            overlap_graph.add_edge((s1, t1), (s2, t2))

        # solve the graph coloring problem for each connected subgraph
        # and use the solution for regions layout
        overlap = dict()
        for sub_graph in nx.connected_components(overlap_graph):
            sub_coloring = nx.coloring.greedy_color(
                overlap_graph.subgraph(sorted(sub_graph))
            )

            num_colors = max(sub_coloring.values()) + 1
            for (_, region_id), color in sub_coloring.items():
                if num_colors > 4:
                    overlap[region_id] = {"level": (color % 4) + 1, "num_levels": 4}
                else:
                    overlap[region_id] = {"level": color + 1, "num_levels": num_colors}
        self.overlap = overlap

    @traitlets.observe("active_label")
    def update_label(self, change: Dict):
        active_label = change["new"]
        if self.active_region and active_label:
            regions = list()
            for region in self.regions:
                if region["id"] == self.active_region:
                    regions.append({"start": region["start"], "end": region["end"], "id": region["id"], "label": self.active_label})
                else:
                    regions.append(region)
            self.regions = regions

    @traitlets.observe("active_region")
    def update_active_label(self, change: Dict):
        """Set active_label to active_region label"""
        active_region = change["new"]
        for region in self.regions:
            if region["id"] == active_region:
                self.active_label = region["label"]
                break

    def keyboard(self, event):

        # for debugging purposes...
        self._last_event = event

        key = event["key"]
        code = event["code"]
        shift = event["shiftKey"]
        alt = event["altKey"]

        # [ space ] toggles play/pause status
        if key == " ":
            self.playing = not self.playing

        # [ tab ] selects next region and move cursor to its start time
        # [ shift + tab ] selects previous region and move cursor to its start time
        elif key == "Tab":
            direction = -1 if shift else 1
            # sort regions by start time (resp. end time) when going forward (resp. backward)
            if direction > 0:
                regions = sorted(self.regions, key=lambda r: (r["start"], r["end"]))
            else:
                regions = sorted(self.regions, key=lambda r: (r["end"], r["start"]))

            if not regions:
                return
            
            if self.active_region:
                region_ids = [region["id"] for region in regions]
                active_region = regions[
                    (region_ids.index(self.active_region) + direction)
                    % len(region_ids)
                ]
            else:
                i = -1 if shift else 0
                active_region = regions[i]

            self.active_region = active_region["id"]

            # move cursor to selected region start time
            playing = self.playing
            self.playing = False
            self.time = active_region["start"]
            self.playing = playing

        # [ esc ] deactivates all regions
        elif key == "Escape":
            self.active_region = ""

        # [ letter ] activates corresponding label
        # side effect is to update the label of the currently active region
        elif key in string.ascii_lowercase:
            self.active_label = key

        # When no region is active:
        # [ left  ] moves cursor to the left
        # [ right ] moves cursor to the right
        # When a region is active:
        # [ left  ] moves start time to the left
        # [ right ] moves start time to the right
        # [ left + alt  ] moves end time to the left
        # [ right + alt ] moves end time to the right
        # Speed is controlled by `precision` and [ shift ] key
        elif key in {"ArrowLeft", "ArrowRight"}:
            direction = -1 if key == "ArrowLeft" else 1
            delta = self.precision[shift] * direction
            if self.active_region:
                self.playing = False
                regions = list()
                for region in self.regions:
                    if region["id"] == self.active_region:
                        if alt:
                            start = region["start"]
                            end = region["end"] + delta
                            if self.t > end:
                                self.t = end - 1.0
                        else:
                            start = region["start"] + delta
                            end = region["end"]
                            self.t = start
                        regions.append({"start": start, "end": end, "id": region["id"], "label": region["label"]})
                    else:
                        regions.append(region)
                self.regions = regions
                self.playing = True
            else:
                self.t += delta

        elif key in {"ArrowUp", "ArrowDown"}:
            direction = -1 if key == "ArrowDown" else 1
            self.zoom = self.zoom + direction

        # [ backspace ] removes active region and activates the one on the left
        # [ delete ] removes active regions and activates the one on the right
        elif key in {"Backspace", "Delete"}:
            if not self.active_region:
                return
            direction = -1 if key == "Backspace" else 1

            # sort regions by start time (resp. end time) when going forward (resp. backward)
            if direction > 0:
                regions = sorted(self.regions, key=lambda r: (r["start"], r["end"]))
            else:
                regions = sorted(self.regions, key=lambda r: (r["end"], r["start"]))

            region_ids = [region["id"] for region in regions]
            active_region = regions[
                (region_ids.index(self.active_region) + direction) % len(region_ids)
            ]["id"]

            regions = list(filter(lambda r: r["id"] != self.active_region, self.regions))
            if regions:
                self.active_region = active_region
            else:
                self.active_region = ""
            self.regions = regions

        # [ enter ] creates a new region at current time
        elif key == "Enter":
            regions = list(self.regions)
            region_id = "".join(random.choices(string.ascii_lowercase, k=20))
            regions.append({
                "start": self.t,
                "end": self.t + self.precision[1],
                "id": region_id,
                "label": self.active_label
            })
            self.regions = regions
            self.active_region = region_id


# https://github.com/jupyter-widgets/ipywidgets/blob/c5103e4084324dc80734fc14ceeafc973e13402f/docs/source/examples/Widget%20Custom.ipynb

# keyboard shortcut ideas
# https://support.prodi.gy/t/audio-ui-enhancement-keyboard-shortcuts-and-clickthrough/3412
