import pyinaturalist as pyinat

def get_species_ids(species: list):
    """Get species IDs from iNaturalist by name.

    Args:
        name (list): Species names."""
    
    results = []
    for name in species:
        res = pyinat.get_taxa(q=name, rank="species", per_page=1)
        if res['results']:
            results.append(res['results'][0]['id'])
        
    return results
def get_place_id(name):
    res = pyinat.get_places(q=name, per_page=1)
    if res["results"]:
        return res["results"][0]["id"]
    return None

# Cache to avoid redundant API calls
place_cache = {}
def get_country_from_obs(obs):
    place_ids = obs.get("place_ids", [])
    
    for pid in place_ids:
        if pid not in place_cache:
            res = pyinat.get_places_by_id([pid])
            if res["results"]:
                place_cache[pid] = res["results"][0]
            else:
                place_cache[pid] = None

        place = place_cache[pid]
        if place and place.get("place_type") == 12:
            return place.get("name")

    return None, None
def get_observations_by_id(
    taxon_ids: list,  
    country: str = None, 
    year_range: tuple = None, 
    lat_min: float = None, 
    lat_max: float = None, 
    lon_min: float = None, 
    lon_max: float = None,
    per_page : int = 200
    ):
    """Get occurrences from iNaturalist by taxon ID.

    Args:
        taxon_ids (list): List of taxon IDs.
        country (str, optional): Country code to filter occurrences. Defaults to None.
        year_range (tuple, optional): Year range to filter occurrences (start_year, end_year). Defaults to None.
        lat_min (float, optional): Minimum latitude for bounding box. Defaults to None.
        lat_max (float, optional): Maximum latitude for bounding box. Defaults to None.
        lon_min (float, optional): Minimum longitude for bounding box. Defaults to None.
        lon_max (float, optional): Maximum longitude for bounding box. Defaults to None.
    """
    all_results = []

    for taxon_id in taxon_ids:
        params = {
            "taxon_id": taxon_id,
            "per_page": per_page,
            "geo": True,
            "page": "all"
        }

        # Filtro de país via place_id
        if country:
            place_id = pyinat.get_places_autocomplete(q=country, per_page=1)['results'][0]['id']
            if place_id:
                params["place_id"] = place_id

        # Filtro por intervalo de ano
        if year_range:
            params["d1"] = f"{year_range[0]}-01-01"
            params["d2"] = f"{year_range[1]}-12-31"

        # Bounding box
        if None not in (lat_min, lat_max, lon_min, lon_max):
            params.update({
                "swlat": lat_min,
                "swlng": lon_min,
                "nelat": lat_max,
                "nelng": lon_max
            })

        res = pyinat.get_observations(**params)

        for obs in res["results"]:
            if(obs is None):
                continue
            else:
                date = obs.get("observed_on_details", {})
                if(date is None):
                    date = obs.get("created_at_details", {})
                
                all_results.append({
                    "source": 'inaturalist',
                    "scientificName": obs.get("taxon", {}).get("preferred_common_name"),
                    "country": get_country_from_obs(obs),
                    "latitude": obs.get("geojson", {}).get("coordinates", [None, None])[1],
                    "longitude": obs.get("geojson", {}).get("coordinates", [None, None])[0],
                    "day": date.get("day"),
                    "month": date.get("month"),
                    "year": date.get("year")
                })

    return all_results