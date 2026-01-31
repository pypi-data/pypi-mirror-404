"""
Old way of creating and handling effects. Now it
is done with the new node classes, so this whole
module is @deprecated and must be removed soon.
"""
# from yta_video_opengl.nodes.video import BreathingFrameVideoNodeProcessor, WavingFramesVideoNodeProcessor
# from yta_video_opengl.context import OpenGLContext
# from yta_video_opengl.nodes.audio import ChorusAudioNodeProcessor, VolumeAudioNodeProcessor
# from yta_video_opengl.nodes.timed import TimedVideoNode, TimedAudioNode
# from yta_video_opengl.utils import texture_to_frame
# from yta_validation.parameter import ParameterValidator
# from yta_validation import PythonValidator
# from yta_programming.singleton import SingletonMeta
# from typing import Union
# from abc import abstractmethod

# import moderngl


# class _AudioEffects:
#     """
#     *For internal use only*

#     The audio effects that will be available
#     throught our internal _Effects class to
#     wrap and make available all the audio
#     effects we want to be available.
#     """

#     def __init__(
#         self,
#         effects: 'Effects'
#     ):
#         self._effects: Effects = effects
#         """
#         The parent instance that includes this
#         class instance as a property.
#         """

#     """
#     Here below we expose all the effects
#     we want the users to have available to
#     be used.
#     """
#     def chorus(
#         self,
#         sample_rate: int,
#         depth: int = 0,
#         frequency: float = 0.25,
#         start: Union[int, float, 'Fraction'] = 0,
#         end: Union[int, float, 'Fraction', None] = None
#     ) -> TimedAudioNode:
#         return _create_timed_node(
#             ChorusAudioNodeProcessor(
#                 sample_rate = sample_rate,
#                 depth = depth,
#                 frequency = frequency
#             ),
#             start = start,
#             end = end
#         )

#     def volume(
#         self,
#         factor: callable,
#         start: Union[int, float, 'Fraction'] = 0,
#         end: Union[int, float, 'Fraction', None] = None
#     ) -> TimedAudioNode:
#         return _create_timed_node(
#             VolumeAudioNodeProcessor(
#                 factor_fn = factor
#             ),
#             start = start,
#             end = end
#         )
    
#     # TODO: Include definitive and tested audio
#     # effects here below

# class _VideoEffects:
#     """
#     *For internal use only*

#     The video effects that will be available
#     throught our internal _Effects class to
#     wrap and make available all the video
#     effects we want to be available.
#     """

#     def __init__(
#         self,
#         effects: 'Effects'
#     ):
#         self._effects: Effects = effects
#         """
#         The parent instance that includes this
#         class instance as a property.
#         """

#     """
#     Here below we expose all the effects
#     we want the users to have available to
#     be used.
#     """
#     def waving_node(
#         self,
#         # TODO: Maybe 'frame_size' (?)
#         size: tuple[int, int],
#         amplitude: float = 0.05,
#         frequency: float = 10.0,
#         speed: float = 2.0,
#         start: Union[int, float, 'Fraction'] = 0.0,
#         end: Union[int, float, 'Fraction', None] = None
#     ) -> TimedVideoNode:
#         """
#         TODO: Explain this effect better.

#         The 'start' and 'end' time moments are the
#         limits of the time range in which the effect
#         has to be applied to the frames inside that
#         time range. Providing start=0 and end=None
#         will make the effect to be applied to any
#         frame.
#         """
#         return _create_timed_node(
#             WavingFramesVideoNodeProcessor(
#                 # TODO: Maybe make this a parameter (?)
#                 do_use_gpu = True,
#                 amplitude = amplitude,
#                 frequency = frequency,
#                 speed = speed
#             ),
#             start = start,
#             end = end
#         )
    
