"""Tibber lowest night price."""

from datetime import timedelta

from typing import Optional, Union
from collections.abc import Callable

from .const import DOMAIN

import pandas as pd

from homeassistant import core, config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.util import dt as dt_util
import voluptuous as vol

# import logging
# _LOGGER = logging.getLogger(__name__)


CONF_START = "start"
CONF_END = "end"
CONF_SIZE = "size"
CONF_PERIODS = "periods"

PERIOD_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.positive_int,
        vol.Required(CONF_START): cv.positive_int,
        vol.Required(CONF_END): cv.positive_int,
        vol.Required(CONF_SIZE): cv.positive_int,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PERIODS): vol.All(cv.ensure_list, [PERIOD_SCHEMA]),
    }
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    sensors = []
    for home in hass.data["tibber"].get_homes(only_active=True):
        sensors.append(
            TibberLowest(
                home,
                hass,
                identifier=config[CONF_NAME],
                hour_start=config[CONF_START],
                hour_end=config[CONF_END],
                window_size=config[CONF_SIZE],
            )
        )
    async_add_entities(sensors, update_before_add=True)


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    sensors = []
    for home in hass.data["tibber"].get_homes(only_active=True):
        periods = hass.data.get("tibber_lowest", {}).get("periods", [])
        for period in periods:
            sensors.append(
                TibberLowest(
                    home,
                    hass,
                    identifier=period[CONF_NAME],
                    hour_start=period[CONF_START],
                    hour_end=period[CONF_END],
                    window_size=period[CONF_SIZE],
                )
            )
    async_add_entities(sensors, update_before_add=True)


class TibberLowest(BinarySensorEntity):
    def __init__(
        self, home, hass, identifier=None, hour_start=22, hour_end=6, window_size=1
    ):
        super().__init__()
        self._name = home.info["viewer"]["home"]["appNickname"]
        if self._name is None:
            self._name = home.info["viewer"]["home"]["address"].get("address1", "")
        if identifier:
            self._name = f"Lowest electricity price {self._name} - {identifier}"
        self._home = home
        self.hass = hass
        self._cons_data = []
        self._last_update = dt_util.now() - timedelta(hours=1)
        self._state = False
        self._hour_start = hour_start
        self._hour_end = hour_end
        self._window_size = window_size
        self._current_window = None
        self._current_lowest = None

    async def async_update(self):
        now = dt_util.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if (now - self._last_update) < timedelta(minutes=1):
            return

        if (self._home.last_data_timestamp - now).total_seconds() < 11 * 3600:
            await self._home.update_info_and_price_info()

        if self._current_window is None or self._current_window[1] < now:
            self._current_lowest = None
            if now.hour < self._hour_end:
                end_day = today
            else:
                end_day = today + timedelta(days=1)
            if self._hour_start < self._hour_end:
                start_day = end_day
            else:
                start_day = end_day + timedelta(days=-1)
            self._current_window = (
                start_day + timedelta(hours=self._hour_start),
                end_day + timedelta(hours=self._hour_end),
            )

        if (
            self._current_lowest is None
            and self._current_window[1] <= self._home.last_data_timestamp
        ):
            price_data = pd.Series(self._home.price_total)
            price_data.index = pd.to_datetime(price_data.index)
            night_data = price_data[
                (price_data.index >= self._current_window[0])
                & (price_data.index < self._current_window[1])
            ]

            indexer = pd.api.indexers.FixedForwardWindowIndexer(
                window_size=self._window_size
            )

            lowest = (
                night_data.rolling(window=indexer, min_periods=self._window_size)
                .mean()
                .idxmin()
            )
            self._current_lowest = (lowest, lowest + timedelta(hours=self._window_size))

        if (
            self._current_lowest is not None
            and now >= self._current_lowest[0]
            and now < self._current_lowest[1]
        ):
            self._state = True
        else:
            self._state = False

        self._last_update = now

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> Union[str, None]:
        uid = super().unique_id
        return uid

    @property
    def is_on(self) -> Optional[str]:
        return self._state

    # @property
    # def unique_id(self) -> str:
    #    """Return the unique ID of the sensor."""
    #    return self.repo

    # @property
    # def available(self) -> bool:
    #    """Return True if entity is available."""
    #    return self._available

    # @property
    # def device_state_attributes(self) -> Dict[str, Any]:
    #    return self.attrs


#    async def async_update(self):
#        try:
#            repo_url = f"/repos/{self.repo}"
#            repo_data = await self.github.getitem(repo_url)
#            self.attrs[ATTR_FORKS] = repo_data["forks_count"]
#            self.attrs[ATTR_NAME] = repo_data["name"]
#            self.attrs[ATTR_STARGAZERS] = repo_data["stargazers_count"]
#
#            if repo_data["permissions"]["push"]:
#                clones_url = f"{repo_url}/traffic/clones"
#                clones_data = await self.github.getitem(clones_url)
#                self.attrs[ATTR_CLONES] = clones_data["count"]
#                self.attrs[ATTR_CLONES_UNIQUE] = clones_data["uniques"]
#
#                views_url = f"{repo_url}/traffic/views"
#                views_data = await self.github.getitem(views_url)
#                self.attrs[ATTR_VIEWS] = views_data["count"]
#                self.attrs[ATTR_VIEWS_UNIQUE] = views_data["uniques"]
#
#            commits_url = f"/repos/{self.repo}/commits"
#            commits_data = await self.github.getitem(commits_url)
#            latest_commit = commits_data[0]
#            self.attrs[ATTR_LATEST_COMMIT_MESSAGE] = latest_commit["commit"]["message"]
#            self.attrs[ATTR_LATEST_COMMIT_SHA] = latest_commit["sha"]
#
#            # Using the search api to fetch open PRs.
#            prs_url = f"/search/issues?q=repo:{self.repo}+state:open+is:pr"
#            prs_data = await self.github.getitem(prs_url)
#            self.attrs[ATTR_OPEN_PULL_REQUESTS] = prs_data["total_count"]
#            if prs_data and prs_data["items"]:
#                self.attrs[ATTR_LATEST_OPEN_PULL_REQUEST_URL] = prs_data["items"][0][
#                    "html_url"
#                ]
#
#            issues_url = f"/repos/{self.repo}/issues"
#            issues_data = await self.github.getitem(issues_url)
#            # GitHub issues include pull requests, so to just get the number of issues,
#            # we need to subtract the total number of pull requests from this total.
#            total_issues = repo_data["open_issues_count"]
#            self.attrs[ATTR_OPEN_ISSUES] = (
#                total_issues - self.attrs[ATTR_OPEN_PULL_REQUESTS]
#            )
#            if issues_data:
#                self.attrs[ATTR_LATEST_OPEN_ISSUE_URL] = issues_data[0]["html_url"]
#
#            releases_url = f"/repos/{self.repo}/releases"
#            releases_data = await self.github.getitem(releases_url)
#            if releases_data:
#                self.attrs[ATTR_LATEST_RELEASE_URL] = releases_data[0]["html_url"]
#                self.attrs[ATTR_LATEST_RELEASE_TAG] = releases_data[0][
#                    "html_url"
#                ].split("/")[-1]
#
#            # Set state to short commit sha.
#            self._state = latest_commit["sha"][:7]
#            self._available = True
#        except (ClientError, gidgethub.GitHubException):
#            self._available = False
#            _LOGGER.exception("Error retrieving data from GitHub.")
