from .occurrence_requests import get_occurrences
from .gbif import save_gbif_credentials, delete_gbif_credentials, get_species_autocomplete
from .speciesLink import save_specieslink_apikey, delete_specieslink_apikey

__all__ = [
    "get_occurrences",
    "get_species_autocomplete",
    "save_gbif_credentials",
    "delete_gbif_credentials",
    "save_specieslink_apikey",
    "delete_specieslink_apikey"
]

def version():
    return "0.0.1"
def  describe ():   
    description = ( 
        "SDM Data Library\n" 
        "Version: {}\n" 
        "Implement functions to get occurrences records from GBIF/INaturalist/SpeciesLink as:\n" 
        " - get_occurrences\n" 
        " - get_species_autocomplete\n" 
     ). format (version()) 
    print (description)
  
    return description