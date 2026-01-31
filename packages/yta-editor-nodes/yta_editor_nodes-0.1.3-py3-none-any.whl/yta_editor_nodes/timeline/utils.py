from yta_validation import PythonValidator
from typing import Union


VALID_EDITION_NODES = ['SerialTimelineNode', 'ParallelTimelineNode']
"""
The list of valid edition nodes as strings, to
compare easy to validate.
"""

def is_edition_node(
    node: Union['SerialTimelineNode', 'ParallelTimelineNode']
) -> bool:
    """
    Check if the provided `node` is an edition node, which
    has to be a SerialTimelineNode or a ParallelTimelineNode (by now).

    TODO: Update this in the future.
    """
    return PythonValidator.is_instance_of(node, VALID_EDITION_NODES)

def validate_is_edition_node(
    node: Union['SerialTimelineNode', 'ParallelTimelineNode']
) -> None:
    """
    Check if the provided `node` is an edition node, which
    has to be a `SerialTimelineNode` or a `ParallelTimelineNode` (by now), or
    raise an exception if not.
    """
    if not is_edition_node(node):
        raise Exception('The "node" provided is not an edition node.')