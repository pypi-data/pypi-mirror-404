from yta_editor_nodes.timeline.parallel.abstract import _ParallelTimelineNodeAbstract
from yta_editor_utils.texture import TextureUtils
from typing import Union

import numpy as np


class ParallelTimelineNode(_ParallelTimelineNodeAbstract):
    """
    A node that is a composition of different nodes
    that are executed in parallel to obtain different
    outputs that are combined into a single one by using
    the MixBlender.
    """

    def _combine_outputs(
        self,
        outputs: list[Union['np.ndarray', 'moderngl.Texture']]
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Combine the different `outputs` into a single one.
        """
        

        # TODO: What about with OpenGL? I found this,
        # but you have a maximum of textures you can
        # so you have to customize the code
        """
        #version 330

        in vec2 v_uv;
        out vec4 output_color;

        uniform sampler2D textures[8];   // max 8 parallel textures
        uniform int number_of_textures;       // how many to use

        void main() {
            vec4 color = vec4(0.0);
            for (int i = 0; i < number_of_textures; ++i)
                color += texture(textures[i], v_uv);

            output_color = color / float(number_of_textures);
        }
        """

        acc = np.zeros_like(outputs[0], dtype = np.float32)

        for output in outputs:
            acc += output

        acc = np.clip(acc, 0.0, 1.0)
        
        return TextureUtils.numpy_to_uint8(acc)

        # Old code below (apparently wrong)
        # TODO: Use the MixBlender, fix it if working not
        results = [
            TextureUtils.numpy_to_float32(output)
            for output in outputs
        ]
        stacked = np.stack(results, axis = 0)  # (N, H, W, C)
        avg = np.mean(stacked, axis = 0)

        return TextureUtils.numpy_to_uint8(avg)

        # TODO: This must be according to the type
        from yta_editor_nodes.blender import MixBlender

        blender = MixBlender(
            do_use_gpu = True
        )

        result = outputs[0]

        """
        TODO: This is not working properly as it is not
        in parallel, if we apply a 0.2, we will keep the
        80% of the base and 20% of the 2nd output, but in
        the next step we will do it again so we will have
        80% of 80% (64%) of the base, and 80% of 20% (16%)
        of the 2nd output, and this is not what we want
        """
        mix_weight = 1.0 / len(outputs)
        for output in outputs[1:]:
            result = blender.blend(
                base_input = result,
                overlay_input = output,
                #mix_weight = 0.5
                mix_weight = mix_weight
            )

        return result
    
"""
This above is the a basic class using the MixBlender
to combine the outputs. We can create more, but by
now is ok.
"""