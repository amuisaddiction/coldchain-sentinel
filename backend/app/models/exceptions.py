"""Model-level immutability and domain exceptions."""


class ImmutableProfileError(Exception):
    """Raised when an in-place update is attempted on a locked ProductProfile's rules."""
    pass


class ImmutableSnapshotError(Exception):
    """Raised when an update is attempted on a Shipment's frozen rule snapshot."""
    pass
