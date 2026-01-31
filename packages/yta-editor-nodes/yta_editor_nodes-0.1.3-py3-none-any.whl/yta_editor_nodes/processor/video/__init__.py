"""
Nodes that modify inputs to obtain outputs but
depending on a 't' time moment to adjust it to the
time of the video in which the input (a frame of a
video) is being edited. A movement effect is not 
edited the same when we are at the begining of the
video effect than when we are at the end.
"""
from yta_editor_nodes.processor.video.breathing_frame import BreathingFrameVideoNodeProcessor
from yta_editor_nodes.processor.video.waving_frame import WavingFrameVideoNodeProcessor


__all__ = [
    'BreathingFrameVideoNodeProcessor',
    'WavingFrameVideoNodeProcessor'
]