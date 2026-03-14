from super_soccer_showdown.domain.repositories.user_repository import UserRepository
from super_soccer_showdown.service.jwt_service import generate_token


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def execute(self, username: str) -> dict[str, str]:
        if not username or not isinstance(username, str) or len(username.strip()) == 0:
            raise ValueError("Username must be a non-empty string")

        username = username.strip()

        if len(username) > 100:
            raise ValueError("Username must not exceed 100 characters")

        user = await self._user_repository.create_user(username)
        token = generate_token(user.id, user.username)

        return {
            "user_id": str(user.id),
            "username": user.username,
            "jwt_token": token,
        }


class RefreshJwtTokenUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def execute(self, user_id: int) -> dict[str, str]:
        if not isinstance(user_id, int):
            raise ValueError("Invalid user_id in token")

        user = await self._user_repository.get_user_by_id(user_id)
        if user is None:
            raise ValueError("User does not exist")

        token = generate_token(user.id, user.username)
        return {
            "user_id": str(user.id),
            "username": user.username,
            "jwt_token": token,
        }