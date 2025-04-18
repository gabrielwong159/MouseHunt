from typing import Optional

from pydantic import BaseModel, Field, model_validator


class UserData(BaseModel):
    user_id: int
    sn_user_id: str
    username: str
    unique_hash: str
    base_name: str
    weapon_name: str
    trinket_name: Optional[str]  # None if disarmed
    trinket_quantity: int
    bait_name: Optional[str]
    bait_quantity: int
    bait_disarmed: bool
    environment_name: str
    trap_power_type_name: str
    next_activeturn_seconds: int
    has_puzzle: bool
    quests: dict
    environment_atts: dict = Field(alias="enviroment_atts")

    @model_validator(mode="before")
    @classmethod
    def convert_sn_user_id_to_str(cls, data: dict) -> dict:
        # for some reason, some routes return sn_user_id as an int, so we always
        # convert to str for consistency
        if "sn_user_id" in data:
            data["sn_user_id"] = str(data["sn_user_id"])
        return data

    @model_validator(mode="before")
    @classmethod
    def convert_bait_disarmed_to_none(cls, data: dict) -> dict:
        if "bait_name" in data:
            # when a bait is disarmed, the value is 0
            if data["bait_name"] == 0:
                data["bait_name"] = None
        return data
