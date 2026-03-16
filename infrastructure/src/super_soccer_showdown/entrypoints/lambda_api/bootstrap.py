import asyncio
import os
from typing import Coroutine, Any

import httpx

from super_soccer_showdown.domain.repositories.player_repository import PlayerRepository
from super_soccer_showdown.domain.repositories.soccer_match_repository import SoccerMatchRepository
from super_soccer_showdown.domain.repositories.soccer_team_repository import SoccerTeamRepository
from super_soccer_showdown.adapters.pokeapi_provider import PokeApiPlayerProvider
from super_soccer_showdown.adapters.swapi_provider import SwapiPlayerProvider
from super_soccer_showdown.domain.repositories.user_repository import UserRepository
from super_soccer_showdown.service.match_service import GenerateShowdownUseCase, ListMatchesUseCase
from super_soccer_showdown.service.player_service import SyncPlayersCatalogUseCase
from super_soccer_showdown.service.team_service import GenerateTeamUseCase, ListTeamsUseCase
from super_soccer_showdown.service.user_service import RefreshJwtTokenUseCase, RegisterUserUseCase
from super_soccer_showdown.domain.entities import Universe
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


_ENGINE = None
_SESSION_FACTORY = None
_HTTP_CLIENT = None
_EVENT_LOOP: asyncio.AbstractEventLoop | None = None
_TRACKED_SESSIONS: list[AsyncSession] = []


def build_database_url() -> str:
    db_user = os.environ.get("DB_USER", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "postgres")
    db_host = os.environ.get("DB_HOST", "postgres")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "super_soccer_showdown")
    return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def get_db_session() -> AsyncSession:
    global _ENGINE, _SESSION_FACTORY, _TRACKED_SESSIONS

    if _ENGINE is None:
        _ENGINE = create_async_engine(build_database_url(), echo=False, pool_pre_ping=True)

    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = async_sessionmaker(bind=_ENGINE, expire_on_commit=False, class_=AsyncSession)

    session = _SESSION_FACTORY()
    _TRACKED_SESSIONS.append(session)
    return session


def get_event_loop() -> asyncio.AbstractEventLoop:
    global _EVENT_LOOP
    if _EVENT_LOOP is None or _EVENT_LOOP.is_closed():
        _EVENT_LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_EVENT_LOOP)
    return _EVENT_LOOP


async def close_tracked_sessions() -> None:
    global _TRACKED_SESSIONS
    sessions = _TRACKED_SESSIONS[:]
    _TRACKED_SESSIONS = []
    for session in sessions:
        try:
            await session.close()
        except Exception:
            pass


def run_handler(coro: Coroutine[Any, Any, Any]) -> Any:
    async def _wrapper() -> Any:
        try:
            return await coro
        finally:
            await close_tracked_sessions()

    return get_event_loop().run_until_complete(_wrapper())


def get_http_client() -> httpx.AsyncClient:
    global _HTTP_CLIENT

    if _HTTP_CLIENT is not None:
        return _HTTP_CLIENT

    pool_maxsize = max(1, int(os.environ.get("HTTP_POOL_MAXSIZE", 50)))
    pool_connections = max(1, int(os.environ.get("HTTP_POOL_CONNECTIONS", 20)))
    transport_retries = max(0, int(os.environ.get("HTTP_TRANSPORT_RETRIES", 2)))
    limits = httpx.Limits(
        max_connections=pool_maxsize,
        max_keepalive_connections=pool_connections,
    )
    transport = httpx.AsyncHTTPTransport(retries=transport_retries)
    _HTTP_CLIENT = httpx.AsyncClient(limits=limits, transport=transport)
    return _HTTP_CLIENT


def build_generate_team_use_case() -> GenerateTeamUseCase:
    db_session = get_db_session()
    player_repository = PlayerRepository(db_session)
    team_repository = SoccerTeamRepository(db_session, player_repository)
    session = get_http_client()

    providers = {
        Universe.STARWARS: SwapiPlayerProvider(session=session),
        Universe.POKEMON: PokeApiPlayerProvider(session=session),
    }

    return GenerateTeamUseCase(
        providers=providers,
        team_repository=team_repository,
        player_repository=player_repository,
    )


def build_sync_players_catalog_use_case() -> SyncPlayersCatalogUseCase:
    db_session = get_db_session()
    player_repository = PlayerRepository(db_session)
    session = get_http_client()

    providers = {
        Universe.STARWARS: SwapiPlayerProvider(session=session),
        Universe.POKEMON: PokeApiPlayerProvider(session=session),
    }

    return SyncPlayersCatalogUseCase(providers=providers, player_repository=player_repository)


def build_list_teams_use_case() -> ListTeamsUseCase:
    db_session = get_db_session()
    player_repository = PlayerRepository(db_session)
    team_repository = SoccerTeamRepository(db_session, player_repository)
    return ListTeamsUseCase(team_repository=team_repository)


def build_generate_showdown_use_case() -> GenerateShowdownUseCase:
    db_session = get_db_session()
    player_repository = PlayerRepository(db_session)
    team_repository = SoccerTeamRepository(db_session, player_repository)
    match_repository = SoccerMatchRepository(db_session)
    return GenerateShowdownUseCase(team_repository=team_repository, match_repository=match_repository)


def build_list_matches_use_case() -> ListMatchesUseCase:
    db_session = get_db_session()
    match_repository = SoccerMatchRepository(db_session)
    return ListMatchesUseCase(match_repository=match_repository)


def build_register_user_use_case() -> RegisterUserUseCase:
    db_session = get_db_session()
    user_repository = UserRepository(db_session)
    return RegisterUserUseCase(user_repository)


def build_refresh_jwt_token_use_case() -> RefreshJwtTokenUseCase:
    db_session = get_db_session()
    user_repository = UserRepository(db_session)
    return RefreshJwtTokenUseCase(user_repository)
