import ipywidgets
import traitlets
from typing import Optional, Union
from pyannote.core import Annotation
from itertools import filterfalse, count


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
    """

    labels = traitlets.Dict().tag(sync=True)

    def __init__(self, annotation: Optional[Annotation] = None):
        super().__init__()
        self.annotation = annotation
            
    def get_annotation(self):
        return self._annotation

    def set_annotation(self, annotation: Union[Annotation, None]):

        if annotation is None:
            self._annotation = Annotation()
            self.labels = dict()
        
        else:
            added_labels = set(annotation.labels()) - set(self.labels.values())
            print(f"{added_labels=}")
            if added_labels:
                new_labels = dict(self.labels)
                index_pool = filterfalse(lambda i: i in self.labels, count(start=1))
                for label in added_labels:
                    index = next(index_pool)
                    new_labels[index] = label
                self.labels = new_labels
            self._annotation = annotation

    annotation = property(get_annotation, set_annotation)

