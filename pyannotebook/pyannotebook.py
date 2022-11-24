


from typing import Optional
from pathlib import Path
from pyannote.core import Annotation
from .annotation import AnnotationWidget
from .labels import LabelsWidget
from .wavesurfer import WavesurferWidget

import ipywidgets

class Pyannotebook(ipywidgets.VBox):

    def __init__(self, audio: Path, init: Optional[Annotation] = None):

        w = WavesurferWidget(audio)
        a = AnnotationWidget(init)
        l = LabelsWidget()
        super().__init__([w, a, l])
        ipywidgets.link((l, 'labels'), (a, 'labels'))
        ipywidgets.link((l, 'labels'), (w, 'labels'))
        ipywidgets.link((a, 'regions'), (w, 'regions'))
        ipywidgets.link((l, 'active_label'), (w, 'active_label'))
        ipywidgets.link((l, 'colors'), (w, 'colors'))