#     def breathing_node(
#         self,
#         # TODO: Handle this
#         output_size: tuple[int, int],
#         zoom: float = 0.05,
#         start: Union[int, float, 'Fraction'] = 0.0,
#         end: Union[int, float, 'Fraction', None] = None
#     ) -> TimedVideoNode:
#         """
#         TODO: Explain this effect better.

#         The 'start' and 'end' time moments are the
#         limits of the time range in which the effect
#         has to be applied to the frames inside that
#         time range. Providing start=0 and end=None
#         will make the effect to be applied to any
#         frame.
#         """
#         return _create_timed_node(
#             BreathingFrameVideoNodeProcessor(
#                 # TODO: Maybe make this a parameter (?)
#                 do_use_gpu = True,
#                 zoom = zoom
#             ),
#             start = start,
#             end = end
#         )
    
#     # TODO: Include definitive and tested video
#     # effects here below

# class Effects(metaclass = SingletonMeta):
#     """
#     *Singleton class*

#     It is a singleton instance to have a
#     unique context for all the instances
#     that need it and instantiate this
#     class to obtain it. Here we group all
#     the nodes we have available for the
#     user.

#     This class is to simplify the access to
#     the effect nodes and also to have the
#     single context always available.

#     Even though we can have more effects,
#     this class is also the way we expose only
#     the ones we actually want to expose to 
#     the user.

#     The GPU will make the calculations in
#     parallel by itself, so we can handle a
#     single context to make the nodes share
#     textures and buffers.
#     """

#     def __init__(
#         self,
#         opengl_context: Union[moderngl.Context, None] = None
#     ):
#         """
#         If you provide an OpenGL context, it will be
#         used, or a new one will be created if the
#         'opengl_context' parameter is None.
#         """
#         ParameterValidator.validate_instance_of('opengl_context', opengl_context, moderngl.Context)

#         self.opengl_context = (
#             OpenGLContext().context
#             if opengl_context is None else
#             opengl_context
#         )
#         """
#         The opengl context that will be shared
#         by all the opengl nodes.
#         """
#         self.audio: _AudioEffects = _AudioEffects(self)
#         """
#         Shortcut to the audio effects that are
#         available.
#         """
#         self.video: _VideoEffects = _VideoEffects(self)
#         """
#         Shortcut to the video effects that are
#         available.
#         """

# def _create_timed_node(
#     node: Union['_AudioNodeProcessor', '_VideoNodeProcessor'],
#     start: Union[int, float, 'Fraction'],
#     end: Union[int, float, 'Fraction', None]
# ) -> Union[TimedVideoNode, TimedAudioNode]:
#     """
#     *For internal use only*

#     Create a TimedNode with the provided 'node' and
#     the 'start' and 'end' time moments.
#     """
#     # We could be other classes in the middle,
#     # because an OpenglNode inherits from
#     # other class
#     ParameterValidator.validate_mandatory_subclass_of('node', node, ['_AudioNodeProcessor', '_VideoNodeProcessor', '_OpenGLBase'])

#     timed_node_class = (
#         TimedAudioNode
#         if PythonValidator.is_subclass_of(node, '_AudioNodeProcessor') else
#         TimedVideoNode
#     )

#     # We have to create a node wrapper with the
#     # time range in which it has to be applied
#     # to all the frames
#     return timed_node_class(
#         node = node,
#         start = start,
#         end = end
#     )

# class _EffectStacked:
#     """
#     *For internal use only*

#     Class to wrap an effect that will be
#     stacked with an specific priority.

#     Priority is higher when lower value,
#     and lower when higher value.
#     """

#     @property
#     def is_audio_effect(
#         self
#     ) -> bool:
#         """
#         Flag to indicate if it is an audio effect
#         or not.
#         """
#         return self.effect.is_audio_node

#     @property
#     def is_video_effect(
#         self
#     ) -> bool:
#         """
#         Flag to indicate if it is a video effect
#         or not.
#         """
#         return self.effect.is_video_node

