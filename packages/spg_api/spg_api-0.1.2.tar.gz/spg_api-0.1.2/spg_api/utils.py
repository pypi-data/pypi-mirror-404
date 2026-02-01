import pandas as pd
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import sys
import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def getResponse(url: str):
    """
    A refined version of requests.get()
    """
    import spg_api

    # Use package-level credits if set, otherwise fall back to environment variables
    user = spg_api.username or os.getenv("CONNECT_KEY")
    pw = spg_api.password or os.getenv("CONNECT_PW")

    if not user or not pw:
        print("Error: S&P Global credentials not found.")
        print(
            "Please set them via spg_api.username/password or in a .env file (CONNECT_KEY/CONNECT_PW)"
        )
        sys.exit(1)

    auth = requests.auth.HTTPBasicAuth(user, pw)

    # if icona:
    #     headers = {
    #         "accept": "application/json",
    #         "icona-auth-key": TOKEN.ICONA_KEY,
    #         "User-Agent": "PostmanRuntime/7.26.8",
    #     }
    # else:
    headers = {
        "Accept": "application/json",
        # 'Authorization': AUTH,
        "User-Agent": "PostmanRuntime/7.26.8",
    }

    try:
        # response = requests.request("GET", url, headers=headers, params=params)
        # if icona:
        #     response = requests.request(
        #         "GET", url, headers=headers, timeout=1000, verify=False
        #     )
        # else:
        response = requests.get(
            url=url,
            headers=headers,
            auth=auth,
            stream=True,
            timeout=1000,
            verify=False,
        )
        # return response
        reqIsJson = False
        reqIsPdf = False

        headers_dict = response.headers or {}
        content_type = headers_dict.get("content-type", "")

        if "application/json" in content_type:
            reqIsJson = True

        if "application/pdf" in content_type:
            reqIsPdf = True

        if response.status_code == 200:
            return response

        print("Status Code: " + str(response.status_code))

        if response.status_code == 400:
            print(
                "The server could not understand your request, check the syntax for your query."
            )
            print("Error Message: " + str(response.json()))
        elif response.status_code == 401:
            print("Login failed, please check your user name and password.")
        elif response.status_code == 403:
            print("You are not entitled to this data.")
        elif response.status_code == 404:
            print(
                "The URL you requested could not be found or you have an invalid view name."
            )
        elif response.status_code == 500:
            print(
                "The server encountered an unexpected condition which prevented it from fulfilling the request."
            )
            print("Error Message: " + str(response.json()))
            print("If this persists, please contact customer care.")
        else:
            print("Error Message: " + str(response.json()))

        sys.exit()

    except Exception as err:
        print("An unexpected error occurred")
        print("Error Message: {0}".format(err))
        sys.exit()


def response_to_dataframe(response):
    """
    convert the returned json data into pandas dataframe
    """
    elements = {"elements", "Elements", "element", "Element"}

    response_json = response.json()
    json_lists = []

    # get the list of the json files
    if isinstance(response_json, list):
        json_lists = response_json
    elif isinstance(response_json, dict):
        # Find if any of the keys match our expected element containers
        matches = list(set(response_json.keys()).intersection(elements))
        if matches:
            json_lists = response_json.get(matches[0])
        else:
            # If no container found, return raw JSON (e.g. for count endpoints)
            return response_json
    else:
        return response_json

    if not json_lists:
        return pd.DataFrame()

    df = pd.DataFrame()
    try:
        # Check if json_lists is indeed a list of dicts/records
        if isinstance(json_lists, list):
            for entry in json_lists:
                s = pd.Series(entry)
                df = pd.concat([df, s], axis=1)
            df = df.T
        else:
            # If it's something else, return the raw data
            return response_json
    except Exception:
        return response_json

    return df


def get_response_in_dataframe(url: str):
    response = getResponse(url)
    dataframe = response_to_dataframe(response)

    return dataframe


def writeToExcel(
    df: pd.DataFrame, excel_file_path: str, sheet_name: str, index=False
) -> None:
    """
    df: dataframe to be saved
    excel_file_path: the path of the excel file
    sheet_name: the sheet name of the excel file

    Append an df to an existing Excel file
    """
    df.columns = df.columns.astype(str)  # ensure all columns are string
    # Check if the file exists
    dict_data = {}
    if os.path.exists(excel_file_path):
        # if the file already exist, read the files:
        dict_data = pd.read_excel(excel_file_path, sheet_name=None)
        dict_data[sheet_name] = df
    else:
        dict_data[sheet_name] = df

    with pd.ExcelWriter(excel_file_path) as writer:
        for sheet_name, df in dict_data.items():
            df.to_excel(
                writer, sheet_name=sheet_name, startrow=0, startcol=0, index=index
            )
            worksheet = writer.sheets[sheet_name]
            # Define the range of the table (adjusting for Excel's 1-based indexing)
            (max_row, max_col) = df.shape
            column_settings = [{"header": column} for column in df.columns]

            # Add a table to the worksheet
            worksheet.add_table(
                0,
                0,
                max_row,
                max_col - 1,
                {"columns": column_settings, "style": "Table Style Light 1"},
            )
            file = os.path.basename(excel_file_path)
    print(f"{sheet_name} is saved in Excel: {file}")


def read_data_from_excel(folder: str, file: str):
    return pd.read_excel(os.path.join(folder, file))
