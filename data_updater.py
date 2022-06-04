from __future__ import annotations
from dataclasses import dataclass
import requests
# import json

# == CONSTANTS ==

BULK_DATA_ENDPOINT = "https://api.scryfall.com/bulk-data/default-cards"
BULK_DATA_DOWNLOAD_URI_KEY = "download_uri"
BULK_DATA_UPDATED_AT_KEY = "updated_at"

# == CONSTANTS END ==


# == DATA CLASSES ==

@dataclass(frozen=True)
class BulkDataResponse:
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


# == DATA CLASSES END ==


def main():
    print("hello")
    bulk_data_response: BulkDataResponse = fetch_data()
    cards: dict = process_data(bulk_data_response.data)
    print(list(cards.items())[:30])
    return

# # TODO: delete this test method
# def main():
#     print("hello")
#     # bulk_data_response: BulkDataResponse = fetch_data()
#     with open('mtg-cotd/test_cards.json') as json_file:
#         test: dict = json.load(json_file)  
#         cards: dict = process_data(test)
#         print(len(cards))
#         print(list(cards.items())[:10])
#     return


def process_data(data: list[dict]) -> dict:
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

    return cards


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

    return BulkDataResponse(updated_at, data)



if __name__ == "__main__":
    main()
