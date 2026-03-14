from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from super_soccer_showdown.service.user_service import RegisterUserUseCase, RefreshJwtTokenUseCase


class TestRegisterUserUseCase:
    async def test_execute_creates_user_and_returns_token_payload(self):
        user_repository = AsyncMock()
        user_repository.create_user = AsyncMock(
            return_value=SimpleNamespace(id=1, username="alice")
        )

        use_case = RegisterUserUseCase(user_repository)

        result = await use_case.execute("alice")

        user_repository.create_user.assert_awaited_once_with("alice")
        assert result["user_id"] == "1"
        assert result["username"] == "alice"
        assert isinstance(result["jwt_token"], str)

    async def test_execute_rejects_blank_username(self):
        user_repository = AsyncMock()
        use_case = RegisterUserUseCase(user_repository)

        with pytest.raises(ValueError, match="non-empty string"):
            await use_case.execute("   ")

    async def test_execute_rejects_usernames_longer_than_100_chars(self):
        user_repository = AsyncMock()
        use_case = RegisterUserUseCase(user_repository)

        with pytest.raises(ValueError, match="must not exceed 100 characters"):
            await use_case.execute("x" * 101)


class TestRefreshJwtTokenUseCase:
    async def test_execute_returns_token_for_existing_user(self):
        user_repository = AsyncMock()
        user_repository.get_user_by_id = AsyncMock(
            return_value=SimpleNamespace(id=7, username="bob")
        )

        use_case = RefreshJwtTokenUseCase(user_repository)

        result = await use_case.execute(7)

        user_repository.get_user_by_id.assert_awaited_once_with(7)
        assert result["user_id"] == "7"
        assert result["username"] == "bob"
        assert isinstance(result["jwt_token"], str)

    async def test_execute_rejects_non_integer_user_id(self):
        user_repository = AsyncMock()
        use_case = RefreshJwtTokenUseCase(user_repository)

        with pytest.raises(ValueError, match="Invalid user_id"):
            await use_case.execute("7")

    async def test_execute_rejects_missing_user(self):
        user_repository = AsyncMock()
        user_repository.get_user_by_id = AsyncMock(return_value=None)

        use_case = RefreshJwtTokenUseCase(user_repository)

        with pytest.raises(ValueError, match="User does not exist"):
            await use_case.execute(7)