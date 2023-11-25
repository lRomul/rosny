import signal

_signals = [signal.SIGINT, signal.SIGTERM]
_default_handlers = {sig: signal.getsignal(signal.SIGINT) for sig in _signals}


class SignalException(BaseException):
    def __init__(self, signum: signal.Signals, frame):
        message = f"Handle signal: {signal.Signals(signum).name}"
        super().__init__(message)
        self.signum = signum
        self.frame = frame


def start_signals(node):
    def signal_handler(signum: signal.Signals, frame):
        exception = SignalException(signum, frame)
        node.logger.error(exception)
        node.stop()
        raise exception

    for sig in _signals:
        signal.signal(sig, signal_handler)
    node.logger.info("Start handling signals")


def stop_signals(node):
    for sig in _signals:
        signal.signal(sig, _default_handlers[sig])
    node.logger.info("Stop handling signals")
