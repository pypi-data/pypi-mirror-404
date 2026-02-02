"""
The nodes that are able to make simple processing.
"""
from yta_editor_nodes.processor.black_and_white import BlackAndWhiteNodeProcessor
from yta_editor_nodes.processor.brightness import BrightnessNodeProcessor
from yta_editor_nodes.processor.color_contrast import ColorContrastNodeProcessor
from yta_editor_nodes.processor.selection_mask import SelectionMaskNodeProcessor


__all__ = [
    'BlackAndWhiteNodeProcessor',
    'BrightnessNodeProcessor',
    'ColorContrastNodeProcessor',
    'SelectionMaskNodeProcessor'
]