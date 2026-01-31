import datetime as dt
import json

from sqlmodel import and_
from sqlmodel import desc
from sqlmodel import select
from sqlmodel import Session

from edfh_data.db.models import FactionStateDB
from edfh_data.db.models import MarketCommodityDB
from edfh_data.db.models import StationDB
from edfh_data.db.models import SystemDB
from edfh_data.db.models import SystemFactionDB
from edfh_data.db.models import SystemFactionHistoryDB
from edfh_data.db.models import SystemPowerConflictProgressDB
from edfh_data.db.models import SystemPowerDB
from edfh_data.db.models import SystemPowerStateHistoryDB
from edfh_data.db.utils import common_keys_equal
from edfh_data.db.utils import engine
from edfh_data.db.utils import index
from edfh_data.models import Station
from edfh_data.models import StationMarket
from edfh_data.models import System

UTC = dt.timezone.utc


def create_update_system(system: System) -> None:

    system_data = system.model_dump(
        exclude={"system_factions", "system_powers", "powerplay_conflict_progress"},
    )

    with Session(engine) as session:
        stmt = select(SystemDB).where(SystemDB.system_address == system.system_address)
        res = session.exec(stmt)
        system_db = res.one_or_none()

        if system_db:
            system_update = system.update_datetime.replace(tzinfo=UTC)
            system_db_update = system_db.update_datetime.replace(tzinfo=UTC)
            if system_update > system_db_update:
                if (
                    system.population > system_db.population
                    or system.controlling_faction == "Brewer Corporation"
                ):
                    system_data["is_colony"] = True
                system_db = system_db | system_data
            else:
                return
        else:
            system_db = SystemDB(**system_data)
            session.add(system_db)
            session.commit()
            session.refresh(system_db)

        system_factions = []
        system_factions_ix = index(system_db.system_factions, key="faction_name")

        for faction in system.system_factions:

            faction_data = faction.model_dump(exclude_none=True, exclude={"states"})

            states_data = None
            if faction.states:
                states_data = json.dumps(faction.model_dump(mode="json")["states"])

            if faction.faction_name in system_factions_ix:
                system_faction = system_factions_ix[faction.faction_name] | faction_data
            else:
                system_faction = SystemFactionDB(**faction_data)

            system_faction.faction_states = [
                FactionStateDB(**state.model_dump()) for state in faction.states
            ]

            system_factions.append(system_faction)

            # Get latest faction data from history
            stmt = (
                select(SystemFactionHistoryDB)
                .where(
                    and_(
                        SystemFactionHistoryDB.system_id == system_db.system_id,
                        SystemFactionHistoryDB.faction_name == faction.faction_name,
                    )
                )
                .order_by(desc(SystemFactionHistoryDB.update_datetime))
            )
            res = session.exec(stmt)
            system_faction_latest = res.first()

            if system_faction_latest:
                # Only update the update_datetime field if faction data has not changed
                if common_keys_equal(faction_data, system_faction_latest.model_dump()):
                    system_faction_latest.update_datetime = system.update_datetime
                    session.add(system_faction_latest)
                # Create new entry only if values have updated
                else:
                    system_faction_latest = SystemFactionHistoryDB(
                        system_id=system_db.system_id,  # type: ignore
                        update_datetime=system.update_datetime,
                        states=states_data,
                        **faction_data,
                    )
            else:
                system_faction_latest = SystemFactionHistoryDB(
                    system_id=system_db.system_id,  # type: ignore
                    update_datetime=system.update_datetime,
                    states=states_data,
                    **faction_data,
                )

            session.add(system_faction_latest)

        system_db.system_factions = system_factions

        system_powers = []
        system_powers_ix = index(system_db.system_powers, key="power")

        for power in system.system_powers:

            if power in system_powers_ix:
                system_power = system_powers_ix[power]
            else:
                system_power = SystemPowerDB(
                    system_id=system_db.system_id,  # type: ignore
                    power=power,
                )

            system_powers.append(system_power)

        system_db.system_powers = system_powers

        # powerplay_conflict_progress
        spcps = []
        spcp_ix = index(system_db.powerplay_conflict_progress, key="power")

        for spcp in system.powerplay_conflict_progress:

            spcp_data = spcp.model_dump()

            if spcp.power in spcp_ix:
                spcp_db = spcp_ix[spcp.power] | spcp_data
            else:
                spcp_db = SystemPowerConflictProgressDB(
                    system_id=system_db.system_id, **spcp_data  # type: ignore
                )

            spcps.append(spcp_db)

        system_db.powerplay_conflict_progress = spcps

        if system.powerplay_state:
            # Get latest powerplay state from history
            stmt = (
                select(SystemPowerStateHistoryDB)
                .where(SystemPowerStateHistoryDB.system_id == system_db.system_id)
                .order_by(desc(SystemPowerStateHistoryDB.update_datetime))
            )
            res = session.exec(stmt)
            power_state_history_latest = res.first()

            if power_state_history_latest:
                # Create a new entry if powerplay values have updated
                if not common_keys_equal(
                    power_state_history_latest.model_dump(),
                    system_data,
                    exclude_keys=["update_datetime"],
                ):
                    power_state_history_new = SystemPowerStateHistoryDB(
                        system_id=system_db.system_id, **system_data  # type: ignore
                    )
                    session.add(power_state_history_new)

            else:
                # No previous powerplay state history -> create one
                power_state_history_new = SystemPowerStateHistoryDB(
                    system_id=system_db.system_id, **system_data  # type: ignore
                )
                session.add(power_state_history_new)

        session.add(system_db)
        session.commit()


