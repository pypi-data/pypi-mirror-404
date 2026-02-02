from typing import Literal, Optional

import pandas as pd

from tukan_python.tukan import Tukan


class Query:

    def __init__(
        self,
        token: Optional[str] = None,
        table_name: Optional[str] = None,
        where: Optional[list[dict]] = None,
        group_by: Optional[list[dict]] = None,
        aggregate: Optional[list[dict]] = None,
        language: str = "en",
        engine: Optional[Literal["air", "blizzard"]] = None,
    ):
        self.Tukan = Tukan(token)
        self.table_name = table_name
        self.where = where if where is not None else []
        self.group_by = group_by if group_by is not None else []
        self.aggregate = aggregate if aggregate is not None else []
        self.language = language
        self.engine = engine

    def set_table_name(self, table_name: str) -> None:
        self.table_name = table_name

    def set_where(self, where: list[dict]) -> None:
        self.where = where

    def add_date_filter(
        self, reference: str, date_from: str, date_to: Optional[str] = None
    ) -> None:
        dt_filter = {"reference": reference, "from": date_from}
        if date_to is not None:
            dt_filter["to"] = date_to
        self.where.append(dt_filter)

    def add_numeric_filter(
        self,
        reference: str,
        lte: Optional[float] = None,
        eq: Optional[float] = None,
        gte: Optional[float] = None,
    ) -> None:
        self.validate_numeric_filter(lte, eq, gte)
        nm_filter = {"reference": reference, "lte": lte, "eq": eq, "gte": gte}
        nm_filter = {k: v for k, v in nm_filter.items() if v is not None}
        self.where.append(nm_filter)

    def validate_numeric_filter(
        self,
        lte: Optional[float] = None,
        eq: Optional[float] = None,
        gte: Optional[float] = None,
    ) -> None:
        if eq is None and lte is None and gte is None:
            raise ValueError("At least one of eq, lte, or gte must be specified")
        elif eq is not None and (lte is not None or gte is not None):
            raise ValueError("The eq parameter cannot be used with lte or gte")

    def add_standard_filter(self, reference: str, value: list[str]) -> None:
        self.where.append({"reference": reference, "value": value})

    def set_group_by(self, group_by: list[dict]) -> None:
        self.group_by = group_by

    def add_non_date_reference_to_group_by(self, reference: str) -> None:
        self.group_by.append({"reference": reference})

    def add_date_reference_to_group_by(
        self, reference: str, level: Literal["yearly", "quarterly", "monthly", "as_is"]
    ) -> None:
        self.validate_date_filter(level)
        dt_filter = {"reference": reference, "level": level}
        self.group_by.append(dt_filter)

    def validate_date_filter(
        self, level: Literal["yearly", "quarterly", "monthly", "as_is"]
    ) -> None:
        if level not in {"yearly", "quarterly", "monthly", "as_is"}:
            raise ValueError(
                "Invalid level. Must be 'yearly', 'quarterly', 'monthly', or 'as_is'"
            )

    def set_aggregate(self, aggregate: list[dict]) -> None:
        self.aggregate = aggregate

    def add_aggregate(self, indicator: str, operations: list[str]) -> None:
        self.validate_aggregate(operations)
        self.aggregate.append({"indicator": indicator, "operations": operations})

    def validate_aggregate(self, operations: list[str]) -> None:
        if len(operations) == 0:
            raise ValueError("At least one operation must be specified")
        elif {*operations} - {"sum", "avg", "identity"}:
            raise ValueError("Invalid operation. Must be 'sum', 'avg', or 'identity'")

    def set_language(self, language: str) -> None:
        self.language = language

    def set_engine(self, engine: Literal["air", "blizzard"]) -> None:
        self.engine = engine

    def get_select(self) -> list[dict]:
        indicators = [x["indicator"] for x in self.aggregate]
        return [{"table": self.table_name, "indicators": indicators}]

    def get_iterate(self) -> list[dict]:
        return [{"group_by": self.group_by, "aggregate": self.aggregate}]

    def __str__(self) -> str:
        return str(self.__request_payload__())

    def __request_payload__(self) -> dict:
        payload = {
            "select": self.get_select(),
            "where": self.where,
            "iterate": self.get_iterate(),
            "language": self.language,
        }
        if self.engine is not None:
            payload["engine"] = self.engine
        return payload

    def create_identity_query_for_table(
        self, table_name: str, language: Literal["en", "es"]
    ) -> dict:
        self.set_table_name(table_name)
        self.set_identity_aggregate_for_indicators(table_name)
        self.set_language(language)
        self.set_groupby_for_all_columns(table_name)

    def create_identity_query_for_table_with_date_filters(
        self,
        table_name: str,
        language: Literal["en", "es"],
        from_date: str,
        to_date: str,
    ) -> dict:
        self.create_identity_query_for_table(table_name, language)
        date_refs = self.all_dt_references_for_table(table_name)
        for date_ref in date_refs:
            self.add_date_filter(date_ref, from_date, to_date)

    def all_dt_references_for_table(self, table_name: str) -> list[str]:
        metadata = self.Tukan.get_table_metadata(table_name, language="en")
        date_refs = metadata["data_table"]["date_ranges"].keys()
        return [*date_refs]

    def set_identity_aggregate_for_indicators(self, table_name: str) -> None:
        all_indicators = self.all_indicators_for_table(table_name)
        self.aggregate = [
            {"indicator": indicator, "operations": ["identity"]}
            for indicator in all_indicators
        ]

    def set_groupby_for_all_columns(self, table_name: str) -> None:
        references = self.all_references_for_table(table_name)
        group_by = [{"reference": reference} for reference in references]
        self.set_group_by(group_by)

    def all_references_for_table(self, table_name: str) -> list[str]:
        return self.Tukan.get_table(table_name)["references"]

    def all_indicators_for_table(self, table_name: str) -> list[str]:
        all_indicators = self.Tukan.all_indicators_for_table(table_name)
        all_indicators = [indicator["ref"] for indicator in all_indicators]
        return all_indicators

    def save_query(self, name: str) -> str:
        BODY = {
            "data_table": self.table_name,
            "language": self.language,
            "name": name,
            "query": self.__request_payload__(),
        }

        response = self.Tukan.execute_post_operation(BODY, "visualizations/query/")

        return response

    def execute_query(
        self, mode: Literal["vertical", "horizontal"] = "vertical"
    ) -> dict:
        payload = self.__request_payload__()
        payload["mode"] = mode
        response = self.Tukan.execute_post_operation(payload, "data/new_retrieve/")
        df = pd.DataFrame(response["data"])
        return {"indicators": response["indicators"], "df": df}
