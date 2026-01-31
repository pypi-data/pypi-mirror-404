from yta_editor_nodes.timeline.parameter.abstract import ParameterSource
from yta_editor_nodes.timeline.parameter.source.constant import ConstantValue
from yta_validation import PythonValidator


def normalize_parameter_sources(
    parameters_sources: dict
) -> dict[str, 'ParameterSource']:
    """
    Transform the values received in the `parameters_sources`
    to `ConstantValues` if needed and return the new `dict`.
    """
    normalized_parameters_sources = {}

    for name, value in parameters_sources.items():
        if PythonValidator.is_instance_of(value, ParameterSource):
            normalized_parameters_sources[name] = value
            continue

        if (
            PythonValidator.is_basic_non_iterable_type(value) or
            value is None
        ):
            normalized_parameters_sources[name] = ConstantValue(value)
            continue
        
        raise Exception(f'The "{name}" parameter is not a ParameterSource nor a basic and non iterable type')

    return normalized_parameters_sources