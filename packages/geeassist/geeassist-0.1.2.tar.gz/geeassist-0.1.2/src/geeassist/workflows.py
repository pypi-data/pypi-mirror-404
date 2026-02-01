import ee
import geemap
import os
from . import indices
from . import graphics

def get_fao_gaul(name, level=2):
    """
    Get a feature collection from FAO GAUL by name.
    
    Args:
        name (str): Name of the administrative unit (e.g., 'Kolkata').
        level (int): Administrative level (0=Country, 1=State, 2=District).
        
    Returns:
        ee.Geometry: The geometry of the found region.
    """
    # FAO GAUL dataset
    collection = ee.FeatureCollection(f"FAO/GAUL/2015/level{level}")
    
    # Filter by name (ADM{level}_NAME)
    # Note: Case sensitivity might be an issue, so we try to be flexible if possible.
    # For now, strict match.
    feature = collection.filter(ee.Filter.eq(f'ADM{level}_NAME', name)).first()
    
    # Check if feature exists
    # This is a client-side check which requires .getInfo() or check size on server
    # We will return geometry.
    return feature.geometry()

def download_ndvi_image(region, start_date, end_date, output_file, scale=100):
    """
    Computes max NDVI for a region and saves it locally.
    
    Args:
        region (ee.Geometry): ROI.
        start_date (str): Start date (YYYY-MM-DD).
        end_date (str): End date.
        output_file (str): Local path to save .tif.
        scale (int): Scale in meters.
        
    Returns:
        str: Path to the saved file.
    """
    # Sentinel-2 is good for this
    s2 = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterBounds(region) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .median() \
        .clip(region)
        
    # Calculate NDVI
    ndvi = indices.calculate_ndvi(s2, 'B8', 'B4')
    
    # Select only NDVI
    ndvi_band = ndvi.select('NDVI')
    
    print(f"Downloading NDVI to {output_file}...")
    geemap.ee_export_image(
        ndvi_band, 
        filename=output_file, 
        scale=scale, 
        region=region,
        file_per_band=False
    )
    return output_file

def auto_process_and_map(location_name, start_date, end_date, output_dir=".", use_ggplot=True):
    """
    Complete workflow:
    1. Find location (FAO GAUL).
    2. Compute NDVI.
    3. Download GeoTIFF.
    4. Map it using R.
    
    Args:
        location_name (str): Name of the city/district.
        start_date (str): 'YYYY-MM-DD'.
        end_date (str): 'YYYY-MM-DD'.
        output_dir (str): Directory to save outputs.
        use_ggplot (bool): If True uses ggplot2, else tmap.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"--- Processing for {location_name} ---")
    
    # 1. Get Region
    print("Fetching region boundary...")
    region = get_fao_gaul(location_name)
    # We need to handle if region is empty/null, but for simplified workflow we assume valid input or error out.
    
    # 2. Download Data
    tif_path = os.path.join(output_dir, f"{location_name}_ndvi.tif")
    map_path = os.path.join(output_dir, f"{location_name}_map.png")
    
    download_ndvi_image(region, start_date, end_date, tif_path)
    
    # 3. Plotting
    # Note: Our graphics.py was designed for vectors (gdf). We need to handle rasters.
    # The simplest 'publication quality' map for raster in R often uses 'terra' + 'ggplot2' (geom_spatraster) or 'tmap'.
    # We need to update graphics module to handle raster paths.
    
    print("Generating Map...")
    title = f"NDVI Map of {location_name} ({start_date} to {end_date})"
    
    if use_ggplot:
        graphics.ggplot_raster_map(tif_path, title, map_path)
    else:
        graphics.tmap_raster_map(tif_path, title, map_path)
        
    print(f"Success! Map saved to {map_path}")
