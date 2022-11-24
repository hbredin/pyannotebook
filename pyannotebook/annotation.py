import ipywidgets
import traitlets
from typing import Dict, Optional, Union
from pyannote.core import Annotation, Segment
from itertools import filterfalse, count
import random
import string
from functools import partial

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
    widget.annotation = None

    Traitlets
    ---------
    labels : int -> human-readable
    regions : list of {"start": float, "end": float, "id": str, "label": int}
    """

    labels = traitlets.Dict().tag(sync=True)
    regions = traitlets.List().tag(sync=True)

    def __init__(self, annotation: Optional[Annotation] = None):
        super().__init__()
        self.annotation = annotation
    
    def _get_annotation(self):
        return get_annotation(self.regions, self.labels)

    annotation = property(_get_annotation)

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

    # def _set_annotation(self, annotation: Union[Annotation, None]):

    #     if annotation is None:
    #         annotation = Annotation()
    #         self.labels = dict()
        
    #     else:
    #         added_labels = set(annotation.labels()) - set(self.labels.values())
    #         if added_labels:
    #             new_labels = dict(self.labels)
    #             index_pool = filterfalse(lambda i: i in self.labels, count(start=1))
    #             for label in added_labels:
    #                 index = next(index_pool)
    #                 new_labels[index] = label
    #             self.labels = new_labels
        
    #     self.regions = [
    #         {
    #             "start": segment.start, 
    #             "end": segment.end, 
    #             "label": self.slebal[label],
    #             "id": "".join(random.choices(string.ascii_lowercase, k=20))
    #         } for segment, _, label in annotation.itertracks(yield_label=True)]
