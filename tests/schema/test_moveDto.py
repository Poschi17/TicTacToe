import pytest
from uuid import uuid4
from datetime import datetime, timezone

from schema.moveDto import MoveResponse, MoveRequest


def test_move_response_happy_path():
	now = datetime.now(timezone.utc)
	move = MoveResponse(
		id=uuid4(),
		game_id=uuid4(),
		player_id=uuid4(),
		player="X",
		position=5,
		created_at=now
	)
	assert move.player == "X"
	assert move.position == 5


def test_move_request_valid_position():
	req = MoveRequest(position=1)
	assert req.position == 1


def test_move_request_invalid_low_position():
	with pytest.raises(ValueError):
		MoveRequest(position=0)


def test_move_request_invalid_high_position():
	with pytest.raises(ValueError):
		MoveRequest(position=10)
