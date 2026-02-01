import ee

def mask_clouds_landsat8(image):
    """
    Mask clouds in Landsat 8 using the QA_PIXEL band (or pixel_qa in older collections).
    Assumes standard Collection 2 Level 2 format.
    """
    qa = image.select('QA_PIXEL')
    
    # Bits 3 and 5 are Cloud Shadow and Cloud
    cloud_shadow_bit_mask = 1 << 3
    cloud_bit_mask = 1 << 5
    
    mask = qa.bitwiseAnd(cloud_shadow_bit_mask).eq(0) \
        .And(qa.bitwiseAnd(cloud_bit_mask).eq(0))
        
    return image.updateMask(mask)

def export_image_to_drive(image, description, folder, region, scale=30, crs='EPSG:4326'):
    """
    Wrapper to export an image to Google Drive.
    """
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        region=region,
        scale=scale,
        crs=crs,
        maxPixels=1e13
    )
    task.start()
    print(f"Export task '{description}' started.")
    return task

def date_filter(collection, start_date, end_date):
    """
    Simple wrapper for filterDate.
    """
    return collection.filterDate(start_date, end_date)
