"""
Module for fetching species occurrence data from multiple sources.

This module provides functions to retrieve species occurrence records from:
- Global Biodiversity Information Facility (GBIF)
- iNaturalist
- SpeciesLink

It supports filtering by geographic bounds, country, and year range, 
with caching to avoid redundant API calls.
"""

import os
import logging
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional, Dict, Union

import pandas as pd

import sdmdata.inaturalist as inaturalist
import sdmdata.gbif as gbif
import sdmdata.speciesLink as speciesLink

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_all(
    species_names: List[str],
    country: Optional[str] = None,
    year_range: Optional[Tuple[int, int]] = None,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lon_min: Optional[float] = None,
    lon_max: Optional[float] = None,
    includeGbif: bool = True,
    includeInaturalist: bool = True,
    includeSpeciesLink: bool = True
) -> Tuple[pd.DataFrame, Dict, Dict]:
    """
    Fetch species occurrences from multiple data sources in parallel.
    
    Retrieves species occurrence data from GBIF, iNaturalist, and SpeciesLink
    simultaneously using ThreadPoolExecutor for improved performance.
    
    Args:
        species_names: List of species names to search for.
        country: Country code or name to filter occurrences (optional).
        year_range: Tuple of (start_year, end_year) to filter occurrences (optional).
        lat_min: Minimum latitude for geographic filtering (optional).
        lat_max: Maximum latitude for geographic filtering (optional).
        lon_min: Minimum longitude for geographic filtering (optional).
        lon_max: Maximum longitude for geographic filtering (optional).
        includeGbif: Whether to fetch data from GBIF (default: True).
        includeInaturalist: Whether to fetch data from iNaturalist (default: True).
        includeSpeciesLink: Whether to fetch data from SpeciesLink (default: True).
    
    Returns:
        Tuple of (gbif_data, inat_data, specieslink_data) as DataFrames/Dicts.
    
    Raises:
        Exception: If any source experiences an API error during fetch.
    """
    try:
        logger.info(f"Fetching species IDs/keys for {len(species_names)} species...")
        gbif_keys = gbif.get_species_keys(species_names)
        inat_ids = inaturalist.get_species_ids(species_names)
        logger.info("Species IDs/keys retrieved successfully.")
    except Exception as e:
        logger.error(f"Error retrieving species IDs/keys: {e}")
        raise
    
    gbif_data = pd.DataFrame()
    inat_data = {}
    specieslink_data = {}
    
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            # Submit GBIF fetch if enabled
            if includeGbif:
                try:
                    futures['gbif'] = executor.submit(
                        gbif.get_occurrences_by_key,
                        gbif_keys,
                        country,
                        year_range,
                        lat_min,
                        lat_max,
                        lon_min,
                        lon_max
                    )
                except Exception as e:
                    raise Exception(f"Error submitting GBIF fetch: {e}")
            
            # Submit iNaturalist fetch if enabled
            if includeInaturalist:
                try:
                    futures['inaturalist'] = executor.submit(
                        inaturalist.get_observations_by_id,
                        inat_ids,
                        country,
                        year_range,
                        lat_min,
                        lat_max,
                        lon_min,
                        lon_max
                    )
                except Exception as e:
                    raise Exception(f"Error submitting iNaturalist fetch: {e}")
            
            # Submit SpeciesLink fetch if enabled
            if includeSpeciesLink:
                try:
                    futures['specieslink'] = executor.submit(
                        speciesLink.get_occurrences_by_name,
                        species_names,
                        country,
                        year_range,
                        lat_min,
                        lat_max,
                        lon_min,
                        lon_max
                    )
                except Exception as e:
                    raise Exception(f"Error submitting SpeciesLink fetch: {e}")
            
            # Collect results as they complete
            for source, future in futures.items():
                try:
                    result = future.result()
                    if source == 'gbif':
                        gbif_data = result if isinstance(result, pd.DataFrame) else pd.DataFrame()
                        logger.info(f"GBIF: Retrieved {len(gbif_data)} occurrences.")
                    elif source == 'inaturalist':
                        inat_data = result if isinstance(result, (dict, list)) else {}
                        logger.info(f"iNaturalist: Retrieved {len(inat_data)} occurrences.")
                    elif source == 'specieslink':
                        specieslink_data = result if isinstance(result, (dict, list)) else {}
                        logger.info(f"SpeciesLink: Retrieved  {len(specieslink_data)} occurrences.")
                except Exception as e:
                    raise Exception(f"Error retrieving {source} data: {e}")
        
        logger.info("All data sources fetched successfully.")
    except Exception as e:
        logger.error(f"Critical error in fetch_all: {e}")
        raise
    
    return gbif_data, inat_data, specieslink_data

