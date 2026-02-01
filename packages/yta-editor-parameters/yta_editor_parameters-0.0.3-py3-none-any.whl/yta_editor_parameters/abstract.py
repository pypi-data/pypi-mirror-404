from yta_editor_parameters.context import VideoEditorEvaluationContext
from yta_parameters.abstract import Parameter
from abc import abstractmethod


class VideoEditorParameter(Parameter):
    """
    A parameter that uses a video editor context
    to be evaluated.
    """

    @abstractmethod
    def evaluate(
        self,
        # This is mandatory, even though it is not used
        evaluation_context: VideoEditorEvaluationContext
    ):
        pass