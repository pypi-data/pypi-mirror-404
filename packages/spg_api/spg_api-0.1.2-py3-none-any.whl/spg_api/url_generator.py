from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Any, Set, List, Tuple, Union
from urllib.parse import urljoin, urlencode, quote
import pandas as pd
from .utils import get_response_in_dataframe


@dataclass(frozen=True)
class BaseURLConfig:
    """
    Configuration schema for S&P Global API clusters.

    This dataclass defines how dynamic URLs and query parameters should be
    constructed for a specific API backend (e.g., Upstream vs. Scenarios).

    Attributes:
        url (str): The base endpoint URL (e.g., 'https://api.connect.spglobal.com/cs/v1/').
        use_dollar_prefix (bool): Whether the API requires OData $ prefixes for
            parameters like $filter, $select, and $top.
        use_boolean_groupby (bool): If True, 'groupby' is sent as a boolean flag
            ('true') and uses fields in 'select' for grouping. If False,
            'groupby' is a list of field names.
        use_multi_filter (bool): If True, multiple filters are sent as separate
            'filter' parameters with trailing commas (required by Scenarios API).
        param_mapping (Dict[str, str]): Optional mapping to override standard
            OData keys (e.g., {'orderby': 'order'}).
    """

    url: str
    use_dollar_prefix: bool
    use_filter_parameter: bool = True
    data_endpoint: str = "retrieve"
    count_endpoint: str = "counts"
    use_boolean_groupby: bool = False
    use_multi_filter: bool = False
    param_mapping: Optional[Dict[str, str]] = None
    field_mapping: Optional[Dict[str, str]] = None


class BaseURL(Enum):
    """
    Enumeration of supported S&P Global API base URL configurations.

    Each member maps to a BaseURLConfig defining the architectural requirements
    of that specific data service.
    """

    UPSTREAM_INSIGHT = BaseURLConfig(
        "https://api.connect.spglobal.com/energy/v1/upstream/",
        use_dollar_prefix=True,
        use_filter_parameter=True,
        count_endpoint="counts",
    )
    UPSTREAM_INSIGHT_IHS = BaseURLConfig(
        "https://api.connect.ihsmarkit.com/energy/v1/upstream/",
        use_dollar_prefix=True,
        use_filter_parameter=True,
        count_endpoint="counts",
    )

    GAS_POWER_CLIMATE = BaseURLConfig(
        "https://api.connect.spglobal.com/cs/v1/",
        use_dollar_prefix=False,
        use_filter_parameter=True,
        count_endpoint="count",
        use_boolean_groupby=True,
    )
    SCENARIOS = BaseURLConfig(
        "https://api.connect.spglobal.com/energy/v1/gpe/",
        use_dollar_prefix=False,
        use_filter_parameter=True,
        count_endpoint="count",
        use_boolean_groupby=True,
        use_multi_filter=True,
        param_mapping={"orderby": "order", "groupby": "groupBy"},
    )
    ENERGY_DATA_SERVICES = BaseURLConfig(
        "https://energydataservices.ci.spglobal.com/data/v1/international/adm/",
        use_dollar_prefix=True,
        use_filter_parameter=True,
        data_endpoint="retrieve",
        count_endpoint="counts",
        field_mapping={"country": "country_names"},
    )
    UPATREAM_INTL_ADM = BaseURLConfig(
        "https://energydataservices.ihsenergy.com/rest/data/v1/international/adm/",
        use_dollar_prefix=True,
        use_filter_parameter=True,
        count_endpoint="counts",
        field_mapping={"country": "country_names"},
    )
    VANTAGE_ASSET_DATA = BaseURLConfig(
        "https://energydataservices.ihsenergy.com/rest/data/v3/",
        use_dollar_prefix=True,
        use_filter_parameter=True,
        count_endpoint="counts",
        field_mapping={"country": "country_names"},
    )


# Dataset registry mapping dataset names to their base URLs
DATASET_REGISTRY: Dict[str, BaseURL] = {
    # Upstream Insight datasets
    "companies_transactions": BaseURL.UPSTREAM_INSIGHT,
    "company_metrics": BaseURL.UPSTREAM_INSIGHT,
    "transactions_assets": BaseURL.UPSTREAM_INSIGHT,
    "peps_ratings": BaseURL.UPSTREAM_INSIGHT,
    "costs_supply_chain": BaseURL.UPSTREAM_INSIGHT,
    "plays_basins": BaseURL.UPSTREAM_INSIGHT,
    "upstream-deals": BaseURL.UPSTREAM_INSIGHT,
    "upstream-assets": BaseURL.UPSTREAM_INSIGHT,
    "upstream-companies": BaseURL.UPSTREAM_INSIGHT,
    "ep-portfolio": BaseURL.UPSTREAM_INSIGHT_IHS,  # a lot of functions cannot be applied to this dataset
    # Legacy/Energy Data Services
    "eandp": BaseURL.ENERGY_DATA_SERVICES,  # EDIN data
    "basin": BaseURL.UPATREAM_INTL_ADM,  # EDIN basin data
    "international-adm": BaseURL.ENERGY_DATA_SERVICES,
    "assetvaluation": BaseURL.VANTAGE_ASSET_DATA,  # Vantage data
    "enhancedemissions": BaseURL.VANTAGE_ASSET_DATA,  # Vantage emissions data
    # Gas, Power and Climate Solutions datasets (Connect REST APIs)
    "ceta": BaseURL.GAS_POWER_CLIMATE,
    "corporate-emissions": BaseURL.GAS_POWER_CLIMATE,
    "energyandclimatescenarios": BaseURL.SCENARIOS,
    "climate-scenarios": BaseURL.GAS_POWER_CLIMATE,
    "fastlmp": BaseURL.GAS_POWER_CLIMATE,
    "gas-markets": BaseURL.GAS_POWER_CLIMATE,
    "lng-analytics": BaseURL.GAS_POWER_CLIMATE,
    "lng-markets": BaseURL.GAS_POWER_CLIMATE,
    "power-markets": BaseURL.GAS_POWER_CLIMATE,
    "pointlogic": BaseURL.GAS_POWER_CLIMATE,
    # Legacy/Mapping aliases
    "cleanenergytech": BaseURL.GAS_POWER_CLIMATE,
    "corporateemissions": BaseURL.GAS_POWER_CLIMATE,
    "gasmarkets": BaseURL.GAS_POWER_CLIMATE,
    "lnganalytics": BaseURL.GAS_POWER_CLIMATE,
    "powerrenewables": BaseURL.GAS_POWER_CLIMATE,
}


