import os
import sys
import geopandas as gpd

try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    from rpy2.robjects.conversion import localconverter
    HAS_RPY2 = True
except ImportError:
    HAS_RPY2 = False
    print("Warning: rpy2 is not installed. specialized plotting functions will not work.")

def check_r_environment():
    """
    Checks if R and required R packages (ggplot2, tmap, ggspatial, sf) are installed.
    """
    if not HAS_RPY2:
        return False, "rpy2 is not installed."
    
    required_packages = ['ggplot2', 'tmap', 'ggspatial', 'sf']
    missing_packages = []
    
    utils = importr('utils')
    
    for pkg in required_packages:
        if not robjects.r.require(pkg)[0]:
            missing_packages.append(pkg)
            
    if missing_packages:
        return False, f"Missing R packages: {', '.join(missing_packages)}"
        
    return True, "All requirements met."

def install_r_packages():
    """
    Installs the necessary R packages for mapping.
    """
    if not HAS_RPY2:
        print("Cannot install R packages because rpy2 is missing.")
        return

    utils = importr('utils')
    packnames = ['ggplot2', 'tmap', 'ggspatial', 'sf', 'dplyr']
    
    print("Installing R packages... This may take a while.")
    utils.install_packages(robjects.StrVector(packnames))
    print("R packages installed.")

def gdf_to_r_sf(gdf):
    """
    Converts a GeoPandas DataFrame to an R sf object.
    Assumes the gdf is properly formatted.
    """
    # This is a bit complex directly, simpler approach is writing to temp file
    # or using specialized conversion. For robustness, let's use a temp shapefile/geojson approach
    # as robust rpy2 conversion can be tricky with geometries.
    import tempfile
    
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, 'data.geojson')
    gdf.to_file(temp_file, driver='GeoJSON')
    
    sf = importr('sf')
    return sf.read_sf(temp_file)

def ggplot_map(data, title="Map", output_file="map.png"):
    """
    Create a static publication-quality map using ggplot2.
    
    Args:
        data: GeoPandas DataFrame or path to vector file.
        title (str): Map title.
        output_file (str): Path to save the output image.
    """
    if not HAS_RPY2:
        print("rpy2 is required for this function.")
        return

    if isinstance(data, str):
        sf = importr('sf')
        r_data = sf.read_sf(data)
    elif isinstance(data, gpd.GeoDataFrame):
        r_data = gdf_to_r_sf(data)
    else:
        print("Unsupported data type.")
        return

    ggplot2 = importr('ggplot2')
    ggspatial = importr('ggspatial')
    
    # Construct the plot
    # Python's rpy2 syntax for: ggplot(data) + geom_sf() + ...
    
    pp = ggplot2.ggplot(r_data) + \
         ggplot2.geom_sf(fill="lightblue", color="black", size=0.2) + \
         ggplot2.ggtitle(title) + \
         ggplot2.theme_bw() + \
         ggspatial.annotation_scale(location="bl", width_hint=0.5) + \
         ggspatial.annotation_north_arrow(location="tl", which_north="true", 
                                          style=ggspatial.north_arrow_fancy_orienteering)

    print(f"Saving map to {output_file}...")
    ggplot2.ggsave(output_file, plot=pp, width=10, height=8, dpi=300)
    print("Done.")

def ggplot_map(data, col_name=None, title="Map", color="lightblue", edge_color="black", 
               add_scale=True, add_north=True, output_file="map.jpg"):
    """
    Create a static publication-quality vector map using ggplot2.
    
    Args:
        data: GeoPandas DataFrame or path to vector file.
        col_name (str): Column name to use for fill color (choropleth). If None, uses fixed 'color'.
        title (str): Map title.
        color (str): Fill color if col_name is None.
        edge_color (str): Border color.
        add_scale (bool): Add scale bar.
        add_north (bool): Add north arrow.
        output_file (str): Path to save output (e.g., .jpg, .png).
    """
    if not HAS_RPY2:
        print("rpy2 is required.")
        return

    if isinstance(data, str):
        sf = importr('sf')
        r_data = sf.read_sf(data)
    elif isinstance(data, gpd.GeoDataFrame):
        r_data = gdf_to_r_sf(data)
    else:
        print("Unsupported data type.")
        return

    ggplot2 = importr('ggplot2')
    ggspatial = importr('ggspatial')
    
    # Base Plot
    pp = ggplot2.ggplot(r_data)
    
    # Geometry
    if col_name:
        # Choropleth
        pp += ggplot2.geom_sf(ggplot2.aes_string(fill=col_name), color=edge_color, size=0.2) + \
              ggplot2.scale_fill_viridis_c() # Default to viridis for ease
    else:
        # Single Color
        pp += ggplot2.geom_sf(fill=color, color=edge_color, size=0.2)
        
    # Layout and Labels
    pp += ggplot2.ggtitle(title) + \
          ggplot2.theme_bw() + \
          ggplot2.labs(x="Longitude", y="Latitude")
          
    if add_scale:
        pp += ggspatial.annotation_scale(location="bl", width_hint=0.5)
        
    if add_north:
        pp += ggspatial.annotation_north_arrow(location="tl", which_north="true", 
                                          style=ggspatial.north_arrow_fancy_orienteering)

    print(f"Saving map to {output_file}...")
    ggplot2.ggsave(output_file, plot=pp, width=10, height=8, dpi=300)
    print("Done.")

