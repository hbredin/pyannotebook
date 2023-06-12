from enum import auto
import ipywidgets
from math import ceil
from pyannotebook.pyannotebook import Pyannotebook
from typing import Optional,Dict
from pyannote.core import Segment
import traitlets

try:
    from pyannote.audio import Audio, Pipeline
    from pyannote.audio.core.io import AudioFile
    from pyannote.audio.pipelines.utils.hook import ProgressHook
    PYANNOTE_AUDIO_AVAILABLE = True
except ImportError:
    PYANNOTE_AUDIO_AVAILABLE = False

# liste des "segment_command" possibles
#    "none"
#    "next"
#    "previous"

class PyannoteWidget(ipywidgets.VBox):

    segment_command = traitlets.Unicode("none").tag(sync=True)


    def __init__(self, 
        audio: Optional["AudioFile"] = None, 
        pipeline: Optional["Pipeline"] = None,
        minimap: bool = True,
        auto_select: bool = False,
        # taille d'un segment audio qui sera traité en seconde
        segmentSize: float = 30.0,
        segment_overlap: float = 0.0,
    ):
        if(not PYANNOTE_AUDIO_AVAILABLE):
            raise ImportError("pyannote.audio is not available")
        
        if(segment_overlap >= segmentSize):
            raise ValueError("segment_overlap must be less than segmentSize")
        
        self.segmentSize = segmentSize
        self.segment_overlap = segment_overlap
        if audio is not None:
            self.audio = audio
            self._set_audio(self.audio)

        self._pyannoteBook = Pyannotebook(audio=None, minimap=minimap, auto_select=auto_select)
        super().__init__([self._pyannoteBook])

    def _set_audio(self, file: "AudioFile"):
        audio = Audio(mono=True)
        audio_lenght = audio.get_duration(file)
        self.nbSegment = int(ceil(audio_lenght/self.segmentSize)) # TODO correct for over lap
        print("Audio lenght:",audio_lenght)
        print("Number of segment:",self.nbSegment)

        self.audio_segment = []
        for i in range(self.nbSegment):
            segment_start = i*(self.segmentSize-self.segment_overlap)

            segment_end = segment_start+self.segmentSize
            if(segment_end > audio_lenght):
                segment_end = audio_lenght
            print("Segment",i,":",segment_start,"-",segment_end)
            new_segment = audio.crop(file,Segment(segment_start,segment_end))
            self.audio_segment.append({"waveform":new_segment[0],"sample_rate":new_segment[1]})

        print("Audio segment:",self.audio_segment)
        self._currentSegment = 0
        self._pyannoteBook.audio = self.audio_segment[self._currentSegment]
        
        if self.pipeline is None:
            return

        # use progress hook to provide feedback
        with ProgressHook() as hook:
            annotation = self.pipeline(file, hook=hook)
        self._pyannoteBook.annotation = annotation
    
    def _del_audio(self):
        del self._pyannoteBook.audio
        del self.audio

    audio = property(None, _set_audio, _del_audio)

    @traitlets.observe("segment_command")
    def segment_command_has_changed(self, change: Dict):
        
        if change["new"] == "next":
            print("next")
            if self._currentSegment < self.nbSegment:
                self._currentSegment += 1
                # TODO: get the next segment
                self._pyannoteBook.audio = self.audio_segment[self._currentSegment]
                
        elif change["new"] == "previous":
            print("previous")
            if self._currentSegment > 0:
                self._currentSegment -= 1
                # TODO: get the previous segment
                self._pyannoteBook.audio = self.audio_segment[self._currentSegment]
                
        self.segment_command = "none"
        raise Warning("segment_command_has_changed")