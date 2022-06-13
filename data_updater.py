from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import requests
import firebase_admin
from firebase_admin import firestore
# import json

# == CONSTANTS ==

BULK_DATA_ENDPOINT = "https://api.scryfall.com/bulk-data/default-cards"
BULK_DATA_DOWNLOAD_URI_KEY = "download_uri"
BULK_DATA_UPDATED_AT_KEY = "updated_at"

DATABASE_WRITE_LIMIT = 19000
COLLECTION_CARD_BACKUPS = "card_backups"

# == CONSTANTS END ==


# == DATA CLASSES ==

@dataclass(frozen=True)
class BulkDataResponse:
    timestamp: str
    updated_at: str
    data: list[dict]


@dataclass(frozen=True)
class Card:
    name: str
    cmc: int
    mana_cost: list[str]
    colors: list[str]
    type: list[str]
    creature_type: str
    sets: list[str]
    power: int
    toughness: int

    def add_set(self, sets: list[str]) -> None:
        self.sets.append(*sets)

    @classmethod
    def from_json(cls: Card, card_json: dict) -> Card:
        if card_json["set_type"] == "funny":
            raise Exception("Card is funny")

        name: str = card_json["name"]

        cmc: float = card_json["cmc"]

        original_cost: str = card_json["mana_cost"]
        mana_cost: list[str] = original_cost.replace("{", "").split("}")[:-1]
        
        colors: list[str] = card_json["colors"]

        original_type: str = card_json["type_line"]
        if original_type.find("Creature") == -1:
            raise Exception("Card is not a Creature")
        allTypes: list[str] = original_type.split(" ")
        types = []
        creature_types = []
        passed_creature: bool = False
        for type in allTypes:
            if type == "Creature":
                passed_creature = True
                continue
            if type == "—":
                continue
            if not passed_creature:
                if type == "Token":
                    raise Exception("Card is a token")
                types.append(type)
            else:
                creature_types.append(type)

        sets = []
        sets.append(card_json["set_name"])

        power = card_json["power"]

        toughness = card_json["toughness"]
        
        return Card(name, cmc, mana_cost, colors, types, creature_types, sets, power, toughness)

    def to_dict(self: Card) -> dict:
        return {
            "name": self.name,
            "cmc": self.cmc,
            "mana_cost": self.mana_cost,
            "colors": self.colors,
            "type": self.type,
            "creature_type": self.creature_type,
            "sets": self.sets,
            "power": self.power,
            "toughness": self.toughness
            }

# == DATA CLASSES END ==


def main():
    print("hello")
    db_client = init_firebase()
    bulk_data_response: BulkDataResponse = fetch_data()
    cards: list[Card] = process_data(bulk_data_response.data)
    if len(cards) < DATABASE_WRITE_LIMIT:
        send_data(db_client, bulk_data_response.timestamp, bulk_data_response.updated_at, cards)
    return

def init_firebase() -> any:
    firebase_admin.initialize_app()
    return firestore.client()


def process_data(data: list[dict]) -> list[Card]:
    cards: dict = {}

    for card_data in data:
        try:
            card: Card = Card.from_json(card_data)
            if card.name in cards:
                existing_card: Card = cards[card.name]
                existing_card.add_set(card.sets)
            else:
                cards[card.name] = card
        except:
            continue

    return list(cards.values())


def fetch_data() -> BulkDataResponse:
    response = requests.get(BULK_DATA_ENDPOINT)
    if response.status_code != 200:
        raise Exception(f"Error fetching bulk data at {BULK_DATA_ENDPOINT}")

    response_json: dict = response.json()
    updated_at: str = response_json[BULK_DATA_UPDATED_AT_KEY]
    download_uri: str = response_json[BULK_DATA_DOWNLOAD_URI_KEY]

    data_response = requests.get(download_uri)
    if data_response.status_code != 200:
        raise Exception(f"Error fetching card bulk data at {download_uri}")

    data: list[dict] = data_response.json()

    return BulkDataResponse(datetime.now(), updated_at, data)

def send_data(db, timestamp: str, updated_at: str, cards: list[Card]):
    collection = db.collection(COLLECTION_CARD_BACKUPS)
    collection.add(
        {
            "timestamp": timestamp,
            "updated_at": updated_at,
            "card1"
            "cards": list(map(lambda card: card.to_dict(), cards))
        }
    )



if __name__ == "__main__":
    main()
