import datetime as dt
from typing import Mapping, Self

from sqlmodel import BigInteger
from sqlmodel import Column
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel
from sqlmodel import String
from sqlmodel import TIMESTAMP


class UpdatableSQLModel(SQLModel):

    def update(self, **kwargs: Mapping) -> Self:
        """Update the speficied fields of the model instance and return the instance."""
        for field, value in kwargs.items():
            if field in self.__class__.model_fields:
                setattr(self, field, value)
        return self

    def __or__(self, other: Mapping) -> Self:
        """Update the speficied fields of the model instance from a dictionary using
        the or ('|') operator"""
        return self.update(**other)


class SystemDB(UpdatableSQLModel, table=True):
    __tablename__ = "systems"  # type: ignore
    system_id: int | None = Field(default=None, primary_key=True, sa_type=BigInteger)
    system_name: str = Field(index=True)
    system_name_lc: str = Field(index=True)
    system_address: int = Field(unique=True, index=True, sa_type=BigInteger)
    x: float
    y: float
    z: float
    population: int = Field(sa_type=BigInteger)
    is_colony: bool | None = Field(default=None)
    system_factions: list["SystemFactionDB"] = Relationship(
        back_populates="system", cascade_delete=True
    )
    update_datetime: dt.datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    system_allegiance: str | None = Field(default=None)
    controlling_faction: str | None = Field(default=None)
    controlling_power: str | None = Field(default=None)
    powerplay_conflict_progress: list["SystemPowerConflictProgressDB"] = Relationship(
        back_populates="system", cascade_delete=True
    )
    powerplay_state: str | None = Field(default=None)
    powerplay_state_control_progress: float | None = Field(default=None)
    powerplay_state_reinforcement: int | None = Field(default=None)
    powerplay_state_undermining: int | None = Field(default=None)
    primary_economy: str | None = Field(default=None)
    secondary_economy: str | None = Field(default=None)
    security: str | None = Field(default=None)
    government: str | None = Field(default=None)
    system_powers: list["SystemPowerDB"] = Relationship(
        back_populates="system", cascade_delete=True
    )
    system_factions_history: list["SystemFactionHistoryDB"] = Relationship(
        back_populates="system", cascade_delete=True
    )
    system_power_state_history: list["SystemPowerStateHistoryDB"] = Relationship(
        back_populates="system", cascade_delete=True
    )
    stations: list["StationDB"] = Relationship(
        back_populates="system", cascade_delete=True
    )


class SystemFactionDB(UpdatableSQLModel, table=True):
    __tablename__ = "system_factions"  # type: ignore
    system_faction_id: int | None = Field(
        default=None, primary_key=True, sa_type=BigInteger
    )
    system_id: int = Field(
        foreign_key="systems.system_id", index=True, sa_type=BigInteger
    )
    faction_name: str
    influence: float
    faction_states: list["FactionStateDB"] = Relationship(
        back_populates="system_faction", cascade_delete=True
    )
    system: SystemDB = Relationship(back_populates="system_factions")


class SystemPowerDB(UpdatableSQLModel, table=True):
    __tablename__ = "system_powers"  # type: ignore
    system_power_id: int | None = Field(
        default=None, primary_key=True, sa_type=BigInteger
    )
    system_id: int = Field(
        foreign_key="systems.system_id", index=True, sa_type=BigInteger
    )
    power: str
    system: SystemDB = Relationship(back_populates="system_powers")


class SystemFactionHistoryDB(SQLModel, table=True):
    __tablename__ = "system_factions_history"  # type: ignore
    system_faction_history_id: int | None = Field(
        default=None, primary_key=True, sa_type=BigInteger
    )
    system_id: int = Field(
        foreign_key="systems.system_id", index=True, sa_type=BigInteger
    )
    faction_name: str
    influence: float
    states: str | None = Field(default=None, sa_type=String(1024))
    update_datetime: dt.datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    system: SystemDB = Relationship(back_populates="system_factions_history")


class FactionStateDB(SQLModel, table=True):
    __tablename__ = "faction_states"  # type: ignore
    faction_state_id: int | None = Field(
        default=None, primary_key=True, sa_type=BigInteger
    )
    system_faction_id: int = Field(
        foreign_key="system_factions.system_faction_id", index=True, sa_type=BigInteger
    )
    state_phase: str
    state: str
    system_faction: SystemFactionDB = Relationship(back_populates="faction_states")


class SystemPowerConflictProgressDB(UpdatableSQLModel, table=True):
    __tablename__ = "system_power_conflict_progress"  # type: ignore
    system_power_conflict_progress_id: int | None = Field(
        default=None, primary_key=True, sa_type=BigInteger
    )
    system_id: int = Field(
        foreign_key="systems.system_id", index=True, sa_type=BigInteger
    )
    power: str
    conflict_progress: float
    system: SystemDB = Relationship(back_populates="powerplay_conflict_progress")


class SystemPowerStateHistoryDB(UpdatableSQLModel, table=True):
    __tablename__ = "system_power_state_history"  # type: ignore
    system_power_state_history_id: int | None = Field(
        default=None, primary_key=True, sa_type=BigInteger
    )
    system_id: int = Field(
        foreign_key="systems.system_id", index=True, sa_type=BigInteger
    )
    controlling_power: str | None = Field(default=None, index=True)
    powerplay_state: str | None = Field(default=None)
    powerplay_state_control_progress: float | None = Field(default=None)
    powerplay_state_reinforcement: int | None = Field(default=None)
    powerplay_state_undermining: int | None = Field(default=None)
    update_datetime: dt.datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    system: SystemDB = Relationship(back_populates="system_power_state_history")


class StationDB(UpdatableSQLModel, table=True):
    __tablename__ = "stations"  # type: ignore
    station_id: int | None = Field(default=None, primary_key=True, sa_type=BigInteger)
    system_id: int = Field(
        foreign_key="systems.system_id", index=True, sa_type=BigInteger
    )
    station_name: str
    distance_from_star: float
    market_id: int = Field(unique=True, index=True, sa_type=BigInteger)
    station_type: str
    is_planetary: bool
    max_landing_pad_size: str
    primary_economy: str
    secondary_economy: str | None = Field(default=None)
    station_faction_name: str = Field(index=True)
    update_datetime: dt.datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    system: SystemDB = Relationship(back_populates="stations")
    market_commodities: list["MarketCommodityDB"] = Relationship(
        back_populates="station", cascade_delete=True
    )
    market_update_datetime: dt.datetime | None = Field(
        default=None, sa_column=Column(TIMESTAMP(timezone=True))
    )


class MarketCommodityDB(UpdatableSQLModel, table=True):
    __tablename__ = "market_commodities"  # type: ignore
    market_commodity_id: int | None = Field(
        default=None, primary_key=True, sa_type=BigInteger
    )
    station_id: int = Field(
        foreign_key="stations.station_id", index=True, sa_type=BigInteger
    )
    name: str
    mean_price: int
    buy_price: int
    stock: int
    sell_price: int
    demand: int
    station: StationDB = Relationship(back_populates="market_commodities")
