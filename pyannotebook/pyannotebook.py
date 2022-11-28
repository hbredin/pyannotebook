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