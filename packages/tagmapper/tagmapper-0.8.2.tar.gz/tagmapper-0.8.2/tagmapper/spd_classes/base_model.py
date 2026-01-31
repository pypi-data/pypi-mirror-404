from abc import ABC
from tagmapper.connector_api import get_api_client
import pandas as pd
from typing import Optional, List

from tagmapper.generic_model import Attribute


class Base(ABC):
    def __init__(self, ui: str):
        self._attributes = []
        self._header = pd.DataFrame()
        self._ui = ui

    def __eq__(self, value: "Base") -> bool:
        if type(self) is not type(value):
            return False
        return (
            self.functional_location.casefold() == value.functional_location.casefold()
            and self.tag_no.casefold() == value.tag_no.casefold()
            and self.ioc_name.casefold() == value.ioc_name.casefold()
            and self.ui.casefold() == value.ui.casefold()
            and len(self.attribute) == len(value.attribute)
            and all(
                self.attribute[i] in value.attribute for i in range(len(self.attribute))
            )
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}(ui={self.ui})"

    @property
    def ui(self) -> str:
        return self._ui

    @property
    def attribute(self) -> List[Attribute]:
        raise NotImplementedError("Subclasses must implement 'attribute' property")

    @property
    def functional_location(self) -> str:
        header_data = type(self).get_header(self.ui)
        if header_data.empty:
            return ""
        return getattr(
            header_data.to_dict(orient="records")[0], "sap_functional_location", ""
        )

    @property
    def ioc_name(self) -> str:
        header_data = type(self).get_header(self.ui)
        if header_data.empty:
            return ""
        return getattr(header_data.to_dict(orient="records")[0], "ioc_name", "")

    @property
    def tag_no(self) -> str:
        header_data = type(self).get_header(self.ui)
        if header_data.empty:
            return ""
        return getattr(
            header_data.to_dict(orient="records")[0],
            "stid_tag_number",
            getattr(header_data.to_dict(orient="records")[0], "stid_tag", ""),
        )

    @classmethod
    def get_header(cls, ui: Optional[str] = None) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement 'get_header' method")

    @classmethod
    def get_attributes(cls, ui: Optional[str] = None) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement 'get_attributes' method")

    @classmethod
    def get_object_names(cls, facility: str = "") -> List[str]:
        raise NotImplementedError("Subclasses must implement 'get_object_names' method")

    @classmethod
    def get_objects(cls, facility: str = ""):
        return [cls(ui) for ui in cls.get_object_names(facility=facility)]


def get_data_base_well(
    facility_names: Optional[List[str]] = None, limit: int = 10, offset: int = 0
) -> pd.DataFrame:
    if facility_names is None:
        facility_names = []

    query_params = []
    for name in facility_names:
        query_params.append(f"gov_fcty_name={name.replace(' ', '%20')}")

    query_params.append(f"limit={limit}")
    query_params.append(f"offset={offset}")
    query_string = "&".join(query_params)

    url = f"/well-attributes-mapped-to-timeseries-base?{query_string}"
    response = get_api_client().get_json(url)
    df = pd.DataFrame(response["data"])
    return df


def get_data_base_separator(
    facility_names: Optional[List[str]] = None, limit: int = 10, offset: int = 0
) -> pd.DataFrame:
    if facility_names is None:
        facility_names = []

    query_params = []
    for name in facility_names:
        query_params.append(f"gov_fcty_name={name.replace(' ', '%20')}")

    query_params.append(f"limit={limit}")
    query_params.append(f"offset={offset}")
    query_string = "&".join(query_params)

    url = f"/separator-attributes-mapped-to-timeseries-base?{query_string}"
    response = get_api_client().get_json(url)
    df = pd.DataFrame(response["data"])
    return df
