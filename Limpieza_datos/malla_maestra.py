import os
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
import numpy as np
import polars as pl

base_dir = "Limpieza_datos/mapas_recortados"
ref_raster_path = os.path.join(base_dir, "elevacion_iberia.tif")
output_path = "data/malla_maestra_iberia.parquet"

print("Extracting spatial grid from reference raster...")
with rasterio.open(ref_raster_path) as ref_src:
    ref_transform = ref_src.transform
    ref_width = ref_src.width
    ref_height = ref_src.height
    ref_crs = ref_src.crs
    nodata_val = ref_src.nodata
    
    cols, rows = np.meshgrid(np.arange(ref_width), np.arange(ref_height))
    lons, lats = rasterio.transform.xy(ref_transform, rows, cols)
    
    grid_data = {
        "fila": rows.flatten(),
        "columna": cols.flatten(),
        "longitud": np.array(lons).flatten(),
        "latitud": np.array(lats).flatten()
    }

vrt_options = {
    'crs': ref_crs,
    'transform': ref_transform,
    'width': ref_width,
    'height': ref_height,
    'resampling': Resampling.nearest
}

single_band_files = [
    "elevacion_iberia.tif", "pendiente_iberia.tif", 
    "agricultura_iberia.tif", "matorral_iberia.tif", "urbano_iberia.tif",
    "clase1_iberia.tif", "clase2_iberia.tif", "clase3_iberia.tif", "clase4_iberia.tif"
]

print("Processing single-band rasters with on-the-fly alignment...")
for file_name in single_band_files:
    file_path = os.path.join(base_dir, file_name)
    if os.path.exists(file_path):
        with rasterio.open(file_path) as src:
            with WarpedVRT(src, **vrt_options) as vrt:
                col_name = file_name.split("_iberia")[0]
                grid_data[col_name] = vrt.read(1).flatten()

print("Building base Polars DataFrame...")
df_region = pl.DataFrame(grid_data)

# Adjusted to process the climate dataset as a Parquet file
climate_path = os.path.join(base_dir, "matriz_climatica.parquet") 
if os.path.exists(climate_path):
    print("Merging climate data from Parquet file...")
    df_climate = pl.read_parquet(climate_path)
    
    # Identify common spatial columns to perform a safe join
    join_cols = [col for col in ["fila", "columna", "latitud", "longitud"] if col in df_climate.columns]
    
    if join_cols:
         df_region = df_region.join(df_climate, on=join_cols, how="left")
    else:
         print("WARNING: No spatial index columns found. Performing direct horizontal concatenation.")
         df_region = pl.concat([df_region, df_climate], how="horizontal")
else:
    raise FileNotFoundError(f"CRITICAL: Climate file missing at {climate_path}. Check the exact spelling.")

print("Filtering nodata pixels...")
if nodata_val is not None:
    df_region = df_region.filter(pl.col("elevacion") != nodata_val)
else:
    df_region = df_region.filter(pl.col("elevacion").is_not_null())

df_region = df_region.with_row_index(name="id_celda")

os.makedirs("data", exist_ok=True)
df_region.write_parquet(output_path)

print(f"Successfully created master grid with {df_region.height} land cells.")