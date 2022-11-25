import ipywidgets

from .wavesurfer import WavesurferWidget
from .annotation import AnnotationWidget
from .labels import LabelsWidget

from typing import Optional
from pathlib import Path
from pyannote.core import Annotation


class Pyannotebook(ipywidgets.VBox):

    def __init__(self, audio: Path, init: Optional[Annotation] = None):

        self._wavesurfer = WavesurferWidget(audio)
        self._annotation = AnnotationWidget()
        self._labels = LabelsWidget()
        super().__init__([self._wavesurfer, self._labels])
        ipywidgets.link((self._labels, 'labels'), (self._annotation, 'labels'))
        ipywidgets.link((self._labels, 'labels'), (self._wavesurfer, 'labels'))
        ipywidgets.link((self._annotation, 'regions'), (self._wavesurfer, 'regions'))
        ipywidgets.link((self._labels, 'active_label'), (self._wavesurfer, 'active_label'))
        ipywidgets.link((self._labels, 'colors'), (self._wavesurfer, 'colors'))
        if init:
            self._annotation.annotation = init
    
    def _get_annotation(self) -> Annotation:
        return self._annotation.annotation
    
    def _set_annotation(self, annotation: Annotation):
        self._annotation.annotation = annotation
    
    def _del_annotation(self):
        del self._annotation.annotation

    annotation = property(_get_annotation, _set_annotation, _del_annotation)