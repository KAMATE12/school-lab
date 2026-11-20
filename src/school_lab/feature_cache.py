"""Bounded exact-source cache; scoring and original positions remain unchanged."""
from collections import OrderedDict

from school_lab.ast_features import prepare_ast_code
from school_lab.prepared_code import prepare_token_code


class FeatureCache:
    # RU: Кеш ограничен; метод фиксируется на время жизни экземпляра.
    # EN: The cache is bounded; the method is fixed for this instance's lifetime.
    def __init__(self, method, capacity=128):
        if method not in ("token", "ast"):
            raise ValueError("Unknown feature method")
        if type(capacity) is not int or capacity < 1:
            raise ValueError("Cache capacity must be a positive integer")
        self._prepare = prepare_token_code if method == "token" else prepare_ast_code
        self._capacity = capacity
        self._items = OrderedDict()
        self.hits = 0
        self.misses = 0

    def prepare(self, code, template=""):
        # RU: Полный текст сохраняет позиции; шаблон входит в ключ конфигурации.
        # EN: Exact text preserves positions; the template is part of the configuration key.
        key = (code, template)
        if key in self._items:
            self.hits += 1
            self._items.move_to_end(key)
            return self._items[key]
        self.misses += 1
        features = self._prepare(code, template)
        self._items[key] = features
        if len(self._items) > self._capacity:
            self._items.popitem(last=False)
        return features