def make_occ_filename(
    species_list: List[str],
    source: str,
    region: Union[str, Tuple],
    year_range: Union[Tuple[int, int], str],
    ext: str = "csv"
) -> str:
    """
    Generate a cache filename for occurrence data based on search parameters.
    
    Creates a consistent filename using species names, sources, geographic region,
    and year range. Includes an MD5 hash of normalized species names to ensure
    uniqueness and handle long filenames.
    
    Args:
        species_list: List of species names.
        source: Data source identifier(s) (e.g., 'gbif', 'inaturalist').
        region: Geographic region as country name or coordinate tuple.
        year_range: Year range tuple or string representation.
        ext: File extension (default: 'csv').
    
    Returns:
        str: Formatted filename for caching occurrence data.
    
    Raises:
        ValueError: If species_list is empty or source is invalid.
    """
    if not species_list:
        raise ValueError("species_list cannot be empty.")
    
    if not source:
        raise ValueError("source cannot be empty.")
    
    try:
        # Normalize species names for consistent hashing
        normalized = ",".join(sorted(s.strip().lower() for s in species_list))
        
        # Create short hash for filename uniqueness
        h = hashlib.md5(normalized.encode()).hexdigest()[:6]
        
        # Format region information
        region_str = str(region) if region else "global"
        
        return f"{source}_occ_{region_str}_{year_range}_{h}.{ext}"
    except Exception as e:
        logger.error(f"Error creating filename: {e}")
        raise

def check_if_file_exists(filename: str, directory: str = "all_occurrences") -> bool:
    """
    Check if a cache file exists in the specified directory.
    
    Args:
        filename: Name of the file to check.
        directory: Directory path to search in (default: "all_occurrences").
    
    Returns:
        bool: True if file exists and is readable, False otherwise.
    
    Raises:
        TypeError: If filename or directory is not a string.
    """
    if not isinstance(filename, str):
        raise TypeError("filename must be a string.")
    
    if not isinstance(directory, str):
        raise TypeError("directory must be a string.")
    
    try:
        filepath = os.path.join(directory, filename)
        exists = os.path.isfile(filepath)
        if exists:
            logger.info(f"Cache file found: {filepath}")
        return exists
    except Exception as e:
        logger.error(f"Error checking file existence: {e}")
        return False

