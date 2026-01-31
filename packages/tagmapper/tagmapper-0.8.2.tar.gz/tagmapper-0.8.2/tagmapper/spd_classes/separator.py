from typing import List
from commonlib_reader import Facility
import pandas as pd

from tagmapper.connector_api import get_api_client
from tagmapper.generic_model import Attribute
from tagmapper.mapping import Timeseries
from tagmapper.spd_classes.base_model import Base


class Separator(Base):
    """
    Separator class
    """

    _sep_attributes = pd.DataFrame()
    _sep_header = pd.DataFrame()

    def __init__(self, usi):
        if isinstance(usi, str):
            data = Separator.get_attributes(usi)
        elif isinstance(usi, pd.DataFrame):
            if usi.empty:
                raise ValueError("Input dataframe is empty")
            data = usi
            usi = data["unique_separator_identifier"].values[0]
        else:
            raise ValueError("Input usi must be a string or a dataframe")

        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a dataframe")

        if data.empty:
            if isinstance(usi, str):
                raise ValueError(f"No data found for {usi}")
            else:
                raise ValueError("Invalid input, empty dataframe provided.")

        super().__init__(ui=usi)

        for _, r in data.iterrows():
            self._attributes.append(r.to_dict())

    @property
    def usi(self) -> str:
        return self._ui

    @property
    def attribute(self) -> list[Timeseries]:
        attributes = []
        for attr in self._attributes:
            attr["identifier"] = getattr(attr, "attribute_identifier", "")
            attr["alias"] = getattr(attr, "attribute_alias", "")
            attr["description"] = getattr(attr, "attribute_description", "")

            # attribute name is not included in api data
            att = Attribute(
                name=getattr(
                    attr, "attribute_name", getattr(attr, "attribute_identifier", "")
                ),
                data=attr,
            )
            att.add_mapping(Timeseries(data=attr))
            attributes.append(att)

        return attributes

    @classmethod
    def get_separators(cls, facility: str = "") -> List["Separator"]:
        return Separator.get_objects(facility=facility)

    @classmethod
    def get_separator(cls, inst_code: str, tag_no: str) -> "Separator":
        raise NotImplementedError(
            "No header table exist for separators yet, not able to get sap fl from inst_code"
        )
        return Separator(Separator.get_attributes(f"{inst_code}-{tag_no}"))

    @classmethod
    def get_object_names(cls, facility: str = "") -> List[str]:
        """
        Get list of unique separator identifiers.

        Returns:
            List[str]: List of unique separator identifiers.
        """
        return cls.get_usi(facility=facility)

    @classmethod
    def get_usi(cls, facility: str = "") -> List[str]:
        df_attributes = cls.get_attributes()
        if facility != "":
            fac = Facility(facility)
            ind = df_attributes["gov_fcty_name"] == fac.resolve_gov_facility_name()
            if any(ind):
                return sorted(set(df_attributes["unique_separator_identifier"][ind]))
            else:
                return []
        return sorted(set(df_attributes["unique_separator_identifier"]))

    @classmethod
    def get_attributes(cls, upi: str = ""):
        if cls._sep_attributes.empty:
            data = get_api_client().get_json(
                url="/separator-attributes-mapped-to-timeseries-all",
                params={"limit": 100000},
            )
            if isinstance(data, dict) and "data" in data.keys():
                cls._sep_attributes = pd.DataFrame(data=data["data"])
            else:
                raise ValueError("No data found from API for separator attributes")

        if upi:
            ind = cls._sep_attributes["unique_separator_identifier"] == upi
            return cls._sep_attributes[ind]

        return cls._sep_attributes

    @classmethod
    def get_header(cls, upi: str = ""):
        if cls._sep_header.empty:
            param = {"limit": 100000}
            data = get_api_client().get_json(url="/separator-master", params=param)
            if isinstance(data, dict) and "data" in data.keys():
                cls._sep_header = pd.DataFrame(data=data["data"])
            else:
                raise ValueError("No data found from API for separator master")

        if upi:
            ind = cls._sep_header["unique_separator_identifier"] == upi
            return cls._sep_header[ind]

        return cls._sep_header
