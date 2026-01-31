import datetime as dt
from typing import Annotated, Literal, Self

from fdev_ids import load_table
from pydantic import AfterValidator
from pydantic import AliasPath
from pydantic import BaseModel
from pydantic import BeforeValidator
from pydantic import computed_field
from pydantic import Field
from pydantic import model_validator

economy_ids = load_table("economy")
security_ids = load_table("security")
government_ids = load_table("government")
happiness_ids = load_table("happiness")
factionstate_ids = load_table("factionstate")
commodity_symbols = {c["symbol"].lower(): c for c in load_table("commodity").values()}
rare_commodity_symbols = {
    c["symbol"].lower(): c for c in load_table("rare_commodity").values()
}

planetary_station_types = (
    "CraterOutpost",
    "CraterPort",
    "OnFootSettlement",
    "SurfaceStation",
)

construction_station_types = (
    "PlanetaryConstructionDepot",
    "SpaceConstructionDepot",
)

stronghold_carrier_names = (
    "Stronghold Carrier",
    "Hochburg-Carrier",
    "Porte-vaisseaux de forteresse",
    "Portanaves bastión",
    "Носитель-база",
    "Transportadora da potência",
)

occupied_states = ("Exploited", "Fortified", "Stronghold")


def replace_none(value: str | None) -> str | None:
    """Replace 'None' string and empty string values with None."""
    if value in ("None", ""):
        return None
    return value


def map_economy(economy_id: str) -> str | None:
    return replace_none(economy_ids.get(economy_id))


def map_security(security_id: str) -> str | None:
    return security_ids.get(security_id)


def map_government(government_id: str) -> str | None:
    return replace_none(government_ids.get(government_id))


def map_happiness(happiness_id: str) -> str | None:
    return happiness_ids.get(happiness_id)


def map_faction_state(factionstate_id: str) -> str | None:
    return replace_none(factionstate_ids.get(factionstate_id))


def map_commodity(commodity_symbol: str) -> str | None:
    all_commodities = commodity_symbols | rare_commodity_symbols
    return all_commodities[commodity_symbol.lower()]["name"]


class FactionState(BaseModel):
    """A state of a faction in a system."""

    state_phase: Literal["pending", "active", "recovering"]
    state: Annotated[str, BeforeValidator(map_faction_state)]


class SystemFaction(BaseModel):
    """Status of a faction in a star system.

    Aliases are defined so that an instance can be created from a record in the
    'Factions' field of the message of a journal/1 event with `event=FSDJump`
    """

    faction_name: str = Field(alias="Name")
    allegiance: str = Field(alias="Allegiance")
    faction_state: str = Field(alias="FactionState")
    government: str = Field(alias="Government")
    Happiness: Annotated[str | None, BeforeValidator(map_happiness)] = Field(
        default=None, alias="Happiness"
    )
    influence: float = Field(alias="Influence")
    states: list[FactionState] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def map_states(cls, data: dict) -> dict:
        pending = [
            FactionState(state=s["State"], state_phase="pending")
            for s in data.get("PendingStates", list())
        ]
        active = [
            FactionState(state=s["State"], state_phase="active")
            for s in data.get("ActiveStates", list())
        ]
        recovering = [
            FactionState(state=s["State"], state_phase="recovering")
            for s in data.get("RecoveringStates", list())
        ]
        data["states"] = pending + active + recovering

        return data


class SystemPowerConflictProgress(BaseModel):
    """Conflict state of a power in a system.

    Aliases are defined so that an instance can be created from a record in the
    'PowerplayConflictProgress' field of the message of a journal/1 event with
    `event=FSDJump`"""

    power: str = Field(alias="Power")
    conflict_progress: float = Field(alias="ConflictProgress")


def influence_total_is_one(system_factions: list[SystemFaction]) -> list[SystemFaction]:
    """Verify that the sum of faction influences is one (within 0.00001)."""
    is_one = 1.00001 >= sum(f.influence for f in system_factions) >= 0.99999

    if not is_one:
        raise ValueError("Sum of faction influences must be one")

    return system_factions


