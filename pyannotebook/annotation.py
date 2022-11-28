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
from typing import Dict, Optional
from pyannote.core import Annotation, Segment
from pyannote.core.utils.generators import string_generator
from itertools import filterfalse, count
import random
import string

def get_annotation(regions, labels):
    annotation = Annotation()
    for region in regions:
        annotation[Segment(region["start"], region["end"]), region["id"]] = labels.get(region["label"], region["label"])
    return annotation


class AnnotationWidget(ipywidgets.Widget):
    """Annotation widget
    
    
    Usage
    -----
    widget = AnnotationWidget()
    assert isinstance(annotation, pyannote.core.Annotation)
    widget.annotation = annotation

    # reset widget
    del widget.annotation

    Traitlets
    ---------
    labels : str -> human-readable
    regions : list of {"start": float, "end": float, "id": str, "label": str}
    """

    labels = traitlets.Dict().tag(sync=True)
    regions = traitlets.List().tag(sync=True)

    def __init__(self, annotation: Optional[Annotation] = None):
        super().__init__()
        if annotation:
            self.annotation = annotation
    
    def _get_annotation(self):
        return get_annotation(self.regions, self.labels)

    def _set_annotation(self, annotation: Annotation):

        # rename tracks if they are not unique
        tracks = [track for _, track in annotation.itertracks()]
        if len(tracks) > len(set(tracks)):
            annotation = annotation.relabel_tracks()

        added_labels = set(annotation.labels()) - set(self.labels.values())
        if added_labels:
            new_labels = dict(self.labels)
            # index_pool = filterfalse(lambda i: i in self.labels, count(start=0))
            index_pool = string_generator(skip=list(self.labels))
            for label in added_labels:
                index = next(index_pool).lower()
                new_labels[index] = label
            self.labels = new_labels
        
        self.regions = [
            {
                "start": segment.start, 
                "end": segment.end, 
                "label": self.slebal[label],
                "id": track if track.startswith("wavesurfer_") else "frompython_" + "".join(random.choices(string.ascii_lowercase, k=11))
            } for segment, track, label in annotation.itertracks(yield_label=True)]

    def _del_annotation(self):
        self.regions = list()
        self.labels = dict()
    
    annotation = property(_get_annotation, _set_annotation, _del_annotation)

    @traitlets.observe("labels")
    def labels_has_changed(self, change: Dict):
        self.slebal = {label: idx for idx, label in change["new"].items()}

    @traitlets.observe("regions")
    def regions_has_changed(self, change: Dict):
        added_labels = set(region["label"] for region in change["new"]) - set(self.labels)
        if added_labels:
            new_labels = dict(self.labels)
            for label in added_labels:
                new_labels[label] = label
            self.labels = new_labels



