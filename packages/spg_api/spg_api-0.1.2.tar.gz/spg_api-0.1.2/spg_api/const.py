import datetime
import os
import requests
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from dotenv import load_dotenv

load_dotenv()
# from .utils.tools import get_excel_path


# define the paths used -----------------------------------------------------------------------------
class paths:
    """
    A class that defines and manages file system paths used in the CCUS project.

    This class handles path configuration for:
    - Current working directory
    - Database folder location
    - Output folder location
    - Map output location

    Methods:
        get_excel_path(): Locates the Excel file path for CCUS data

    Attributes:
        CURRENT_FOLDER (str): Path to current working directory
        DATABASE_FOLDER (str): Path to database folder containing Excel files
        OUTPUT_FOLDER (str): Path to output folder for generated files
        MAP_OUTPUT (str): Path to map output folder
    """

    research_topic = "Foreign companies in China_2025"

    def __init__(self) -> None:
        self.CURRENT_FOLDER = os.getcwd()
        # self.INSIGHTS_FOLDER = os.path.join(os.path.dirname(self.CURRENT_FOLDER),"10_Insight Memos")
        # self.RESEARCH_TOPIC_FOLDER = os.path.join(self.INSIGHTS_FOLDER,self.research_topic)
        # self.OUTPUT_FOLDER = os.path.join(self.CURRENT_FOLDER,'output')
        # self.MAP_OUTPUT =os.path.join(self.OUTPUT_FOLDER,'maps')


# FILE_PATH = os.getcwd()


# time stamps use in file names -----------------------------------------------------------------------
class timestamps:

    def __init__(self) -> None:
        self.timestamp_for_file_name = datetime.datetime.strftime(
            datetime.datetime.now(), "%Y%m%d-%H%M"
        )
        self.timestampnn = datetime.datetime.strftime(
            datetime.datetime.now(), "%Y%m%d-%H%M%S"
        )
        self.date_hour = datetime.datetime.strftime(
            datetime.datetime.now(), "%b%d-%H:%M"
        )
        self.dateStamp = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
        self.timestamp_for_archive = datetime.datetime.strftime(
            datetime.datetime.now(), "%d%b%Y"
        )


# API keys -------------------------------------------------------------------------------------------
class tokens:

    def __init__(self) -> None:

        # S&P Tokens
        self.CONNECT_KEY = os.getenv("CONNECT_KEY")
        self.CONNECT_PW = os.getenv("CONNECT_PW")
        # self.ICONA_KEY = os.getenv("ICONA_KEY")
        self.CONNECT_AUTH = requests.auth.HTTPBasicAuth(
            os.getenv("CONNECT_KEY"), os.getenv("CONNECT_PW")
        )
        # self.SNOWFLAKE_ID = os.getenv("SNOWFLAKE_ID")
        # self.SNOWFLAKE_KEY = os.getenv("SNOWFLAKE_KEY")
        # self.SPARK_APP_ID = os.getenv("SPARK_APP_ID")
        # self.SPARK_API_KEY = os.getenv("SPARK_API_KEY")
        # self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        # self.POWERTRAIN_TOKEN = os.getenv("POWERTRAIN_TOKEN")
        # self.CI_API_KEY = os.getenv("CI_API_KEY")

        # # External tokens
        # self.GEMINI_API_KEY = os.getevn("GEMINI_API_KEY")
        # self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        # self.QWEN_API_KEY = os.getenv("QWEN_API_KEY")
        # self.QWEN_API_KEY_CODING = os.getenv("QWEN_API_KEY_CODING")


# settings ===========================================================================================


# config the colors used in matplotlib
# SPG standard color pallet ----------------------------------------------------------------------------
class lists:

    def __init__(self) -> None:
        self.SPG_COLORS = [
            "#006D89",
            "#F1A649",
            "#782080",
            "#54BAA0",
            "#B92051",
            "#AAB5DF",
            "#1D3BAA",
            "#B280B6",
            "#C94100",
            "#6DACBC",
            "#501555",
            "#CD6083",
            "#125E1F",
            "#9DCEA6",
            "#9D5700",
            "#E8AE92",
            "#00495B",
            "#EC8200",
            "#6B0F01",
            "#566CBF",
        ]
        self.YEAR_RANGE = list(
            range(1972, 2040)
        )  # used for generating annual addition chart


# folium map styles ======================================
def style_function(feature):
    return {
        # 'color': LISTS.SPG_COLORS[5],       # Line color (e.g., 'blue', 'green', etc.)
        "color": "red",  # Line color (e.g., 'blue', 'green', etc.)
        "weight": 3,  # Line weight (thickness)
        "opacity": 0.7,  # Line opacity (0.0 to 1.0)
        # 'dashArray': '5, 5'    # Dashes in the line (optional)
    }


# Create a highlight function for mouseover effects
def highlight_function(feature):
    return {
        "color": "red",  # Highlight color
        "weight": 5,  # Highlight weight
        "opacity": 1.0,  # Highlight opacity
        "dashArray": "5, 5",  # Highlight dash pattern (optional)
    }


PATH = paths()
TIMESTAMP = timestamps()
TOKEN = tokens()
LISTS = lists()