class SPGlobalAPIClient:
    """
    Unified client for accessing S&P Global Connect and Energy Data APIs.

    This client abstracts the complexity of different API architectures (OData vs REST)
    into a standardized Pythonic interface. It automatically handles URL construction,
    parameter formatting (including dollar prefixes), and response parsing.

    Example:
        >>> client = SPGlobalAPIClient("energyandclimatescenarios")
        >>> df = client.retrieve_data("coal_markets", filters={"CountryCode": "CHN"})
    """

    def __init__(self, dataset_name: str):
        """
        Initializes the client for a specific dataset.

        Args:
            dataset_name (str): The name of the dataset to connect to
                (e.g., 'upstream-deals', 'eandp'). Must exist in DATASET_REGISTRY.

        Raises:
            ValueError: If the dataset_name is not recognized.
        """
        if dataset_name not in DATASET_REGISTRY:
            available = ", ".join(DATASET_REGISTRY.keys())
            raise ValueError(f"Unknown dataset: {dataset_name}. Available: {available}")

        self.dataset_name = dataset_name
        self.config = DATASET_REGISTRY[dataset_name].value
        self.base_url = self.config.url
        self.use_dollar_prefix = self.config.use_dollar_prefix
        self.use_filter_parameter = self.config.use_filter_parameter
        self.data_endpoint = self.config.data_endpoint
        self.count_endpoint = self.config.count_endpoint
        self.use_boolean_groupby = self.config.use_boolean_groupby
        self.use_multi_filter = self.config.use_multi_filter
        self.param_mapping = self.config.param_mapping or {}
        self.field_mapping = self.config.field_mapping or {}

    # --- Internal Helpers ---

    def _map_field(self, field: str) -> str:
        """Applies field name mapping if defined in configuration."""
        if not self.field_mapping:
            return field
        # Handle cases like "Field desc" in orderby
        parts = field.split()
        if parts:
            parts[0] = self.field_mapping.get(parts[0], parts[0])
            return " ".join(parts)
        return field

    def _format_key(self, key: str) -> str:
        """
        Applies OData $ prefix if required by the configuration.

        Args:
            key (str): The parameter name (e.g., 'filter').

        Returns:
            str: The formatted key (e.g., '$filter', 'order', or 'filter').
        """
        # 1. Apply overrides from mapping (e.g., orderby -> order)
        mapped_key = self.param_mapping.get(key, key)

        # 2. Apply OData $ prefix if required
        return f"${mapped_key}" if self.use_dollar_prefix else mapped_key

    def _build_full_url(
        self, path_segments: List[str], params: List[Tuple[str, str]] = None
    ) -> str:
        """
        Constructs the final URL with path segments and encoded query parameters.

        Args:
            path_segments (List[str]): List of URL path parts after the base URL.
            params (List[Tuple[str, str]]): List of query parameters as tuples.

        Returns:
            str: The fully constructed and encoded URL string.
        """
        # Build path: base_url / dataset / segments...
        full_path = "/".join(
            [self.dataset_name] + [s.strip("/") for s in path_segments if s]
        )
        url = urljoin(self.base_url, full_path)

        if params:
            # S&P APIs prefer %20 for spaces and literal characters in OData filters
            # We remove '=' from safe_chars to ensure it's encoded in OData filter values if needed
            safe_chars = ",()'"
            query = urlencode(params, safe=safe_chars, doseq=True, quote_via=quote)
            return f"{url}?{query}"
        return url

    def _execute_request(
        self, path_segments: List[str], params: List[Tuple[str, str]] = None
    ) -> Any:
        """
        Internal dispatcher that builds the URL and triggers the HTTP request.

        Args:
            path_segments (List[str]): URL path components.
            params (List[Tuple[str, str]]): URL query parameters.

        Returns:
            Any: The parsed API response (usually a DataFrame or Dictionary).
        """
        url = self._build_full_url(path_segments, params)
        print(f"Requesting URL: {url}")
        return get_response_in_dataframe(url)

    def _prepare_params(
        self,
        filters: Optional[Any] = None,
        select: Any = None,
        orderby: Any = None,
        groupby: Any = None,
        having: Any = None,
        expand: Any = None,
        page_size: int = None,
        page_index: int = None,
        **kwargs,
    ) -> List[Tuple[str, str]]:
        """
        Transforms high-level function arguments into a standardized list of query parameters.

        This method handles the conversion from Python dictionaries to OData filter strings
        and manages the naming differences for paging parameters (top/skip vs pageSize/pageIndex).

        Args:
            filters (Union[str, dict]): Filtering conditions.
            select (Union[str, List[str]]): Columns to include.
            orderby (Union[str, List[str]]): Sorting instructions.
            groupby (Union[str, List[str]]): Aggregation fields.
            having (str): Post-aggregation filters.
            expand (Union[str, List[str]]): Related entities to include.
            page_size (int): Max records per request.
            page_index (int): Page number to retrieve (0-indexed).
            **kwargs: Additional arbitrary query parameters.

        Returns:
            List[Tuple[str, str]]: Formatted query parameters for the URL.
        """
        params = []

        # 1. Filters processing
        if filters:
            filter_key = self._format_key("filter")
            if isinstance(filters, str):
                params.append((filter_key, filters))
            elif isinstance(filters, dict):
                if self.use_filter_parameter:
                    # OData style
                    if self.use_multi_filter:
                        # Scenarios style: filter=Field1='Val1', &filter=Field2='Val2'
                        items = list(filters.items())
                        for i, (k, v) in enumerate(items):
                            k = self._map_field(k)
                            if isinstance(v, str) and not (
                                v.startswith("'") and v.endswith("'")
                            ):
                                v_str = f"'{v}'"
                            else:
                                v_str = str(v)

                            val = f"{k}={v_str}"
                            # Add trailing comma+space for all items except the very last field
                            if i < len(items) - 1:
                                val += ", "
                            params.append((filter_key, val))
                    else:
                        # Standard OData: filter=Field1='Val1', Field2='Val2'
                        items = []
                        for k, v in filters.items():
                            k = self._map_field(k)
                            if isinstance(v, (list, tuple)):
                                v_items = []
                                for item in v:
                                    if isinstance(item, str) and not (
                                        item.startswith("'") and item.endswith("'")
                                    ):
                                        v_items.append(f"'{item}'")
                                    else:
                                        v_items.append(str(item))
                                v_str = ", ".join(v_items)
                            else:
                                if isinstance(v, str) and not (
                                    v.startswith("'") and v.endswith("'")
                                ):
                                    v_str = f"'{v}'"
                                else:
                                    v_str = str(v)
                            items.append(f"{k}={v_str}")
                        params.append((filter_key, ", ".join(items)))
                else:
                    # individual params style (Legacy EDS)
                    for k, v in filters.items():
                        k_mapped = self._map_field(k)
                        if isinstance(v, str) and not (
                            v.startswith("'") and v.endswith("'")
                        ):
                            v = f"'{v}'"
                        params.append((self._format_key(k_mapped), str(v)))

        # 2. OData Clauses (Select, OrderBy, etc.)
        for key, val in [("select", select), ("orderby", orderby), ("expand", expand)]:
            if val:
                if isinstance(val, (list, tuple)):
                    val = ", ".join([self._map_field(v) for v in val])
                else:
                    # If it's a comma-separated string, split and map
                    if "," in str(val):
                        val = ", ".join(
                            [self._map_field(v.strip()) for v in str(val).split(",")]
                        )
                    else:
                        val = self._map_field(str(val))
                params.append((self._format_key(key), val))

        # 2a. GroupBy handling (List vs Boolean)
        if groupby:
            if self.use_boolean_groupby:
                params.append((self._format_key("groupby"), "true"))
            else:
                if isinstance(groupby, (list, tuple)):
                    groupby = ",".join([self._map_field(v) for v in groupby])
                else:
                    if "," in str(groupby):
                        groupby = ",".join(
                            [
                                self._map_field(v.strip())
                                for v in str(groupby).split(",")
                            ]
                        )
                    else:
                        groupby = self._map_field(str(groupby))
                params.append((self._format_key("groupby"), groupby))

        # 3. Paging parameter normalization
        if page_size is not None:
            key = "pageSize" if not self.use_dollar_prefix else "top"
            params.append((self._format_key(key), str(page_size)))
        if page_index is not None:
            key = "pageIndex" if not self.use_dollar_prefix else "skip"
            params.append((self._format_key(key), str(page_index)))

        # 4. Overflow for custom parameters
        for k, v in kwargs.items():
            if v is not None:
                params.append((self._format_key(k), str(v)))

        return params

    # --- Public API ---

    def list_views(self) -> pd.DataFrame:
        """
        Retrieves the list of all available data views for the current dataset.

        Returns:
            pd.DataFrame: A table containing view names and descriptions.
        """
        return self._execute_request(["views"])

    def get_view_definition(self, view_name: str) -> pd.DataFrame:
        """
        Retrieves the field definitions and metadata for a specific view.

        Args:
            view_name (str): The name of the view (e.g., 'coal_markets').

        Returns:
            pd.DataFrame: Meta-information about columns, data types, and constraints.
        """
        return self._execute_request(["views", view_name])

    def get_schema(self, view_name: str = None) -> pd.DataFrame:
        """
        Retrieves the schema information for the entire dataset or a specific view.

        Args:
            view_name (Optional[str]): If provided, gets the schema for the view.
                Otherwise, gets the dataset schema.

        Returns:
            pd.DataFrame: Schema details.
        """
        segments = ["views", view_name, "schema"] if view_name else ["schema"]
        return self._execute_request(segments)

    def get_count(self, view_name: str, filters: Optional[Any] = None) -> int:
        """
        Returns the total number of records available for a specific view and filter set.

        This is useful for pre-validating request sizes before downloading data.

        Args:
            view_name (str): The target data view.
            filters (Optional[dict]): Conditions to apply to the count query.

        Returns:
            int: The total record count.
        """
        params = self._prepare_params(filters=filters)
        response_data = self._execute_request([self.count_endpoint, view_name], params)
        return self._parse_count_response(response_data)

    def retrieve_data(self, view_name: str, **kwargs) -> pd.DataFrame:
        """
        Primary method to fetch data from a specific API view.

        Supports complex filtering, selection, and pagination.

        Args:
            view_name (str): The target data view.
            **kwargs: Query parameters including:
                - filters (dict): e.g., {'Country': 'China'}
                - select (list): e.g., ['Year', 'Value']
                - orderby (str): e.g., 'Year desc'
                - page_size (int): Limit results.
                - page_index (int): Offset results.

        Returns:
            pd.DataFrame: The requested data.

        Example:
            >>> client.retrieve_data("gdp", filters={'Country': 'China'}, select=['Year', 'Value'])
        """
        params = self._prepare_params(**kwargs)
        return self._execute_request([self.data_endpoint, view_name], params)

    def get_distinct_values(
        self, view_name: str, column_name: str, filters: Optional[dict] = None
    ) -> List[Any]:
        """
        Retrieves unique values for a specific column in a view.

        Uses the OData 'groupby' functionality to perform server-side distinct selection.

        Args:
            view_name (str): The target view.
            column_name (str): The column to get unique values from.
            filters (Optional[dict]): Optional filters to apply before finding unique values.

        Returns:
            List[Any]: A list of unique values in the specified column.

        Example:
            >>> countries = client.get_distinct_values("coal_markets", "Country")
        """
        params = self._prepare_params(
            select=[column_name], groupby=[column_name], filters=filters
        )
        df = self._execute_request([self.data_endpoint, view_name], params)

        if df.empty or column_name not in df.columns:
            return []

        return df[column_name].dropna().unique().tolist()

    def fetch_all(
        self, view_name: str, chunk_size: int = 50000, limit: int = None, **kwargs
    ) -> pd.DataFrame:
        """
        High-level convenience method that automatically handles pagination to retrieve
        large datasets in their entirety.

        This method first checks the total record count and then iterates through
        pages, concatenating the results into a single DataFrame.

        Args:
            view_name (str): The target view name.
            chunk_size (int): Number of records to fetch per iteration. Defaults to 50,000.
            limit (Optional[int]): Cap the total number of records to retrieve.
            **kwargs: Same parameters as retrieve_data (filters, select, etc.).

        Returns:
            pd.DataFrame: Full dataset combined from all pages.

        Example:
            >>> full_df = client.fetch_all("coal_markets", chunk_size=100000)
        """
        total_count = self.get_count(view_name, filters=kwargs.get("filters"))
        if limit:
            total_count = min(total_count, limit)

        print(
            f"Fetching {total_count} records for '{view_name}' in chunks of {chunk_size}..."
        )

        all_dfs = []
        fetched = 0
        page = 0

        while fetched < total_count:
            df = self.retrieve_data(
                view_name, page_size=chunk_size, page_index=page, **kwargs
            )
            if df.empty:
                break
            all_dfs.append(df)
            fetched += len(df)
            page += 1
            print(f"Progress: {fetched}/{total_count} records")

        return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

    def _parse_count_response(self, response_data: Any) -> int:
        """
        Internal parser to extract an integer count from various API response formats.

        Handles cases where the count is returned as a plain number, a dictionary
        entry (e.g., {'count': 10}), or a single-cell DataFrame.
        """
        if isinstance(response_data, (int, float)):
            return int(response_data)
        if isinstance(response_data, str) and response_data.isdigit():
            return int(response_data)

        if isinstance(response_data, dict):
            # Normalizing keys: ignore case and separators
            norm = {
                k.lower().replace("_", "").replace("-", ""): v
                for k, v in response_data.items()
            }
            for key in ["count", "totalcount", "recordcount"]:
                if key in norm:
                    return int(norm[key])
            if len(response_data) == 1:
                val = list(response_data.values())[0]
                if str(val).isdigit():
                    return int(val)
            return 0

        if isinstance(response_data, pd.DataFrame):
            if response_data.empty:
                return 0
            if response_data.shape == (1, 1):
                try:
                    return int(response_data.iloc[0, 0])
                except:
                    pass

            cols = [
                c.lower().replace("_", "").replace("-", "")
                for c in response_data.columns
            ]
            for target in ["count", "totalcount", "recordcount"]:
                if target in cols:
                    return int(response_data.iloc[0, cols.index(target)])
            return response_data.shape[0]

        try:
            return len(response_data)
        except:
            return 0

    @classmethod
    def list_all_datasets(cls) -> list:
        """
        Returns a list of all dataset identifiers registered in the client.

        Returns:
            List[str]: Available dataset keys.
        """
        return list(DATASET_REGISTRY.keys())
