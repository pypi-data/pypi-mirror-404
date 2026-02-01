import ee
import geemap

def init(project=None):
    """
    Initialize Google Earth Engine and Geemap.
    Automatically handles authentication if needed.
    
    Args:
        project (str, optional): The Google Cloud Project ID to use.
    """
    try:
        ee.Initialize(project=project)
        print("Google Earth Engine initialized successfully.")
    except Exception as e:
        print("Initialization failed. Attempting authentication...")
        try:
            ee.Authenticate()
            ee.Initialize(project=project)
            print("Google Earth Engine initialized successfully after authentication.")
        except Exception as auth_e:
            print(f"Failed to authenticate and initialize: {auth_e}")
            raise

def get_info(ee_object):
    """
    Get client-side info of an EE object in a human-readable format.
    """
    return ee_object.getInfo()

def create_map(center=[20, 0], zoom=3, **kwargs):
    """
    Create a geemap Map object with default settings.
    """
    return geemap.Map(center=center, zoom=zoom, **kwargs)
