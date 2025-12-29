# app/core/registry.py

from app.core.metrics import BaseMetric, JaccardMetric


class MetricsRegistry:
    def __init__(self):
        self._metrics = {}

    def register(self, metric):
        self._metrics[metric.name] = metric

    def get(self, name):
        return self._metrics.get(name)

    def list(self):
        return [
            {"name": m.name, "description": m.description}
            for m in self._metrics.values()
        ]


registry = MetricsRegistry()
registry.register(JaccardMetric())