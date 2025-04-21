class ChannelNotConnectedError(Exception):
    """Raised when no output channels are configured"""
    pass


class InvalidConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass
