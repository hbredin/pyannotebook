#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Hervé Bredin.
# Distributed under the terms of the Modified BSD License.

import ipywidgets

from .wavesurfer import WavesurferWidget
from .annotation import AnnotationWidget
from .labels import LabelsWidget
from .rttm import load_rttm

from typing import Optional
from pathlib import Path
from pyannote.core import Annotation

from ._version import __version__, version_info




def _jupyter_labextension_paths():
    """Called by Jupyter Lab Server to detect if it is a valid labextension and
    to install the widget
    Returns
    =======
    src: Source directory name to copy files from. Webpack outputs generated files
        into this directory and Jupyter Lab copies from this directory during
        widget installation
    dest: Destination directory name to install widget files to. Jupyter Lab copies
        from `src` directory into <jupyter path>/labextensions/<dest> directory
        during widget installation
    """
    return [{
        'src': 'labextension',
        'dest': 'pyannotebook',
    }]


def _jupyter_nbextension_paths():
    """Called by Jupyter Notebook Server to detect if it is a valid nbextension and
    to install the widget
    Returns
    =======
    section: The section of the Jupyter Notebook Server to change.
        Must be 'notebook' for widget extensions
    src: Source directory name to copy files from. Webpack outputs generated files
        into this directory and Jupyter Notebook copies from this directory during
        widget installation
    dest: Destination directory name to install widget files to. Jupyter Notebook copies
        from `src` directory into <jupyter path>/nbextensions/<dest> directory
        during widget installation
    require: Path to importable AMD Javascript module inside the
        <jupyter path>/nbextensions/<dest> directory
    """
    return [{
        'section': 'notebook',
        'src': 'nbextension',
        'dest': 'pyannotebook',
        'require': 'pyannotebook/extension'
    }]

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