class System(BaseModel):
    """Star system.

    Aliases are defined so that an instance can be created from the message of a
    journal/1 event with `event=FSDJump`.
    """

    system_name: str = Field(alias="StarSystem")
    system_address: int = Field(alias="SystemAddress")
    population: int = Field(alias="Population")
    x: float = Field(validation_alias=AliasPath("StarPos", 0))
    y: float = Field(validation_alias=AliasPath("StarPos", 1))
    z: float = Field(validation_alias=AliasPath("StarPos", 2))
    update_datetime: dt.datetime = Field(alias="timestamp")
    is_colony: bool | None = Field(default=None)
    system_allegiance: Annotated[str | None, AfterValidator(replace_none)] = Field(
        default=None, alias="SystemAllegiance"
    )
    controlling_faction: Annotated[str | None, AfterValidator(replace_none)] = Field(
        default=None, validation_alias=AliasPath("SystemFaction", "Name")
    )
    controlling_power: Annotated[str | None, AfterValidator(replace_none)] = Field(
        default=None, alias="ControllingPower"
    )
    powerplay_conflict_progress: list[SystemPowerConflictProgress] = Field(
        default_factory=list, alias="PowerplayConflictProgress"
    )
    powerplay_state: (
        Literal["Unoccupied", "Exploited", "Fortified", "Stronghold"] | None
    ) = Field(default=None, alias="PowerplayState")
    powerplay_state_control_progress: float | None = Field(
        default=None, lt=10, alias="PowerplayStateControlProgress"
    )
    powerplay_state_reinforcement: int | None = Field(
        default=None, alias="PowerplayStateReinforcement"
    )
    powerplay_state_undermining: int | None = Field(
        default=None, alias="PowerplayStateUndermining"
    )
    primary_economy: Annotated[str | None, BeforeValidator(map_economy)] = Field(
        default=None, alias="SystemEconomy"
    )
    secondary_economy: Annotated[str | None, BeforeValidator(map_economy)] = Field(
        default=None, alias="SystemSecondEconomy"
    )
    security: Annotated[str | None, BeforeValidator(map_security)] = Field(
        default=None, alias="SystemSecurity"
    )
    government: Annotated[str | None, BeforeValidator(map_government)] = Field(
        default=None, alias="SystemGovernment"
    )
    system_factions: Annotated[
        list[SystemFaction], AfterValidator(influence_total_is_one)
    ] = Field(default_factory=list, alias="Factions")
    system_powers: list[str] = Field(default_factory=list, alias="Powers")

    @model_validator(mode="after")
    def occupied_system_has_powerplay_state_data(self) -> Self:
        required_state_values = (
            self.controlling_power,
            self.powerplay_state_control_progress,
            self.powerplay_state_reinforcement,
            self.powerplay_state_undermining,
        )
        state_values_missing = any(v is None for v in required_state_values)
        if self.powerplay_state in occupied_states and state_values_missing:
            raise ValueError("Occupied system has missing powerplay state values")
        return self

    @computed_field
    @property
    def system_name_lc(self) -> str:
        return self.system_name.lower()


def construction_type_not_allowed(station_type: str) -> str:
    """Raise an exception if the station type is a construction depot."""
    if station_type in construction_station_types:
        raise ValueError("Construction site not allowed as station")
    return station_type


def colonisation_ship_not_allowed(station_name: str) -> str:
    """Raise an exception if the station name indicates a colonisation ship."""
    if "colonisationship" in station_name.lower():
        raise ValueError("Colonisation ship not allowed as station")
    return station_name


class Station(BaseModel):
    """Station.

    Aliases are defined so that an instance can be created from the message of a
    journal/1 event with `event=Docked`.
    """

    system_name: str = Field(alias="StarSystem")
    system_address: int = Field(alias="SystemAddress")
    station_name: Annotated[str, AfterValidator(colonisation_ship_not_allowed)] = Field(
        alias="StationName"
    )
    distance_from_star: float = Field(alias="DistFromStarLS")
    market_id: int = Field(alias="MarketID")
    station_type: Annotated[str, AfterValidator(construction_type_not_allowed)] = Field(
        alias="StationType"
    )
    is_planetary: bool = Field(default=False)
    max_landing_pad_size: Literal["L", "M", "S"]
    primary_economy: Annotated[str, BeforeValidator(map_economy)] = Field(
        alias="StationEconomy"
    )
    secondary_economy: str | None = Field(default=None)
    station_faction_name: str = Field(
        validation_alias=AliasPath("StationFaction", "Name")
    )
    update_datetime: dt.datetime = Field(alias="timestamp")

    @model_validator(mode="before")
    @classmethod
    def _secondary_economy(cls, data: dict) -> dict:
        if len(data["StationEconomies"]) >= 2:
            data["secondary_economy"] = map_economy(data["StationEconomies"][1]["Name"])
        else:
            data["secondary_economy"] = None
        return data

    @model_validator(mode="before")
    @classmethod
    def _is_planetary(cls, data: dict) -> dict:
        data["is_planetary"] = data["StationType"] in planetary_station_types
        return data

    @model_validator(mode="before")
    @classmethod
    def _max_landing_pad_size(cls, data: dict) -> dict:
        pads = data.get("LandingPads")

        if not pads:
            raise ValueError("'LandingPads' field is missing")

        if pads.get("Large", 0) > 0:
            size = "L"
        elif pads.get("Medium", 0) > 0:
            size = "M"
        else:
            size = "S"
        data["max_landing_pad_size"] = size
        return data

    @model_validator(mode="after")
    def update_stronghold_carrier(self) -> Self:
        if self.station_name in stronghold_carrier_names:
            self.station_name = "Stronghold Carrier"
            self.station_type = "StrongholdCarrier"
            self.is_planetary = False
        return self


class Commodity(BaseModel):
    """A single commodity.

    Aliases are defined so that an instance can be created from a record in the
    commodities field of the commodity/3 event message.
    """

    name: Annotated[str, BeforeValidator(map_commodity)]
    mean_price: int = Field(alias="meanPrice")
    buy_price: int = Field(alias="buyPrice")
    stock: int
    sell_price: int = Field(alias="sellPrice")
    demand: int


def exclude_zero_commodities(commodities: list[Commodity]) -> list[Commodity]:
    """Exclude commodities with zero supply & demand."""
    return [c for c in commodities if not all([c.stock == 0, c.demand == 0])]


class StationMarket(BaseModel):
    """List of commodities in a station/market.

    Aliases are defined so that an instance can be created the message of the
    commodity/3 event.
    """

    market_id: int = Field(alias="marketId")
    commodities: Annotated[
        list[Commodity], AfterValidator(exclude_zero_commodities)
    ] = Field(default_factory=list, alias="commodities")
    update_datetime: dt.datetime = Field(alias="timestamp")
