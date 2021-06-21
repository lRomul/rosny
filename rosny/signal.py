import signal

_signals = [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]
_default_handlers = {sig: signal.getsignal(signal.SIGINT) for sig in _signals}


class SignalException(BaseException):
    def __init__(self, signum, frame):
        message = f"Handle signal: {signal.Signals(signum).name}"
        super().__init__(message)
        self.signum = signum
        self.frame = frame


def start_signals(stream):
    def signal_handler(signum, frame):
        exception = SignalException(signum, frame)
        stream.logger.error(exception)
        stream.stop()
        raise exception

    for sig in _signals:
        signal.signal(sig, signal_handler)
    stream.logger.info("Start handling signals")


def stop_signals(stream):
    for sig in _signals:
        signal.signal(sig, _default_handlers[sig])
    stream.logger.info("Stop handling signals")
