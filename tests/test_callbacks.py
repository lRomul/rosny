import pytest

from rosny import ComposeStream, ThreadStream


@pytest.mark.parametrize('stream_class', [ThreadStream, ComposeStream])
def test_stream_callbacks(stream_class):
    class CallbackStream(stream_class):
        def __init__(self):
            super().__init__()
            self.callback_history = []

        def work(self):
            pass

        def on_compile_begin(self):
            self.callback_history += ['on_compile_begin']

        def on_compile_end(self):
            self.callback_history += ['on_compile_end']

        def on_start_begin(self):
            self.callback_history += ['on_start_begin']

        def on_start_end(self):
            self.callback_history += ['on_start_end']

        def on_stop_begin(self):
            self.callback_history += ['on_stop_begin']

        def on_stop_end(self):
            self.callback_history += ['on_stop_end']

        def on_join_begin(self):
            self.callback_history += ['on_join_begin']

        def on_join_end(self):
            self.callback_history += ['on_join_end']

    stream = CallbackStream()
    stream.compile()
    assert stream.callback_history[-2:] == ['on_compile_begin', 'on_compile_end']
    stream.start()
    assert stream.callback_history[-2:] == ['on_start_begin', 'on_start_end']
    stream.stop()
    assert stream.callback_history[-2:] == ['on_stop_begin', 'on_stop_end']
    stream.join()
    assert stream.callback_history[-2:] == ['on_join_begin', 'on_join_end']
    assert stream.callback_history == [
        'on_compile_begin', 'on_compile_end',
        'on_start_begin', 'on_start_end',
        'on_stop_begin', 'on_stop_end',
        'on_join_begin', 'on_join_end'
    ]
