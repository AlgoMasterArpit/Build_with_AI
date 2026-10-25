from __future__ import annotations

import hashlib
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app.config import Settings
from app.domain.rounds import Room


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def link_key(token: str) -> dict[str, str]:
    return {"PK": f"LINK#{token_hash(token)}", "SK": "LINK"}


def hostel_pk(hostel_id: str) -> str:
    return f"HOSTEL#{hostel_id}"


def room_key(hostel_id: str, room_id: str) -> dict[str, str]:
    return {"PK": hostel_pk(hostel_id), "SK": f"ROOM#{room_id}"}


def _strip(item: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in item.items() if k not in ("PK", "SK")}


class Table:
    def __init__(self, settings: Settings) -> None:
        resource = boto3.resource(
            "dynamodb", region_name=settings.aws_region, endpoint_url=settings.aws_endpoint_url
        )
        self.client = resource.meta.client
        self.name = settings.table_name
        self.table = resource.Table(settings.table_name)

    def create_if_missing(self) -> None:
        try:
            self.client.describe_table(TableName=self.name)
            return
        except ClientError as error:
            if error.response["Error"]["Code"] != "ResourceNotFoundException":
                raise
        self.client.create_table(
            TableName=self.name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        self.client.get_waiter("table_exists").wait(TableName=self.name)
        self.client.update_time_to_live(
            TableName=self.name,
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "expires_at"},
        )

    def put_link(self, token: str, hostel_id: str, caretaker: str) -> None:
        self.table.put_item(
            Item={**link_key(token), "hostel_id": hostel_id, "caretaker": caretaker}
        )

    def get_link(self, token: str) -> dict[str, Any] | None:
        item = self.table.get_item(Key=link_key(token)).get("Item")
        return _strip(item) if item else None

    def put_hostel(self, hostel_id: str, name: str) -> None:
        self.table.put_item(Item={"PK": hostel_pk(hostel_id), "SK": "META", "name": name})

    def get_hostel_name(self, hostel_id: str) -> str | None:
        item = self.table.get_item(Key={"PK": hostel_pk(hostel_id), "SK": "META"}).get("Item")
        return str(item["name"]) if item else None

    def put_room(self, room: Room) -> None:
        self.table.put_item(
            Item={**room_key(room.hostel_id, room.room_id), **room.model_dump(exclude_none=True)}
        )

    def get_room(self, hostel_id: str, room_id: str) -> Room | None:
        item = self.table.get_item(Key=room_key(hostel_id, room_id)).get("Item")
        return Room.model_validate(_strip(item)) if item else None

    def list_rooms(self, hostel_id: str) -> list[Room]:
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(hostel_pk(hostel_id))
            & Key("SK").begins_with("ROOM#")
        )
        rooms = [Room.model_validate(_strip(i)) for i in response["Items"]]
        return sorted(rooms, key=lambda r: (len(r.room_id), r.room_id))
