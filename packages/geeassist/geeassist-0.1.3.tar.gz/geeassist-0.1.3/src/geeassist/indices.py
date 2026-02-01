import ee

def calculate_ndvi(image, nir_band, red_band, rename='NDVI'):
    """
    Calculate NDVI for an image.
    
    Args:
        image (ee.Image): Input image.
        nir_band (str): Name of the Near-Infrared band.
        red_band (str): Name of the Red band.
        rename (str): Name of the output band (default: 'NDVI').
        
    Returns:
        ee.Image: Image with the added NDVI band.
    """
    ndvi = image.normalizedDifference([nir_band, red_band]).rename(rename)
    return image.addBands(ndvi)

def calculate_ndwi(image, green_band, nir_band, rename='NDWI'):
    """
    Calculate NDWI (McFeeters) for water bodies.
    
    Args:
        image (ee.Image): Input image.
        green_band (str): Name of the Green band.
        nir_band (str): Name of the Near-Infrared band.
        
    Returns:
        ee.Image: Image with the added NDWI band.
    """
    ndwi = image.normalizedDifference([green_band, nir_band]).rename(rename)
    return image.addBands(ndwi)

def calculate_evi(image, nir_band, red_band, blue_band, rename='EVI'):
    """
    Calculate Enhanced Vegetation Index (EVI).
    Formula: 2.5 * ((NIR - Red) / (NIR + 6 * Red - 7.5 * Blue + 1))
    """
    nir = image.select(nir_band)
    red = image.select(red_band)
    blue = image.select(blue_band)
    
    evi = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
            'NIR': nir,
            'RED': red,
            'BLUE': blue
        }).rename(rename)
        
    return image.addBands(evi)
