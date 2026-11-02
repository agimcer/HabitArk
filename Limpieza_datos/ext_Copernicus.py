import pystac_client
import planetary_computer
import odc.stac
import rioxarray
import numpy as np
import xarray as xr
import os

os.makedirs("mapas_recortados", exist_ok=True)

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

bbox = [-9.5, 36.0, 3.5, 44.0]

search = catalog.search(
    collections=["cop-dem-glo-90"],
    bbox=bbox,
)

items = list(search.items())

data = odc.stac.load(
    items,
    bands=["data"],
    bbox=bbox,
    resolution=0.00833333,
)

dem_da = data["data"].isel(time=0)
dem_da.rio.to_raster("mapas_recortados/elevacion_iberia.tif")

elev_arr = dem_da.values.astype(np.float32)
elev_arr = np.where(elev_arr < -100, np.nan, elev_arr)

lat_media = np.radians(40.0)
dx = 111320.0 * 0.00833333 * np.cos(lat_media)
dy = 111320.0 * 0.00833333

dz_dy, dz_dx = np.gradient(elev_arr, dy, dx)
pendiente_grados = np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)))

slope_da = xr.DataArray(
    pendiente_grados.astype(np.float32),
    coords=dem_da.coords,
    dims=dem_da.dims,
    attrs=dem_da.attrs
)
slope_da.rio.write_crs(dem_da.rio.crs, inplace=True)
slope_da.rio.write_nodata(np.nan, inplace=True)
slope_da.rio.to_raster("mapas_recortados/pendiente_iberia.tif")

