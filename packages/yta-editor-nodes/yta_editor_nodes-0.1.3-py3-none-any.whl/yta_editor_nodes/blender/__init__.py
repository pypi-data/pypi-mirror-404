"""
The blenders, capable of mixing different inputs into
a single one by using different parameters and 
techniques.

All the classes here will have an instance of the
specific CPU and/or GPU class that is able to run the
code by using either CPU or GPU. The user can choose
between GPU and CPU and that option will be considered
(only if available).
"""
from yta_editor_nodes.blender.mix import MixBlender
from yta_editor_nodes.blender.alpha import AlphaBlender
from yta_editor_nodes.blender.add import AddBlender


__all__ = [
    'MixBlender',
    'AlphaBlender',
    'AddBlender'
]

"""
Note for the developer:

I leave this old way to instantiate dynamically
but less refactored, just in case. Please, remove
in the next commits if the new version is already
working.

TODO: Old way to import dynamically
blender_cpu = None
if is_cpu_available():
    from yta_editor_nodes_cpu.blender.add import AddBlenderCPU

    blender_cpu = AddBlenderCPU()

blender_gpu = None
if is_gpu_available():
    from yta_editor_nodes_gpu.blender import AddBlenderGPU

    blender_gpu = AddBlenderGPU(
        opengl_context = None,
        # TODO: Do not hardcode please...
        output_size = (1920, 1080),
    )
"""