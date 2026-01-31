from yta_parameters.context.abstract import EvaluationContext


class VideoEditorEvaluationContext(EvaluationContext):
    """
    Evaluation context that includes all the parameters
    needed to be able to evaluate the parameter for a
    video editor, including information about the local
    and global time moment, the frame index and the
    total number of frames, or the fps of the video.
    """

    # TODO: Maybe allow some of them as None (?)
    def __init__(
        self,
        t: float,
        t_normalized: float,
        t_global: float,
        t_global_normalized: float,
        frame_index: int,
        # TODO: This value is not clear at all
        number_of_frames: int,
        fps: float
    ):
        # TODO: We should validate the values but also
        # maybe allow some as None (?)
        self.t: float = t
        """
        The local not normalized time moment in which
        the parameter must be evaluated, that is based
        on the segment or item in which the parameter
        is being used. This can be a a transition, a
        node, etc.
        """
        self.t_normalized: float = t_normalized
        """
        The local normalized time moment in which the
        parameter must be evaluated, that is based on
        the segment or item in which the parameter is
        being used. This can be a transition, a node,
        etc.
        """
        self.t_global: float = t_global
        """
        The global not normalized time moment that is
        useful to compare the `t` with it. This is
        based on the global timeline in which the
        element that includes the parameter is placed.
        """
        self.t_global_normalized: float = t_global_normalized
        """
        The global normalized time moment that is
        useful to compare the `t` with it. This is
        based on the global timeline in which the
        element that includes t he parameter is placed.
        """
        self.frame_index: int = frame_index
        """
        The index of the frame in which the parameter
        is being evaluated.
        """
        self.number_of_frames: int = number_of_frames
        """
        The total number of frames that the video
        includes.

        TODO: Is this useful? It is not clear at all...
        """
        self.fps: float = fps
        """
        The number of frames per seconds that are being
        used for the video in which the element this
        parameter belongs to is being evaluated.
        """