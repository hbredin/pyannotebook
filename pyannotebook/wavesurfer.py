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
from typing import Dict, Tuple, Union, Text, Optional

from pathlib import Path

try:
    import soundfile as sf
    SOUNDFILE_IS_AVAILABLE = True
except OSError as e:
    SOUNDFILE_IS_AVAILABLE = False
    print("Could not import `soundfile`: using `scipy.io.wavfile` instead, with limited audio file format support.")

import networkx as nx
import numpy as np
import base64
import io
import random
import string
import scipy.io.wavfile

from .annotation import get_annotation

from itertools import filterfalse, tee

def partition(pred, iterable):
    "Use a predicate to partition entries into false entries and true entries"
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)


class WavesurferWidget(DOMWidget):
    """wavesurfer.js widget
    
    Parameters
    ----------
    minimap : bool, optional
        Display a minimap on top of waveform. Defaults to True.
    auto_select : bool, optional
        Automatically select region corresponding to current time.
        Defaults to False.

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

    b64 = traitlets.Unicode().tag(sync=True)
    minimap = traitlets.Bool().tag(sync=True)

    labels = traitlets.Dict().tag(sync=True)
    colors = traitlets.Dict().tag(sync=True)
    active_label = traitlets.Unicode("A").tag(sync=True)

    playing = traitlets.Bool(False).tag(sync=True)
    time = traitlets.Float(0.0).tag(sync=True)
    zoom = traitlets.Int(20).tag(sync=True)

    regions = traitlets.List().tag(sync=True)
    active_region = traitlets.Unicode("").tag(sync=True)

    overlap = traitlets.Dict().tag(sync=True)

    play_command = traitlets.Unicode("none").tag(sync=True)
    control_bar_command = traitlets.Unicode("none").tag(sync=True)

    def __init__(
        self, 
        audio: Optional[Union[Text, Path, Tuple[np.ndarray, int]]] = None, 
        precision: Tuple[float, float] = (0.1, 0.5),
        minimap: bool = True,
        auto_select: bool = False,
    ):
        super().__init__()
        self.precision = tuple(precision)
        self.minimap = minimap
        self.auto_select = auto_select
    
        if audio is None:
            del self.audio
        else:
            self.audio = audio

        # keyboard shortcuts handler
        self._keyboard = Event(source=self, watched_events=["keydown"])
        self._keyboard.on_dom_event(self.keyboard)

    def to_base64(self, waveform: np.ndarray, sample_rate: int) -> Text:
        with io.BytesIO() as content:
            scipy.io.wavfile.write(content, sample_rate, waveform)
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

    t = property(get_time, set_time, None)

    def set_audio(self, audio: Union[Text, Path, Tuple[np.ndarray, int]]):

        if isinstance(audio, (str, Path)):
            if SOUNDFILE_IS_AVAILABLE:
                waveform, sample_rate = sf.read(audio)
            else:
                sample_rate, waveform = scipy.io.wavfile.read(audio)

        else:
            waveform, sample_rate = audio
            assert isinstance(waveform, np.ndarray)
            assert waveform.ndim == 1

        waveform = waveform.astype(np.float32)
        waveform /= np.max(np.abs(waveform)) + 1e-8

        self.b64 = self.to_base64(waveform, sample_rate)

    def del_audio(self):
        sample_rate = 16000
        waveform = np.zeros((sample_rate, ), dtype=np.float32)
        self.audio = (waveform, sample_rate)

    audio = property(None, set_audio, del_audio)

    @traitlets.observe("b64")
    def on_b64_change(self, change: Dict):
        self.regions = list()

    @traitlets.observe("time")
    def on_time_change(self, change: Dict):
        """Automatically select region corresponding to current time"""

        # skip if auto_select is disabled or no region exists
        if not (self.auto_select and self.regions):
            return
        
        # read current time
        current_time = change['new']
        
        # Gather list of regions overlapping current time
        # because of Javascript/Python/wavesurfer.seek conversion, we allow a bit of tolerance on both sides.
        # in particular, this avoids a corner case where Python side asks to seek to a region start time and
        # Javascript/Wavesurfer side does not manage to seek to this exact time and ends up outside of the region.
        overlapping_regions = list(filter(lambda r: r["start"] - 0.01 <= current_time <= r["end"] + 0.01, self.regions))
        if not overlapping_regions:
            return

        # among every overlapping regions, select the one whose start time is the closest
        self.active_region = min(overlapping_regions, key=lambda r: abs(r["start"] - current_time))["id"]

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
                    regions.append(region) # ligne qui ajoute les regions quand appuye sur touche ?
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

        # [ esc ] unselects all regions
        elif key == "Escape":
            self.active_region = ""

        # [ letter ] selects corresponding label
        # side effect is to update the label of the currently selected region
        elif key in string.ascii_lowercase:
            self.active_label = key

        # When no region is selected:
        # [ left  ] moves cursor to the left
        # [ right ] moves cursor to the right
        # When a region is selected:
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

        # [ up ] zooms in
        # [ down ] zooms out
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
        # [ shift + enter ] split selected region at current time

        elif key == "Enter":

            if shift:
                # check that a region is selected...
                if not self.active_region:
                    return

                other_regions, selected_region = partition(lambda r: r["id"] == self.active_region, self.regions)
                other_regions = list(other_regions)
                selected_region = list(selected_region)[0]

                # check that selected region contains current time
                if self.t < selected_region["start"] or self.t > selected_region["end"]:
                    return
            
                # split selected region into first and second halves  
                first_half = {
                    "start": selected_region["start"],
                    "end": self.t,
                    "id": selected_region["id"],
                    "label": selected_region["label"]
                }
                region_id = "".join(random.choices(string.ascii_lowercase, k=20))
                second_half = {
                    "start": self.t,
                    "end": selected_region["end"],
                    "id": region_id,
                    "label": selected_region["label"]
                }
                
                # append to halves to list of regions
                self.regions = other_regions + [first_half, second_half]

                # selects second half
                self.active_region = region_id

            else:
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
        

# keyboard shortcut ideas
# https://support.prodi.gy/t/audio-ui-enhancement-keyboard-shortcuts-and-clickthrough/3412
    @traitlets.observe("play_command")
    def _on_play_command(self, change: Dict):
        # define direction and speed
        command = change["new"]

        if command == "play":
                self.playing = not self.playing

        elif command == "backward":
                direction = -1
                speed = False

        elif command == "forward":
                direction = 1
                speed = False

        elif command == "fast_backward":
                direction = -1
                speed = True

        elif command == "fast_forward":
                direction = 1
                speed = True

        elif command == "none":
                return
            
        else:
                raise ValueError(f"Unsupported play command '{change['new']}'")
        
        # apply move, with special handling for active region
        delta = self.precision[speed] * direction
            
        if self.active_region:
            self.playing = False
            regions = list()
            for region in self.regions:
                if region["id"] == self.active_region:
                    if speed:
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


    @traitlets.observe("control_bar_command")
    def _on_control_bar(self, change: Dict):
        
        command = change["new"]
        
        if command ==  "delete_region":
                if not self.active_region:
                    return
                regions = sorted(self.regions, key=lambda r: (r["start"], r["end"]))
                region_ids = [region["id"] for region in regions]
                active_region = regions[
                    (region_ids.index(self.active_region) + 1) % len(region_ids)
                ]["id"]

                regions = list(filter(lambda r: r["id"] != self.active_region, self.regions))
                if regions:
                    self.active_region = active_region
                else:
                    self.active_region = ""
                self.regions = regions


        elif command == "insert_region":

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

        elif command == "cut_region":
                 # check that a region is selected...
                if not self.active_region:
                    return

                other_regions, selected_region = partition(lambda r: r["id"] == self.active_region, self.regions)
                other_regions = list(other_regions)
                selected_region = list(selected_region)[0]

                # check that selected region contains current time
                if self.t < selected_region["start"] or self.t > selected_region["end"]:
                    return
            
                # split selected region into first and second halves  
                first_half = {
                    "start": selected_region["start"],
                    "end": self.t,
                    "id": selected_region["id"],
                    "label": selected_region["label"]
                }
                region_id = "".join(random.choices(string.ascii_lowercase, k=20))
                second_half = {
                    "start": self.t,
                    "end": selected_region["end"],
                    "id": region_id,
                    "label": selected_region["label"]
                }
                
                # append to halves to list of regions
                self.regions = other_regions + [first_half, second_half]

                # selects second half
                self.active_region = region_id

        elif command == "none":
                return
            
        else:
                raise ValueError(f"Unsupported control command '{change['new']}'")
            
        self.play_command = "none"