"""
The transitions module, with all the classes that
are able to process transitions by using CPU, GPU
or both.

All the classes here will have an instance of the
specific CPU and/or GPU class that is able to run
the code by using either CPU or GPU. The user can
choose between GPU and CPU and that option will be
considered (only if available).

Note for the developer:
A class must have, at least, one specific 
processor (GPU is prefered).

TODO: This module doesn't use 't' but 'progress'
so it is not a child of 'processor.video', maybe
we should move it to be 'processor.transitions'
instead of 'processor.video.transitions'... (?)
"""
from yta_editor_nodes.processor.video.transitions.alphapedia_mask import AlphaPediaMaskTransitionProcessor
from yta_editor_nodes.processor.video.transitions.bars_falling import BarsFallingTransitionProcessor
from yta_editor_nodes.processor.video.transitions.circle_closing import CircleClosingTransitionProcessor
from yta_editor_nodes.processor.video.transitions.circle_opening import CircleOpeningTransitionProcessor
from yta_editor_nodes.processor.video.transitions.crossfade import CrossfadeTransitionProcessor
from yta_editor_nodes.processor.video.transitions.distorted_crossfade import DistortedCrossfadeTransitionProcessor
from yta_editor_nodes.processor.video.transitions.slide import SlideTransitionProcessor


__all__ = [
    'AlphaPediaMaskTransitionProcessor',
    'BarsFallingTransitionProcessor',
    'CircleClosingTransitionProcessor',
    'CircleOpeningTransitionProcessor',
    'CrossfadeTransitionProcessor',
    'DistortedCrossfadeTransitionProcessor',
    'SlideTransitionProcessor'
]