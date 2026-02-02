from yta_editor_parameters.abstract import VideoEditorParameter
from yta_editor_parameters import ConstantVideoEditorParameter
from yta_parameters.types import BASIC_NON_ITERABLE_TYPE
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

def is_this_constant_value(
    parameter: VideoEditorParameter,
    value: BASIC_NON_ITERABLE_TYPE
) -> bool:
    """
    Check if the `parameter` provided is a 
    `ConstantVideoEditorParameter` and has the
    `value` provided.

    This is useful to check if a parameter is
    the default value and we don't need to apply
    any change because of this.
    """
    # TODO: We could add an Eased but with the
    # same 'start_value' and 'end_value' because
    # the evaluation will be the same always
    return (
        PythonValidator.is_instance_of(parameter, ConstantVideoEditorParameter) and
        parameter.value == value
    )