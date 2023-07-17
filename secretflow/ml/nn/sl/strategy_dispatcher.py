# Copyright 2023 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

BACKEND_LIST = ['tensorflow', 'torch']


class Dispatcher:
    def __init__(self):
        self._ops = {}

    def register(self, name, check_skip_grad, cls):
        if name in self._ops:
            raise Exception(f"Duplicate op {name} registered")
        self._ops[name] = (cls, check_skip_grad)

    def dispatch(self, name, backend, *args, **kwargs):
        strategy_name = f"{name}_{backend}"
        if strategy_name not in self._ops:
            raise Exception(f"Strategy {name} on backend {backend} not registered")
        cls, check_skip_grad = self._ops[strategy_name]
        return cls(*args, **kwargs), check_skip_grad


_strategy_dispatcher = Dispatcher()


def register_strategy(
    _cls=None, *, strategy_name=None, backend=None, check_skip_grad=False
):
    """register new strategy

    Args:
        _cls:
        strategy_name: name of strategy
        backend: backend of strategy(tensorflow/torch)
        check_skip_grad: whether this strategy need check skip gradient

    Returns:

    """

    def _register(cls):
        assert strategy_name is not None, "strategy_name is required, cannot be None"
        assert (
            backend is not None and backend in BACKEND_LIST
        ), "backend is required, cannot be None"
        name = f"{strategy_name}_{backend}"
        _strategy_dispatcher.register(name, check_skip_grad, cls)
        return cls

    # We're called with parameter.
    if _cls is None:
        return _register

    # We're called as @register without parameter.
    return _register(_cls)


def dispatch_strategy(name, backend, *args, **kwargs):
    """strategy dispatcher

    Args:
        name: name of strategy, str
        *args:
        **kwargs:

    Returns:

    """
    return _strategy_dispatcher.dispatch(name, backend, *args, **kwargs)
