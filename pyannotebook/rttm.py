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

import csv
import random
import string
from pathlib import Path
from typing import Dict, Text, Union
from collections import defaultdict
from pyannote.core import Segment, Annotation

def load_rttm(rttm: Path, keep_type="SPEAKER") -> Dict[Text, Annotation]:
    """Load RTTM file

    Parameters
    ----------
    rttm : Path
        Path to RTTM file
    keep_type : {"SPEAKER"}, optional
        Only load lines of that type. Defaults to "SPEAKER".

    Returns
    -------
    annotations : dictionary of Annotation
        {file_id: pyannote.core.Annotation instance} dictionary
    """
    annotations = defaultdict(Annotation)
    letters = string.ascii_lowercase
    with open(rttm, "r") as rttm_file:
        rttm_reader = csv.reader(rttm_file, delimiter=' ')
        for l, line in enumerate(rttm_reader):
            main_type = line[0]
            if main_type != keep_type:
                continue
            file_id = line[1] 
            # channel = line[2] 
            time = float(line[3])
            duration = float(line[4]) 
            # orthography = line[5] 
            #sub_type = line[6] 
            speaker_name = line[7] 
            # confidence = line[8] 
            # slat = line[9]
            
            annotations[file_id].uri = file_id
            speech_turn = Segment(start=time, end=time+duration)
            track_id = "".join(random.choices(letters, k=20)) + f"_{l:06d}"
            annotations[file_id][speech_turn, track_id] = speaker_name

    return annotations

