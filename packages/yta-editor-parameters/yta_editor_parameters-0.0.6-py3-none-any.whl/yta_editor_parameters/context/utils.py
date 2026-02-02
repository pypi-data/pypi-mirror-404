from yta_editor_parameters.context import VideoEditorEvaluationContext


def get_evaluation_context(
    t_track: float,
    t_start_item: float,
    t_end_item: float,
    fps: float,
    track_duration: float
) -> VideoEditorEvaluationContext:
    """
    Get the evaluation context that should be passed
    to the different nodes and elements to be able to
    be applied correctly according to this data.
    """
    # The general time moment
    t_track_clamped = min(max(t_track, t_start_item), t_end_item)
    # The duration of the element in which we are
    item_duration = t_end_item - t_start_item
    # The local time moment of the element we are in
    t = t_track_clamped - t_start_item
    # The number of frames of the element we are in
    number_of_frames = max(1, round(item_duration * fps))
    # The index of the frame of the element we are in
    frame_index = min(
        number_of_frames - 1,
        int(round(t * fps))
    )
    # The local time moment but normalized
    t_normalized = (
        1.0
        if number_of_frames == 1 else
        frame_index / (number_of_frames - 1)
    )
    # The global time moment but normalized
    t_global_normalized = (
        1.0
        if track_duration == 0 else
        min(1.0, t_track_clamped / track_duration)
    )

    return VideoEditorEvaluationContext(
        t_normalized = t_normalized,
        t = t,
        t_global_normalized = t_global_normalized,
        t_global = t_track_clamped,
        frame_index = frame_index,
        number_of_frames = number_of_frames,
        fps = fps
    )