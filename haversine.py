def haversine(lat1, lon1, lat2, lon2):
    """
    Bereken de grootcirkelafstand tussen twee punten 
    op de aarde (gemiddelde afwijking: 395m)
    """
    import numpy as np
    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    lon1 = np.radians(lon1)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    R = 6378137  # equatoriale radius (WGS84)
    
    return R * c
