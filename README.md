# super-soccer-showdown
The Star Wars and Pokemon universes have collided and a big soccer tournament is being  planned to settle which universe is best.

## Solution Overview

This project provides a local REST API running as AWS Lambda functions (via AWS SAM) that generates random "Super Soccer Showdown" teams using:
- SWAPI: https://swapi.dev
- PokeAPI: https://pokeapi.co

### Team Rules Implemented

1. Team size is always 5 players.
2. A player can have exactly one position.
3. Each player includes:
- `Name`
- `Weight` (kg)
- `Height` (cm)
4. Player types:
- `Goalie`: tallest player
- `Defence`: heaviest players (based on lineup)
- `Offence`: shortest players (based on lineup)
5. Lineups are configurable by number of defenders and attackers, where:
- `defenders + attackers = 4`
- 1 goalie is always present

## Clean Architecture Structure

All backend code is under `infrastructure/src/super_soccer_showdown`:

- `domain/`: entities, business rules, domain exceptions
- `application/`: use cases (`GenerateTeamUseCase`, `GenerateShowdownUseCase`)
- `ports/`: provider interfaces
- `adapters/`: external API implementations for SWAPI/PokeAPI + random provider
- `entrypoints/lambda_api/`: Lambda handlers and dependency bootstrap

## API Endpoints

### 1) Generate One Universe Team

- `GET /teams/{universe}`
- `universe` values: `starwars`, `pokemon`
- Optional query params:
- `defenders` (default `2`)
- `attackers` (default `2`)

Example:

```bash
curl "http://127.0.0.1:3000/teams/starwars?defenders=3&attackers=1"
```

### 2) Generate Full Showdown (Both Teams)

- `POST /showdown`
- Optional JSON body:

```json
{
	"starwars": {"defenders": 2, "attackers": 2},
	"pokemon": {"defenders": 1, "attackers": 3}
}
```

Example:

```bash
curl -X POST "http://127.0.0.1:3000/showdown" \
	-H "Content-Type: application/json" \
	-d '{"starwars":{"defenders":2,"attackers":2},"pokemon":{"defenders":1,"attackers":3}}'
```

## Run Locally (Lambda + API Gateway)

Prerequisites:
- Python 3.12+
- AWS SAM CLI

From `infrastructure/`:

```bash
pip install -r requirements.txt
sam build
sam local start-api
```

API base URL:

```text
http://127.0.0.1:3000
```

## Run Tests

From `infrastructure/`:

```bash
python -m unittest discover -s tests -v
```