#     def __init__(
#         self,
#         effect: Union[TimedVideoNode, TimedAudioNode],
#         priority: int
#     ):
#         self.effect: Union[TimedVideoNode, TimedAudioNode] = effect
#         """
#         The effect to be applied.
#         """
#         self.priority: int = priority
#         """
#         The priority this stacked frame has versus
#         the other stacked effects.
#         """

# class _VideoEffectStacked(_EffectStacked):
#     """
#     *For internal use only*

#     Class to wrap a video effect that will
#     be stacked with a specific priority.

#     Priority is higher when lower value,
#     and lower when higher value.
#     """

#     def __init__(
#         self,
#         effect: TimedVideoNode,
#         priority: int
#     ):
#         ParameterValidator.validate_mandatory_instance_of('effect', effect, TimedVideoNode)

#         super().__init__(
#             effect = effect,
#             priority = priority
#         )

# class _AudioEffectStacked(_EffectStacked):
#     """
#     *For internal use only*

#     Class to wrap an audio effect that will
#     be stacked with a specific priority.

#     Priority is higher when lower value,
#     and lower when higher value.
#     """

#     def __init__(
#         self,
#         effect: TimedAudioNode,
#         priority: int
#     ):
#         ParameterValidator.validate_mandatory_instance_of('effect', effect, TimedAudioNode)
        
#         super().__init__(
#             effect = effect,
#             priority = priority
#         )

# # TODO: Move to another py file (?)
# class _EffectsStack:
#     """
#     *For internal use only*

#     *This class is to be inherited by the
#     specific video and audio classes.

#     Class to include a collection of effects
#     we want to apply in some entity, that 
#     will make easier applying them.

#     You can use this stack to keep the effects
#     you want to apply on a Media or on the
#     Timeline of your video editor.
#     """

#     @property
#     def copy(
#         self
#     ) -> '_EffectsStack':
#         """
#         Get a copy of this instance.
#         """
#         effects_stack = self.__class__()

#         for effect_sttacked in self._effects:
#             effects_stack.add_effect(
#                 effect = effect_sttacked.effect.copy,
#                 priority = effect_sttacked.priority
#             )

#         return effects_stack
    
#     @property
#     def number_of_effects(
#         self
#     ) -> int:
#         """
#         The number of effects that are stacked.
#         """
#         return len(self._effects)

#     @property
#     def effects(
#         self
#     ) -> list[_EffectStacked]:
#         """
#         The effects but ordered by 'priority' and
#         'start' time moment.
#         """
#         return sorted(
#             [
#                 effect
#                 for effect in self._effects
#             ],
#             key = lambda effect: (effect.priority, effect.effect.start)
#         )
    
#     @property
#     def lowest_priority(
#         self
#     ) -> int:
#         """
#         The priority of the effect with the lowest
#         one, or 0 if no video effects.
#         """
#         return min(
#             (
#                 effect.priority
#                 for effect in self.effects
#             ),
#             default = 0
#         )
    
#     def __init__(
#         self
#     ):
#         self._effects: list[Union[_AudioEffectStacked, _VideoEffectStacked]] = []
#         """
#         A list containing all the effects that
#         have been added to this stack, unordered.
#         """

#     def get_effects_at(
#         self,
#         t: Union[int, float, 'Fraction']
#     ) -> list[Union[TimedVideoNode, TimedAudioNode]]:
#         """
#         Get the effects, ordered by priority and the
#         'start' field, that must be applied within the
#         't' time moment provided because they are in
#         the [start, end) time range.
#         """
#         return [
#             effect.effect
#             for effect in self.effects
#             if effect.effect.is_within_time(t)
#         ]

#     def add_effect(
#         self,
#         effect: Union[TimedVideoNode, TimedAudioNode],
#         priority: Union[int, None] = None
#     ) -> 'EffectsStack':
#         """
#         Add the provided 'effect' to the stack with
#         the also given 'priority'.
#         """
#         ParameterValidator.validate_mandatory_instance_of('effect', effect, [TimedVideoNode, TimedAudioNode])
#         ParameterValidator.validate_positive_int('priority', priority, do_include_zero = True)

