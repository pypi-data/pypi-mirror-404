from dotenv import load_dotenv
import requests
import os
from pathlib import Path

path_root = Path(__file__).resolve().parent
load_dotenv(path_root/'.env')
apikey = os.getenv("SPECIESLINK_APIKEY")
url  = "https://specieslink.net/ws/1.0/search"

def create_params(country: str = None, year_range: tuple = None, lat_min: float = None, lat_max: float = None, lon_min: float = None, lon_max: float = None):
    params = {}
    if(country):
        params["country"] = country
    if(year_range):
        years = range(year_range[0], year_range[1] + 1)
        params["yearCollected"] = f"{','.join(map(str, years))}"
    if(lat_min is not None and lat_max is not None and lon_min is not None and lon_max is not None):
        params["bbox"] = f"{lon_min}+{lat_min}+{lon_max}+{lat_max}"
    return params

def get_occurrences_by_name(species_names: list, country: str = None, year_range: tuple = None, lat_min: float = None, lat_max: float = None, lon_min: float = None, lon_max: float = None): # type: ignore
    """Get occurrences from SpeciesLink by species_names.

    Args: 
        keys (list): List of specie keys.
        country (str, optional): Country code to filter occurrences. Defaults to None.
        year_range (tuple, optional): Year range to filter occurrences (start_year, end_year). Defaults to None.
        """
    params = create_params(country, year_range, lat_min, lat_max, lon_min, lon_max)

    params["scientificname"] = ",".join(species_names)
    params["coordinates"] = "yes"
    if(not apikey):
        raise Exception( "Missing SpeciesLink credentials. "
                        "Call save_specieslink_apikey(apikey: str) "
                        "to configure your account. "
                        "Retrieve your credentials from: https://specieslink.net/aut/profile/apikeys"
                    )
    params["apikey"] = apikey
    
    request = requests.get(url, params=params)
    request.raise_for_status()
    if(request.status_code != 200):
        raise ValueError("SpeciesLink API returned an error")
    data = request.json()
    all_results = []
    for i in data['features']:
        property = i['properties']
        if('daycollected' not in property  or 'monthcollected' not in property ):
            continue
        all_results.append({
            "source": 'speciesLink',
            "scientificName": property['scientificname'],
            "country": str(property['country']).casefold(),
            "latitude": property['decimallatitude'],
            "longitude": property['decimallongitude'],
            "day": property['daycollected'],
            "month": property['monthcollected'],
            "year": property['yearcollected']
        })
    return all_results



def save_specieslink_apikey(
    apikey: str
):
    """
    Saves SpeciesLink API key to a .env file.
    """
    env_path = path_root/'.env'
    print(env_path)
    data = {
        "SPECIESLINK_APIKEY": apikey
    }
    existent_lines  = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existent_lines[k] = v
                    
    existent_lines.update(data)

    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in existent_lines.items():
            f.write(f"{k}={v}\n")

    print("SpeciesLink API key saved to .env file.")

def delete_specieslink_apikey():
    """
    Removes SpeciesLink credentials from a .env file.
    """

    keys_to_remove = {"SPECIESLINK_APIKEY"}

    env_path = path_root/'.env'
    if not os.path.exists(env_path):
        print("No .env file found.")
        return

    existent_lines = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                existent_lines[k] = v

    removed_any = False
    for key in keys_to_remove:
        if key in existent_lines:
            del existent_lines[key]
            removed_any = True

    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in existent_lines.items():
            f.write(f"{k}={v}\n")

    if removed_any:
        print("SpeciesLink credentials removed from .env file.")
    else:
        print("No SpeciesLink credentials found in .env file.")
    
