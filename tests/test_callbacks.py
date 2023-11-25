import pytest
from multiprocessing import Manager

from rosny import ThreadNode, ProcessNode, ComposeNode


@pytest.mark.parametrize('node_class', [ThreadNode, ProcessNode, ComposeNode])
def test_node_callbacks(node_class):
    class CallbackNode(node_class):
        def __init__(self):
            super().__init__()
            self.manager = Manager()
            self.callback_history = self.manager.list([])

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

    node = CallbackNode()
    node.compile()
    assert node.callback_history[-2:] == ['on_compile_begin', 'on_compile_end']
    node.start()
    assert node.callback_history[-2:] == ['on_start_begin', 'on_start_end']
    node.stop()
    assert node.callback_history[-2:] == ['on_stop_begin', 'on_stop_end']
    node.join()
    assert node.callback_history[-2:] == ['on_join_begin', 'on_join_end']
    assert node.callback_history[:] == [
        'on_compile_begin', 'on_compile_end',
        'on_start_begin', 'on_start_end',
        'on_stop_begin', 'on_stop_end',
        'on_join_begin', 'on_join_end'
    ]
