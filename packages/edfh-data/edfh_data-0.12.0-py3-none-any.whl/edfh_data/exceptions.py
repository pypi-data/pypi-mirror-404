class RejectedEventError(ValueError):
    """Top level exception for EDDN events that pass validation but are rejected for
    other reasons."""

    pass


class EventTooOldError(RejectedEventError):
    """The EDDN event timestamp is too old."""

    pass
