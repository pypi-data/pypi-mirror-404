"""
TODO: Maybe this is not the place to be in.
"""
from yta_validation.parameter import ParameterValidator
from yta_validation import PythonValidator
from typing import Union


class _TimedNode:
    """
    *For internal use only*

    Class to represent a Node wrapper to
    be able to specify the time range in
    which we want the node to be applied.

    If the 't' time moment is not inside
    this range, the frame will be returned
    as it is, with no change.

    A 't' time moment inside the range has
    this condition:
    - `start <= t < end`

    We are not including the end because
    the next TimedNode could start on that
    specific value, and remember that the
    first time moment is 0.

    This is the class that has to be applied
    when working with videos and not a Node
    directly.

    The 'start' and 'end' values by default
    are 0 and the end of the media to which
    we will apply the modification (that is
    defined here by None).
    """

    @property
    def copy(
        self
    ) -> '_TimedNode':
        """
        Get a copy of this instance.
        """
        return self.__class__(
            node = self.node,
            start = self.start,
            end = self.end
        )

    @property
    def is_audio_node(
        self
    ) -> bool:
        """
        Flag to indicate if the node (or effect)
        is an audio effect or not.
        """
        # TODO: Is this checking not only the
        # first level (?)
        return PythonValidator.is_subclass_of(self.node, '_AudioNodeProcessor')
    
    @property
    def is_video_node(
        self
    ) -> bool:
        """
        Flag to indicate if the node (or effect)
        is a video effect or not.
        """
        # TODO: Is this checking not only the
        # first level (?)
        return PythonValidator.is_subclass_of(self.node, '_VideoNodeProcessor')

    def __init__(
        self,
        node: Union['_VideoNodeProcessor', '_AudioNodeProcessor'],
        start: Union[int, float, 'Fraction'] = 0.0,
        end: Union[int, float, 'Fraction', None] = None
    ):
        ParameterValidator.validate_mandatory_positive_number('start', start, do_include_zero = True)
        ParameterValidator.validate_positive_number('end', end, do_include_zero = False)

        if (
            end is not None and
            end < start
        ):
            raise Exception('The "end" parameter provided must be greater or equal to the "start" parameter.')

        self.node: Union['_VideoNodeProcessor', '_AudioNodeProcessor'] = node
        """
        The node we are wrapping and we want to
        apply as a modification of the frame in
        which we are in a 't' time moment.
        """
        self.start: float = start
        """
        The 't' time moment in which the Node must
        start being applied (including it).
        """
        # TODO: The 'end' we receive here could be
        # greater than the actual end of the media
        # in which the TimedNode will be applied,
        # but it seems to be working correctly as
        # we will never receive a 't' from that
        # media that is out of its own bounds...
        self.end: Union[float, None] = end
        """
        The 't' time moment in which the Node must
        stop being applied (excluding it).
        """

    def _get_t(
        self,
        t: Union[int, float, 'Fraction']
    ) -> float:
        """
        Obtain the 't' time moment relative to the
        effect duration.

        Imagine `start=3` and `end=5`, and we receive 
        a `t=4`. It is inside the range, so we have
        to apply the effect, but as the effect
        lasts from second 3 to second 5 (`duration=2`),
        the `t=4` is actually a `t=1` for the effect
        because it is the time elapsed since the
        effect started being applied, that was on the 
        second 3.

        The formula:
        - `t - self.start`
        """
        return t - self.start

    def is_within_time(
        self,
        t: float
    ) -> bool:
        """
        Flag to indicate if the 't' time moment provided
        is in the range of this TimedNode instance, 
        which means between the 'start' and the 'end'.

        The formula:
        - `start <= t < end`
        """
        return (
            self.start <= t < self.end
            if self.end is not None else
            self.start <= t
        )

    def process(
        self,
        frame: Union['moderngl.Texture', 'np.ndarray'],
        t: float
        # TODO: Maybe we need 'fps' and 'number_of_frames'
        # to calculate progressions or similar...
    ) -> Union['moderngl.Texture', 'np.ndarray']:
        """
        Process the frame if the provided 't' time
        moment is in the range of this TimedNode
        instance.
        """
        return (
            self.node.process(frame, self._get_t(t))
            if self.is_within_time(t) else
            frame
        )
    
class TimedVideoNode(_TimedNode):
    """
    Class to represent a video node wrapper
    to be able to specify the time range in
    which we want the node to be applied.

    If the 't' time moment is not inside
    this range, the frame will be returned
    as it is, with no change.

    A 't' time moment inside the range has
    this condition:
    - `start <= t < end`

    We are not including the end because
    the next TimedNode could start on that
    specific value, and remember that the
    first time moment is 0.

    This is the class that has to be applied
    when working with videos and not a Node
    directly.

    The 'start' and 'end' values by default
    are 0 and the end of the media to which
    we will apply the modification (that is
    defined here by None).
    """

    def __init__(
        self,
        node: '_VideoNodeProcessor',
        start: Union[int, float, 'Fraction'] = 0.0,
        end: Union[int, float, 'Fraction', None] = None
    ):
        # TODO: Is this working (?)
        ParameterValidator.validate_mandatory_subclass_of('node', node, '_VideoNodeProcessor')

        super().__init__(
            node = node,
            start = start,
            end = end
        )

class TimedAudioNode(_TimedNode):
    """
    Class to represent an audio node wrapper
    to be able to specify the time range in
    which we want the node to be applied.

    If the 't' time moment is not inside
    this range, the frame will be returned
    as it is, with no change.

    A 't' time moment inside the range has
    this condition:
    - `start <= t < end`

    We are not including the end because
    the next TimedNode could start on that
    specific value, and remember that the
    first time moment is 0.

    This is the class that has to be applied
    when working with videos and not a Node
    directly.

    The 'start' and 'end' values by default
    are 0 and the end of the media to which
    we will apply the modification (that is
    defined here by None).
    """

    def __init__(
        self,
        node: '_AudioNodeProcessor',
        start: Union[int, float, 'Fraction'] = 0.0,
        end: Union[int, float, 'Fraction', None] = None
    ):
        # TODO: Is this working (?)
        ParameterValidator.validate_mandatory_subclass_of('node', node, '_AudioNodeProcessor')

        super().__init__(
            node = node,
            start = start,
            end = end
        )