from functools import lru_cache
from pathlib import Path

from reverse_recruiter.config import settings
from reverse_recruiter.infrastructure.json.job_store import JsonJobStore
from reverse_recruiter.infrastructure.json.saved_search_store import JsonSavedSearchStore
from reverse_recruiter.infrastructure.json.settings_store import JsonSettingsStore
from reverse_recruiter.infrastructure.linkedin_mcp.gateway import McpLinkedInGateway, MockLinkedInGateway
from reverse_recruiter.infrastructure.scoring.llm_scorer import LlmMatchScorer
from reverse_recruiter.infrastructure.scoring.rules_scorer import RulesMatchScorer
from reverse_recruiter.services.pipeline_service import PipelineService
from reverse_recruiter.services.saved_search_service import SavedSearchService
from reverse_recruiter.services.search_service import SearchService


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
