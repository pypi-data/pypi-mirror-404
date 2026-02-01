from yta_editor_parameters.abstract import VideoEditorParameter
from yta_editor_parameters import ConstantVideoEditorParameter
from yta_validation import PythonValidator


def parse_parameters(
    parameters: dict
) -> dict[str, 'VideoEditorParameter']:
    """
    Parse the `parameters` provided and raise an exception
    if some of them is unaccepted. It will transform the
    basic types into `ConstantVideoEditorParameter`
    instances, and return the new dict with the values
    transformed.

    These types will be transformed into constant values:
    - `int`
    - `float`
    - `bool`
    - `str`
    - `None`
    """
    parameters_parsed = {}

    for name, value in parameters.items():
        if PythonValidator.is_instance_of(value, VideoEditorParameter):
            parameters_parsed[name] = value
            continue

        if (
            PythonValidator.is_basic_non_iterable_type(value) or
            value is None
        ):
            parameters_parsed[name] = ConstantVideoEditorParameter(value)
            continue
        
        raise Exception(f'The "{name}" parameter is not a "VideoEditorParameter" nor a basic and non iterable type')

    return parameters_parsed