def tmap_map(data, col_name=None, title="Map", palette="Blues", style="white", output_file="map.jpg"):
    """
    Create a thematic map using tmap.
    
    Args:
        data: GeoPandas DataFrame or path.
        col_name (str): Column to visualize.
        title (str): Map title.
        palette (str): Color palette (e.g., "Blues", "RdYlGn").
        style (str): tmap style (e.g., "white", "classic", "cobalt").
        output_file (str): Output filename.
    """
    if not HAS_RPY2: return

    if isinstance(data, str):
        sf = importr('sf')
        r_data = sf.read_sf(data)
    elif isinstance(data, gpd.GeoDataFrame):
        r_data = gdf_to_r_sf(data)
    else:
        return

    tmap = importr('tmap')
    
    tmap.tmap_mode("plot")
    tmap.tm_style(style)
    
    # Build map
    tm = tmap.tm_shape(r_data)
    
    if col_name:
        tm += tmap.tm_polygons(col=col_name, palette=palette, title=col_name)
    else:
        tm += tmap.tm_polygons(col="blue", alpha=0.5)
        
    tm += tmap.tm_layout(title=title, frame=True, legend_position=robjects.StrVector(["right", "bottom"])) + \
          tmap.tm_scale_bar(position=robjects.StrVector(["left", "bottom"])) + \
          tmap.tm_compass(position=robjects.StrVector(["right", "top"]))

    print(f"Saving map to {output_file}...")
    tmap.tmap_save(tm, filename=output_file, width=10, height=8, dpi=300)
    print("Done.")

def ggplot_raster_map(raster_path, title="Raster Map", output_file="map.png"):
    """
    Map a raster file using R's terra and tidyterra/ggplot2.
    """
    if not HAS_RPY2:
        print("rpy2 is required.")
        return

    # Check for terra
    if not robjects.r.require('terra')[0]:
        print("R package 'terra' is missing.")
        return
        
    terra = importr('terra')
    ggplot2 = importr('ggplot2')
    # tidyterra is excellent for ggplot + terra, but might not be standard. 
    # Let's try standard plotting or just terra's plot if tidyterra missing? 
    # Actually, converting terra to df for ggplot is standard but slow. 
    # Let's verify if user has 'tidyterra' or use 'gplot' from rasterVis?
    # For simplicity and robustness without too many dependencies, we might use tmap for rasters as it handles them natively well.
    # But user asked for ggplot2 example.
    
    # We will assume 'terra' produces a SpatRaster.
    # To plot in ggplot effectively without extra packages, we sample or convert.
    # Let's use tmap instead as fallback if valid, but try to implement a basic ggplot raster approach.
    
    print("Reading raster in R...")
    r_raster = terra.rast(raster_path)
    
    # Simple conversion to dataframe for ggplot (warning: heavy for large rasters)
    # R: df <- as.data.frame(r_raster, xy=TRUE)
    r_df = terra.as_data_frame(r_raster, xy=True)
    
    # Column names usually x, y, and the band name (e.g. 'NDVI')
    # We assume 3rd col is value.
    
    pp = ggplot2.ggplot(r_df, ggplot2.aes_string(x='x', y='y', fill='NDVI')) + \
         ggplot2.geom_raster() + \
         ggplot2.scale_fill_viridis_c() + \
         ggplot2.coord_fixed() + \
         ggplot2.ggtitle(title) + \
         ggplot2.theme_minimal()
         
    print(f"Saving raster map to {output_file}...")
    ggplot2.ggsave(output_file, plot=pp, width=10, height=8, dpi=300)

def tmap_raster_map(raster_path, title="Raster Map", output_file="map.png"):
    """
    Map a raster using tmap.
    """
    if not HAS_RPY2: return

    if not robjects.r.require('terra')[0]:
        print("R package 'terra' missing.")
        return
        
    tmap = importr('tmap')
    terra = importr('terra')
    
    r_raster = terra.rast(raster_path)
    tmap.tmap_mode("plot")
    
    tm = tmap.tm_shape(r_raster) + \
         tmap.tm_raster(title="NDVI", style="cont", palette="RdYlGn") + \
         tmap.tm_layout(title=title, frame=True)
         
    tmap.tmap_save(tm, filename=output_file, width=10, height=8, dpi=300)

