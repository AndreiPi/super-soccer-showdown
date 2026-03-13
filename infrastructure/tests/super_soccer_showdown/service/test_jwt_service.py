import pytest
import jwt
from datetime import datetime, timedelta, timezone

from super_soccer_showdown.service.jwt_service import (
    JWTConfig,
    decode_token,
    generate_token,
    get_jwt_payload,
)


# ---------------------------------------------------------------------------
# generate_token
# ---------------------------------------------------------------------------

class TestGenerateToken:
    def test_returns_a_string(self):
        token = generate_token(1, "alice")
        assert isinstance(token, str)

    def test_token_contains_correct_user_claims(self):
        token = generate_token(42, "bob")
        payload = jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM])
        assert payload["user_id"] == 42
        assert payload["username"] == "bob"

    def test_token_contains_exp_and_iat_claims(self):
        token = generate_token(1, "alice")
        payload = jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM])
        assert "exp" in payload
        assert "iat" in payload

    def test_different_users_produce_different_tokens(self):
        token1 = generate_token(1, "alice")
        token2 = generate_token(2, "bob")
        assert token1 != token2


# ---------------------------------------------------------------------------
# decode_token
# ---------------------------------------------------------------------------

class TestDecodeToken:
    def test_valid_token_returns_full_payload(self):
        token = generate_token(7, "charlie")
        payload = decode_token(token)
        assert payload["user_id"] == 7
        assert payload["username"] == "charlie"

    def test_expired_token_raises_value_error_with_expired_message(self):
        expired = jwt.encode(
            {
                "user_id": 1,
                "username": "test",
                "iat": datetime.now(timezone.utc) - timedelta(hours=2),
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            JWTConfig.SECRET_KEY,
            algorithm=JWTConfig.ALGORITHM,
        )
        with pytest.raises(ValueError, match="[Ee]xpired"):
            decode_token(expired)

    def test_token_signed_with_wrong_secret_raises_value_error(self):
        token = jwt.encode({"user_id": 1, "username": "x"}, "wrong-secret", algorithm="HS256")
        with pytest.raises(ValueError):
            decode_token(token)

    def test_completely_invalid_token_raises_value_error(self):
        with pytest.raises(ValueError):
            decode_token("this.is.not.a.jwt")

    def test_empty_token_raises_value_error(self):
        with pytest.raises(ValueError):
            decode_token("")


# ---------------------------------------------------------------------------
# get_jwt_payload
# ---------------------------------------------------------------------------

class TestGetJwtPayload:
    def test_valid_bearer_token_returns_correct_payload(self):
        token = generate_token(5, "dave")
        event = {"headers": {"Authorization": f"Bearer {token}"}}
        payload = get_jwt_payload(event)
        assert payload["user_id"] == 5
        assert payload["username"] == "dave"

    def test_lowercase_authorization_header_is_accepted(self):
        token = generate_token(5, "dave")
        event = {"headers": {"authorization": f"Bearer {token}"}}
        payload = get_jwt_payload(event)
        assert payload["user_id"] == 5

    def test_missing_authorization_header_raises(self):
        with pytest.raises(ValueError, match="[Mm]issing"):
            get_jwt_payload({"headers": {}})

    def test_missing_headers_key_raises(self):
        with pytest.raises(ValueError):
            get_jwt_payload({})

    def test_token_without_bearer_prefix_raises(self):
        token = generate_token(1, "x")
        with pytest.raises(ValueError):
            get_jwt_payload({"headers": {"Authorization": f"Token {token}"}})

    def test_bearer_with_expired_token_raises_value_error(self):
        expired = jwt.encode(
            {
                "user_id": 1,
                "username": "x",
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            JWTConfig.SECRET_KEY,
            algorithm=JWTConfig.ALGORITHM,
        )
        with pytest.raises(ValueError):
            get_jwt_payload({"headers": {"Authorization": f"Bearer {expired}"}})