def create_update_station(station: Station) -> None:

    station_data = station.model_dump(exclude_none=True)

    with Session(engine) as session:
        # Get the parent system from the DB if it exists
        stmt = select(SystemDB).where(SystemDB.system_address == station.system_address)
        res = session.exec(stmt)
        system_db = res.one_or_none()

        # Stop if the system does not exist in the DB
        if system_db is None:
            return

        # Get the station from the DB if it exists
        stmt = select(StationDB).where(StationDB.market_id == station.market_id)
        res = session.exec(stmt)
        station_db = res.one_or_none()

        if station_db:
            station_update = station.update_datetime.replace(tzinfo=UTC)
            station_db_update = station_db.update_datetime.replace(tzinfo=UTC)
            if station_update > station_db_update:
                station_db = station_db | station_data
                station_db.system_id = system_db.system_id  # type: ignore
            else:
                return
        else:
            station_db = StationDB(
                system_id=system_db.system_id,  # type: ignore
                **station_data,
            )

        session.add(station_db)
        session.commit()


def create_update_station_market(market: StationMarket):

    with Session(engine) as session:
        # Get the parent station from the DB
        stmt = select(StationDB).where(StationDB.market_id == market.market_id)
        res = session.exec(stmt)
        station_db = res.one_or_none()

        # Stop if the station does not exist in the DB
        if station_db is None:
            return

        market_update = market.update_datetime.replace(tzinfo=UTC)
        station_market_update = station_db.market_update_datetime
        if (
            station_market_update is None
            or market_update > station_market_update.replace(tzinfo=UTC)
        ):
            existing_commodities = {c.name: c for c in station_db.market_commodities}
            commodities = []

            for commodity in market.commodities:
                if commodity.name in existing_commodities:
                    commodities.append(
                        existing_commodities[commodity.name] | commodity.model_dump()
                    )
                else:
                    commodities.append(
                        MarketCommodityDB(
                            station_id=station_db.station_id,  # type: ignore
                            **commodity.model_dump(),
                        )
                    )

            station_db.market_update_datetime = market.update_datetime
            station_db.market_commodities = commodities

            session.add(station_db)
            session.commit()
