from yta_parameters.context.abstract import EvaluationContext
from typing import Union


class VideoEditorEvaluationContext(EvaluationContext):
    """
    Evaluation context that includes all the parameters
    needed to be able to evaluate the parameter for a
    video editor, including information about the local
    and global time moment, the frame index and the
    total number of frames of the local item, or the fps
    of the video.
    """

    # We should not accept 'None' to be more strict
    # and build always the context with all the info
    def __init__(
        self,
        t_normalized: float,
        t: Union[float, None] = None,
        t_global_normalized: Union[float, None] = None,
        t_global: Union[float, None] = None,
        frame_index: Union[int, None] = None,
        # TODO: This value is not clear at all
        number_of_frames: Union[int, None] = None,
        fps: Union[float, None] = None
    ):
        # Local time
        self.t_normalized: float = t_normalized
        """
        The local normalized time moment in which the
        parameter must be evaluated, that is based on
        the segment or item in which the parameter is
        being used. This can be a transition, a node,
        etc.

        A value in the `[0.0, 1.0]` range representing
        the progress of the local item.
        """
        self.t: Union[float, None] = t
        """
        The local not normalized time moment in which
        the parameter must be evaluated, that is based
        on the segment or item in which the parameter
        is being used. This can be a a transition, a
        node, etc.

        The time (in seconds) elapsed since the
        `t_start` of the local item.
        """

        # Global (track) time
        self.t_global_normalized: Union[float, None] = t_global_normalized
        """
        The global normalized time moment that is
        useful to compare the `t` with it. This is
        based on the global timeline in which the
        element that includes t he parameter is placed.

        A value in the `[0.0, 1.0]` range representing
        the progress of the global track.
        """
        self.t_global: Union[float, None] = t_global
        """
        The global not normalized time moment that is
        useful to compare the `t` with it. This is
        based on the global timeline in which the
        element that includes the parameter is placed.

        The time (in seconds) elapsed since the
        `t_start` of the global track.
        """

        # Frame (local) indexes
        self.frame_index: Union[int, None] = frame_index
        """
        The index of the frame in which the parameter
        is being evaluated.

        The index according to the local item.
        """
        self.number_of_frames: Union[int, None] = number_of_frames
        """
        The total number of frames of the local item.
        """

        self.fps: Union[float, None] = fps
        """
        The number of frames per seconds that are being
        used for the video in which the element this
        parameter belongs to is being evaluated.
        """