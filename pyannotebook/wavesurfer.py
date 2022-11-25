#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Hervé Bredin.
# Distributed under the terms of the Modified BSD License.

"""
TODO: Add module docstring
"""

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
    def update_overlap_layout(self, change: Dict):
        """Update regions overlap"""
        annotation = get_annotation(self.regions, self.labels)

        overlap_graph = nx.Graph()
        for (s1, t1), (s2, t2) in annotation.co_iter(annotation):
            overlap_graph.add_edge((s1, t1), (s2, t2))

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

        # [ tab ] activates next region
        # [ shift + tab ] activates previous region
        elif key == "Tab":
            # FIXME: sort by end time when moving backward
            regions = sorted(self.regions, key=lambda r: (r["start"], r["end"]))
            direction = -1 if shift else 1
            if not regions:
                return
            if self.active_region:
                region_ids = [region["id"] for region in regions]
                self.active_region = regions[
                    (region_ids.index(self.active_region) + direction)
                    % len(region_ids)
                ]["id"]
            else:
                i = -1 if shift else 0
                self.active_region = regions[i]["id"]

        # [ esc ] deactivates all regions
        elif key == "Escape":
            self.active_region = ""

        # [ letter ] assigns label letter to currently active region
        elif key in string.ascii_lowercase:
            self.active_label = key
            if self.active_region:
                regions = list()
                for region in self.regions:
                    if region["id"] == self.active_region:
                        regions.append({"start": region["start"], "end": region["end"], "id": region["id"], "label": self.active_label})
                    else:
                        regions.append(region)
                self.regions = regions

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

        # [ backspace ] removes active region and activates the one on the left
        # [ delete ] removes active regions and activates the one on the right
        elif key in {"Backspace", "Delete"}:
            if not self.active_region:
                return
            direction = -1 if key == "Backspace" else 1
            # FIXME: sort by end time when moving backward
            regions = sorted(self.regions, key=lambda r: (r["start"], r["end"]))
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