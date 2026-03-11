import requests

from super_soccer_showdown.adapters.pokeapi_provider import PokeApiPlayerProvider
from super_soccer_showdown.adapters.random_provider import PythonRandomProvider
from super_soccer_showdown.adapters.swapi_provider import SwapiPlayerProvider
from super_soccer_showdown.application.use_cases import GenerateShowdownUseCase, GenerateTeamUseCase
from super_soccer_showdown.domain.entities import Universe


def build_generate_team_use_case() -> GenerateTeamUseCase:
    session = requests.Session()
    random_provider = PythonRandomProvider()

    providers = {
        Universe.STARWARS: SwapiPlayerProvider(session=session, random_provider=random_provider),
        Universe.POKEMON: PokeApiPlayerProvider(session=session, random_provider=random_provider),
    }

    return GenerateTeamUseCase(providers=providers)


def build_generate_showdown_use_case() -> GenerateShowdownUseCase:
    return GenerateShowdownUseCase(generate_team_use_case=build_generate_team_use_case())