#         # TODO: What about the same effect added
#         # twice during the same time range? Can we
#         # allow it? It will be applied twice for
#         # specific 't' time moments but with 
#         # different attributes. is it ok (?)

#         # TODO: What if priority is already taken?
#         # Should we let some effects have the same
#         # priority (?)
#         priority = (
#             self.lowest_priority + 1
#             if priority is None else
#             priority
#         )

#         self._effects.append(_EffectStacked(
#             effect = effect,
#             priority = priority
#         ))

#         return self
    
#     # TODO: Create 'remove_effect'
    
#     @abstractmethod
#     def apply_effects_at(
#         self,
#         frame: Union['np.ndarray', moderngl.Texture],
#         t: Union[int, float, 'Fraction']
#     ) -> Union['np.ndarray', moderngl.Texture]:
#         """
#         Apply all the effects that must be applied
#         for the given `t` time moment to the also
#         provided `frame` (that must be the video or
#         audio frame of that time moment).
#         """
#         pass
    
# class VideoEffectsStack(_EffectsStack):
#     """
#     Class to include a collection of video effects
#     we want to apply in some entity, that will
#     make easier applying and organizing them.

#     You can use this stack to keep the video effects
#     you want to apply on a Media or on the Timeline
#     of your editor.
#     """

#     def add_effect(
#         self,
#         effect: TimedVideoNode,
#         priority: Union[int, None] = None
#     ) -> 'VideoEffectsStack':
#         """
#         Add the provided video 'effect' to the stack
#         with the also given 'priority'.
#         """
#         ParameterValidator.validate_mandatory_instance_of('effect', effect, TimedVideoNode)

#         return super().add_effect(
#             effect = effect,
#             priority = priority
#         )
    
#     def apply_effects_at(
#         self,
#         frame: Union['np.ndarray', moderngl.Texture],
#         t: Union[int, float, 'Fraction']
#     ) -> Union['np.ndarray', moderngl.Texture]:
#         """
#         Apply all the effects that must be applied
#         for the given `t` time moment to the also
#         provided `frame` (that must be the video
#         frame of that time moment).
#         """
#         for effect in self.get_effects_at(t):
#             frame = effect.process(frame, t)

#         # TODO: Check when the frame comes as a
#         # Texture and when as a numpy array. I
#         # think when we apply an opengl node it
#         # is a texture, but we need to return it
#         # as a numpy, always
#         return (
#             texture_to_frame(frame)
#             if PythonValidator.is_instance_of(frame, moderngl.Texture) else
#             frame
#         )
    
# class AudioEffectsStack(_EffectsStack):
#     """
#     Class to include a collection of audio effects
#     we want to apply in some entity, that will
#     make easier applying and organizing them.

#     You can use this stack to keep the audio effects
#     you want to apply on a Media or on the Timeline
#     of your editor.
#     """

#     def add_effect(
#         self,
#         effect: TimedAudioNode,
#         priority: Union[int, None] = None
#     ) -> 'VideoEffectsStack':
#         """
#         Add the provided audio 'effect' to the stack
#         with the also given 'priority'.
#         """
#         ParameterValidator.validate_mandatory_instance_of('effect', effect, TimedAudioNode)

#         return super().add_effect(
#             effect = effect,
#             priority = priority
#         )

#     def apply_effects_at(
#         self,
#         frame: Union['np.ndarray', moderngl.Texture],
#         t: Union[int, float, 'Fraction']
#     ) -> Union['np.ndarray', moderngl.Texture]:
#         """
#         Apply all the effects that must be applied
#         for the given `t` time moment to the also
#         provided `frame` (that must be the audio
#         frame of that time moment).
#         """
#         for effect in self.get_effects_at(t):
#             frame = effect.process(frame, t)

#         # Frame can only by a numpy array here
#         return frame