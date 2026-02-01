"""
This module includes sample analysis with the S&P Global Connect API.
"""

from .url_generator import SPGlobalAPIClient
from typing import Optional, List
import pandas as pd
import matplotlib.pyplot as plt

from . import spg_style

STYLE = spg_style.SpglobalStyle(theme="light")


class ScenariosAnalysis(SPGlobalAPIClient):
    """
    The available views are:
    - coal_markets
    - employment
    - final_energy_consumption
    - gdp
    - geohierarchy
    - ghg_emissions
    - ghgsectorshierarchy
    - ghgsourcehierarchy
    - natural_gas_markets
    - oil_consumption_by_product
    - oil_consumption_by_sector
    - population_by_age
    - population_urban_rural
    - power_markets_by_technology
    - power_markets_demand
    - primary_energy_demand
    - sectorcoalhierarchy
    - sectorgashierarchy
    - sectorhierarchy
    - sectoroilhierarchy

    scenarios:
    ['CI Base Case', 'Renaissance', 'Fracture', 'Adaptation', 'Net-Zero 2050']
    """

    DATASET = "energyandclimatescenarios"

    def __init__(self):
        super().__init__(self.DATASET)

    @property
    def views(self):
        return self.get_views().iloc[:, 0].to_list()

    def emission_comparison(self, country_list: Optional[List[str]] = None):
        if country_list is None:
            country_list = [
                "Australia",
                "China (mainland)",
                "India",
                "Japan",
                "Mexico",
                "Russia",
                "South Korea",
                "United States",
                "Brazil",
                "Canada",
                "France",
                "Germany",
                "Indonesia",
                "Saudi Arabia",
                "United Kingdom",
            ]

        all_data = []
        print(f"Retrieving data for {len(country_list)} countries...")

        for country in country_list:
            df = self.retrieve_data(
                view_name="ghg_emissions",
                select=["country", "year", "value"],
                filters={
                    "scenario": "CI Base Case",
                    "country": country,
                    "ccus_savings": "Including CCUS",
                },
            )
            if not df.empty:
                all_data.append(df)

        if not all_data:
            print("No data found for the specified countries and scenario.")
            return pd.DataFrame()

        final_df = pd.concat(all_data, ignore_index=True)

        fig, ax = plt.subplots(figsize=spg_style.get_edp_figsize())
        df_pivot = final_df.pivot_table(
            index="year", columns="country", values="value", aggfunc="sum"
        )
        df_pivot.plot(ax=ax, legend=True)

        plt.title("GHG Emissions Comparison (CI Base Case)")
        plt.xlabel("Year")
        plt.ylabel("GHG Emissions (MtCO2)")

        STYLE.apply_legend(ax)
        STYLE.add_footnotes(fig, source="S&P Global")
        plt.show()

        return df_pivot


class EdinAnalysis(SPGlobalAPIClient):
    """
    The available views are:
    """

    DATASET = "eandp"

    def __init__(self):
        super().__init__(self.DATASET)

    @property
    def views(self):
        return self.list_views().iloc[:, 0].to_list()


class CompanyAnalysis(SPGlobalAPIClient):
    """
    The available views are:

    """

    DATASET = "ep-portfolio"
