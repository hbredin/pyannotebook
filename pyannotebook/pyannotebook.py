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
from .controlBar import ControlBarWidget

from typing import Optional
from pyannote.core import Annotation

try:
    from pyannote.audio import Audio, Pipeline
    from pyannote.audio.core.io import AudioFile
    from pyannote.audio.pipelines.utils.hook import ProgressHook
    PYANNOTE_AUDIO_AVAILABLE = True
except ImportError:
    PYANNOTE_AUDIO_AVAILABLE = False


class Pyannotebook(ipywidgets.VBox):
    """Notebook widget for audio annotation
    
    Parameters
    ----------
    audio : pyannote.audio.core.io.AudioFile, optional
        Load provided audio file (using any pyannote.audio-compliant format).
        Defaults to not load any audio.
    pipeline : pyannote.audio.Pipeline, optional
        Use pretrained pipeline for pre-annotation. 
        Defaults to start annotating from scratch.
    minimap : bool, optional
        Display a minimap on top of waveform. Defaults to True.
    auto_select : bool, optional
        Automatically select region corresponding to current time.
        Defaults to False.
    
    See also
    --------
    pyannote.audio.core.io.AudioFile
    """

    def __init__(
        self, 
        audio: Optional["AudioFile"] = None, 
        pipeline: Optional["Pipeline"] = None,
        minimap: bool = True,
        auto_select: bool = False,
    ):

        self.minimap = minimap
        self.auto_select = auto_select

        self._wavesurfer = WavesurferWidget(minimap=self.minimap, auto_select=self.auto_select)
        self._annotation = AnnotationWidget()
        self._labels = LabelsWidget()
        self._control_bar = ControlBarWidget()
        super().__init__([self._wavesurfer, self._labels,self._control_bar])
        ipywidgets.link((self._labels, 'labels'), (self._annotation, 'labels'))
        ipywidgets.link((self._labels, 'labels'), (self._wavesurfer, 'labels'))
        ipywidgets.link((self._annotation, 'regions'), (self._wavesurfer, 'regions'))
        ipywidgets.link((self._labels, 'active_label'), (self._wavesurfer, 'active_label'))
        ipywidgets.link((self._labels, 'colors'), (self._wavesurfer, 'colors'))

        ipywidgets.link((self._wavesurfer, 'playing'), (self._control_bar, 'playing'))
        
        self.pipeline = pipeline
        if audio is not None:
            self.audio = audio
                
    def _get_annotation(self) -> Annotation:
        return self._annotation.annotation
    
    def _set_annotation(self, annotation: Annotation):
        self._annotation.annotation = annotation
    
    def _del_annotation(self):
        del self._annotation.annotation

    annotation = property(_get_annotation, _set_annotation, _del_annotation)

    def _set_audio(self, file: "AudioFile"):

        if PYANNOTE_AUDIO_AVAILABLE:
            audio = Audio(mono=True)
            file = audio.validate_file(file)
            file["waveform"], file["sample_rate"] = audio(file)
            self._wavesurfer.audio = (file["waveform"].numpy().squeeze(), file["sample_rate"])
        else:
            self._wavesurfer.audio = file

        if self.pipeline is None:
            return

        # use progress hook to provide feedback
        with ProgressHook() as hook:
            annotation = self.pipeline(file, hook=hook)
        self.annotation = annotation

    def _del_audio(self):
        del self._wavesurfer.audio

    audio = property(None, _set_audio, _del_audio)