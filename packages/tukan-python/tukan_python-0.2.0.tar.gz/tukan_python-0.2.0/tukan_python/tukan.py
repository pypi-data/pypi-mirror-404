import logging
import os
import json
from functools import partial, update_wrapper
from io import StringIO
from random import randint
from time import sleep
from typing import Callable, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Tukan:
    def __init__(self, token: Optional[str] = None):
        env_token = os.getenv("API_TUKAN")
        if token is None and not env_token:
            raise ValueError(
                "Token not provided and not found in environment variables"
            )
        self.token = token or env_token
        self.env = "https://client.tukanmx.com/"

    def execute_post_operation(self, payload: dict, source: str):
        target_url = self.env + source
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {self.token}",
        }
        request_partial = wrapped_partial(
            requests.request,
            method="POST",
            url=target_url,
            json=payload,
            headers=headers,
            timeout=20,
        )
        response = self.persistent_request(request_partial)
        if response.status_code < 300:
            message = response.json()
            return message
        elif response.status_code == 403:
            logger.info(f"{response.text}")
            raise Exception("Operation not allowed on admin. Contact administrator!")
        else:
            message = response.text
            return json.loads(message)

    def persistent_request(self, request_partial: Callable):
        attempts = 0
        while attempts < 2:
            try:
                response = request_partial()
                if response.status_code < 300:
                    break
            except Exception as e:
                pass
            attempts += 1
            sleep(randint(3, 5))
        return response

    def all_tables(self, page: int = 1, page_size: int = 2_500) -> list[dict]:
        payload = {
            "resource": "datatable",
            "operation": "view",
            "page": page,
            "page_size": page_size,
        }
        response = self.execute_post_operation(payload, "data/")
        # Filter out tables that should not be indexed (restricted tables)
        tables = [t for t in response["data"] if t.get("should_index", True)]
        return tables

    def get_table(self, table_name: str) -> dict:
        payload = {
            "resource": "datatable",
            "operation": "view",
            "page": "1",
            "page_size": "1",
            "filter_by": {"id": table_name},
        }
        response = self.execute_post_operation(payload, "data/")
        return response["data"][0]

    def does_table_exist(self, table_name: str) -> bool:
        try:
            self.get_table(table_name)
            return True
        except IndexError:
            return False

    def get_table_metadata(self, table_name: str, language="en") -> dict:
        payload = {"data": {"id": table_name, "language": language}}
        response = self.execute_post_operation(payload, "data/metadata/")
        return response

    def does_indicator_ref_exist(self, indicator_ref: str) -> bool:
        indicator_info = self.get_indicator_by_ref(indicator_ref, page_size=1)
        return bool(indicator_info)

    def all_indicators(self, page: int = 1, page_size: int = 2_500) -> list[dict]:
        payload = {
            "resource": "indicator",
            "operation": "view",
            "page": page,
            "page_size": page_size,
        }
        response = self.execute_post_operation(payload, "data/")
        return response["data"]

    def all_indicators_for_table(
        self, table_name: str, page: int = 1, page_size: int = 2_500
    ) -> list[dict]:
        payload = {
            "resource": "indicator",
            "operation": "view",
            "page": page,
            "page_size": page_size,
            "filter_by": {"data_table": table_name},
        }
        response = self.execute_post_operation(payload, "data/")
        return response["data"]

    def get_indicator_by_ref(
        self, indicator_ref: str, page: int = 1, page_size: int = 2_500
    ) -> dict:
        payload = {
            "resource": "indicator",
            "operation": "view",
            "page": page,
            "page_size": page_size,
            "filter_by": {"ref": indicator_ref},
        }
        response = self.execute_post_operation(payload, "data/")
        return response["data"][0]

    def ask_leah(self, query: str, language: str = "en") -> dict:
        payload = {"query": query, "language": language}
        response = self.execute_post_operation(payload, "leah/")
        parsed_response = parse_leah(response)
        return parsed_response

    def get_saved_query_with_query_name(self, query_name: str) -> list[dict]:
        BODY = {
            "resource": "query",
            "operation": "view",
            "filter_by": {"name": query_name},
            "page_size": 10_000,
        }

        response = self.execute_post_operation(BODY, "visualizations/queries")
        return response["data"]

    def get_query_from_id(self, query_id: str) -> dict:
        BODY = {
            "resource": "query",
            "operation": "view",
            "id": query_id,
        }

        response = self.execute_post_operation(BODY, "visualizations/queries")
        data = response["data"]
        query = next(x for x in data if x["id"] == query_id)
        return query

    def get_reference_flat_tree(
        self, table_name: str, reference: str, only_in_table: bool = False
    ) -> pd.DataFrame:
        """
        Get all available values for a reference (column/category) in a table.

        Args:
            table_name: The table ID
            reference: The reference/column name
            only_in_table: If True, only return values that exist in the data

        Returns:
            DataFrame with columns: raw, ref, name, name_en, parent_ref, order, in_table
        """
        url = f"{self.env}data/visualizations/flat-tree/{table_name}/{reference}/?export=csv"
        headers = {
            "Authorization": f"token {self.token}",
        }
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code >= 300:
            raise Exception(f"Failed to get reference values: {response.text}")

        # Decode response with proper encoding (API returns UTF-8 but sometimes needs fixing)
        text = response.content.decode("utf-8")
        df = pd.read_csv(StringIO(text), sep="|")
        if only_in_table:
            df = df[df["in_table"] == True]
        return df


def wrapped_partial(func, *args, **kwargs) -> Callable:
    partial_func = partial(func, *args, **kwargs)
    update_wrapper(partial_func, func)
    return partial_func


def parse_leah(response: dict) -> dict:
    ans = []
    for element in response["openai_completion"]:
        table_metadata = element["metadata"]["data_table"]
        ans.append(
            {
                "id": table_metadata["id"],
                "description": table_metadata["description"],
                "name": table_metadata["name"],
            }
        )
    return ans
