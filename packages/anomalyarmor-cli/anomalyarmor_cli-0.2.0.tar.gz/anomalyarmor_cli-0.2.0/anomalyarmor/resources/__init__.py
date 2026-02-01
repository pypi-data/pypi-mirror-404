"""Resource classes for the Armor SDK."""

from anomalyarmor.resources.alerts import AlertsResource
from anomalyarmor.resources.api_keys import APIKeysResource
from anomalyarmor.resources.assets import AssetsResource
from anomalyarmor.resources.badges import BadgesResource
from anomalyarmor.resources.freshness import FreshnessResource
from anomalyarmor.resources.health import HealthResource
from anomalyarmor.resources.intelligence import IntelligenceResource
from anomalyarmor.resources.lineage import LineageResource
from anomalyarmor.resources.recommendations import RecommendationsResource
from anomalyarmor.resources.schema import SchemaResource
from anomalyarmor.resources.tags import TagsResource

__all__ = [
    "AssetsResource",
    "FreshnessResource",
    "HealthResource",
    "SchemaResource",
    "LineageResource",
    "AlertsResource",
    "APIKeysResource",
    "IntelligenceResource",
    "TagsResource",
    "BadgesResource",
    "RecommendationsResource",
]