def get_occurrences(
    species_names: List[str],
    country: Optional[str] = None,
    year_range: Optional[Tuple[int, int]] = None,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lon_min: Optional[float] = None,
    lon_max: Optional[float] = None,
    includeGbif: bool = True,
    includeInaturalist: bool = True,
    includeSpeciesLink: bool = True
) -> pd.DataFrame:
    """
    Retrieve species occurrence records from multiple sources with caching.
    
    Fetches occurrence data for specified species from available sources, with
    support for geographic and temporal filtering. Results are cached to avoid
    redundant API calls. If cached data exists, it is returned immediately.
    
    Args:
        species_names: List of species names to search for (required, must not be empty).
        country: Country filter for occurrences (optional).
        year_range: Tuple of (start_year, end_year) for temporal filtering (optional).
        lat_min: Minimum latitude boundary (optional).
        lat_max: Maximum latitude boundary (optional).
        lon_min: Minimum longitude boundary (optional).
        lon_max: Maximum longitude boundary (optional).
        includeGbif: Include GBIF data source (default: True).
        includeInaturalist: Include iNaturalist data source (default: True).
        includeSpeciesLink: Include SpeciesLink data source (default: True).
    
    Returns:
        pd.DataFrame: Combined occurrence data from all enabled sources, or empty
                      DataFrame if an error occurs.
    
    Raises:
        ValueError: If species_names is empty or no data sources are enabled.
        IOError: If cache directory cannot be created.
    
    Examples:
        >>> df = get_occurrences(['Puma concolor'], country='Brazil')
        >>> df = get_occurrences(['Apis mellifera'], year_range=(2020, 2023))
        >>> df = get_occurrences(['Panthera onca'], lat_min=-5, lat_max=5, 
        ...                      lon_min=-60, lon_max=-55)
    """
    
    # Validate input parameters
    if not species_names or (isinstance(species_names, list) and len(species_names) == 0):
        logger.error("species_names must be a non-empty list of species names.")
        raise ValueError("species_names must be a non-empty list of species names.")
    
    if not (includeGbif or includeInaturalist or includeSpeciesLink):
        logger.error("At least one data source must be included.")
        raise ValueError("At least one data source must be included.")
    
    logger.info(f"Starting occurrence data retrieval for {len(species_names)} species.")
    
    # Setup cache directory
    directory = "all_occurrences"
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created cache directory: {directory}")
    except OSError as e:
        logger.error(f"Failed to create cache directory '{directory}': {e}")
        raise IOError(f"Cannot create cache directory: {e}")
    
    # Generate source identifier string
    
    source_parts = []
    if includeGbif:
        
        source_parts.append('gbif')
    if includeInaturalist:
        source_parts.append('inaturalist')
    if includeSpeciesLink:
        source_parts.append('specieslink')
    
    source = '_'.join(source_parts) if source_parts else 'unknown'
    
    # Determine region identifier
    try:
        if country:
            region = country
        elif all(v is not None for v in [lat_max, lat_min, lon_max, lon_min]):
            region = f"({lat_max},{lat_min},{lon_max},{lon_min})"
        else:
            region = "global"
    except Exception as e:
        logger.warning(f"Error determining region: {e}, using 'global'")
        region = "global"
    
    # Generate cache filename
    year = str(year_range) if year_range else "all_years"
    try:
        cache_filename = make_occ_filename(species_names, source, region, year, ext="csv")
    except Exception as e:
        logger.error(f"Error generating cache filename: {e}")
        return pd.DataFrame()
    
    logger.info(f"Cache filename: {cache_filename}")
    
    # Check cache first
    if check_if_file_exists(cache_filename, directory=directory):
        try:
            logger.info("Loading occurrences from cache...")
            df = pd.read_csv(os.path.join(directory, cache_filename))
            logger.info(f"Loaded {len(df)} records from cache.")
            return df
        except pd.errors.ParserError as e:
            logger.warning(f"Cache file is corrupted: {e}. Fetching fresh data.")
        except Exception as e:
            logger.warning(f"Error reading cache file: {e}. Fetching fresh data.")
    
    # Fetch fresh data from sources
    try:
        logger.info("Fetching fresh data from sources...")
        gbif_data, inat_data, specieslink_data = fetch_all(
            species_names,
            country,
            year_range,
            lat_min,
            lat_max,
            lon_min,
            lon_max,
            includeGbif,
            includeInaturalist,
            includeSpeciesLink
        )
        
        # Convert all data to DataFrames
        try:
            df_inat = pd.DataFrame(inat_data) if inat_data else pd.DataFrame()
        except Exception as e:
            logger.warning(f"Error converting iNaturalist data: {e}")
            df_inat = pd.DataFrame()
        
        try:
            df_specieslink = pd.DataFrame(specieslink_data) if specieslink_data else pd.DataFrame()
        except Exception as e:
            logger.warning(f"Error converting SpeciesLink data: {e}")
            df_specieslink = pd.DataFrame()
        
        # Combine all DataFrames
        try:
            dfs_to_combine = [gbif_data, df_inat, df_specieslink]
            dfs_to_combine = [df for df in dfs_to_combine if not df.empty]
            
            if not dfs_to_combine:
                logger.warning("No data retrieved from any source.")
                return pd.DataFrame()
            
            df = pd.concat(dfs_to_combine, ignore_index=True)
            logger.info(f"Combined {len(df)} total records from all sources.")
        except Exception as e:
            logger.error(f"Error combining DataFrames: {e}")
            return pd.DataFrame()
        
        # Save to cache
        try:
            cache_path = os.path.join(directory, cache_filename)
            df.to_csv(cache_path, index=False)
            logger.info(f"Cached {len(df)} records to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save cache file: {e}. Data still returned.")
        
        return df
        
    except Exception as e:
        logger.error(f"Critical error retrieving occurrences: {e}", exc_info=True)
        return pd.DataFrame()