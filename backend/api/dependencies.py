from functools import lru_cache
from pathlib import Path

from backend.config import settings
from backend.infrastructure.json.job_store import JsonJobStore
from backend.infrastructure.json.saved_search_store import JsonSavedSearchStore
from backend.infrastructure.json.settings_store import JsonSettingsStore
from backend.infrastructure.linkedin_mcp.gateway import McpLinkedInGateway, MockLinkedInGateway
from backend.infrastructure.scoring.llm_scorer import LlmMatchScorer
from backend.infrastructure.scoring.rules_scorer import RulesMatchScorer
from backend.services.pipeline_service import PipelineService
from backend.services.saved_search_service import SavedSearchService
from backend.services.search_service import SearchService


@lru_cache
def get_data_dir() -> Path:
    d = settings.data_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


@lru_cache
def get_job_store() -> JsonJobStore:
    return JsonJobStore(get_data_dir())


@lru_cache
def get_saved_search_store() -> JsonSavedSearchStore:
    return JsonSavedSearchStore(get_data_dir())


@lru_cache
def get_settings_store() -> JsonSettingsStore:
    return JsonSettingsStore(get_data_dir())


@lru_cache
def get_gateway() -> McpLinkedInGateway | MockLinkedInGateway:
    if settings.mock_mcp:
        return MockLinkedInGateway()
    return McpLinkedInGateway(settings.mcp_base_url)


@lru_cache
def get_rules_scorer() -> RulesMatchScorer:
    return RulesMatchScorer()


@lru_cache
def get_llm_scorer() -> LlmMatchScorer:
    return LlmMatchScorer(get_rules_scorer())


def get_scorer(use_llm: bool):
    return get_llm_scorer() if use_llm else get_rules_scorer()


@lru_cache
def get_pipeline_service() -> PipelineService:
    return PipelineService(get_job_store())


@lru_cache
def get_saved_search_service() -> SavedSearchService:
    return SavedSearchService(get_saved_search_store(), get_gateway())


def get_search_service(use_llm: bool = False) -> SearchService:
    return SearchService(
        get_job_store(),
        get_saved_search_store(),
        get_gateway(),
        get_scorer(use_llm),
        get_pipeline_service(),
    )


def reset_dependencies() -> None:
    """Clear cached singletons (tests and hot reload)."""
    get_data_dir.cache_clear()
    get_job_store.cache_clear()
    get_saved_search_store.cache_clear()
    get_settings_store.cache_clear()
    get_gateway.cache_clear()
    get_rules_scorer.cache_clear()
    get_llm_scorer.cache_clear()
    get_pipeline_service.cache_clear()
    get_saved_search_service.cache_clear()
