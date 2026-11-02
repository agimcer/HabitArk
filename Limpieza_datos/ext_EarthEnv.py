import os
import rasterio
from rasterio.windows import from_bounds
import numpy as np

# 1. Definir el Bounding Box (Extensión espacial) de la Península Ibérica
# (Lon_min, Lat_min, Lon_max, Lat_max)
bbox_iberia = (-9.5, 36.0, 3.5, 44.0)

os.makedirs("mapas_recortados", exist_ok=True)

def recortar_y_guardar_raster(ruta_entrada, ruta_salida, bbox):
    """Recorta un raster global ajustándolo a las coordenadas de la Península Ibérica."""
    with rasterio.open(ruta_entrada) as src:
        # Calcular la ventana espacial correspondiente a la caja delimitadora de España
        left, bottom, right, top = bbox
        window = from_bounds(left, bottom, right, top, transform=src.transform)
        
        # Leer los datos de esa ventana específica
        datos = src.read(window=window)
        
        # Actualizar la georreferenciación (transform) para la nueva ventana recortada
        transform_nuevo = rasterio.windows.transform(window, src.transform)
        
        meta = src.meta.copy()
        meta.update({
            "height": datos.shape[1],
            "width": datos.shape[2],
            "transform": transform_nuevo
        })
        
        # Escribir el nuevo archivo .tif recortado
        with rasterio.open(ruta_salida, "w", **meta) as dest:
            dest.write(datos)
            
    print(f"Raster recortado guardado: {ruta_salida}")

# 2. Recortar las clases individuales de EarthEnv a la zona de España
# Rutas de tus archivos originales descargados
archivos_earthenv = {
    "clase1": "C:/Users/agime/Downloads/consensus_full_class_1.tif",
    "clase2": "C:/Users/agime/Downloads/consensus_full_class_2.tif",
    "clase3": "C:/Users/agime/Downloads/consensus_full_class_3.tif",
    "clase4": "C:/Users/agime/Downloads/consensus_full_class_4.tif",
    "matorral": "C:/Users/agime/Downloads/consensus_full_class_5.tif",
    "agricultura": "C:/Users/agime/Downloads/consensus_full_class_7.tif",
    "urbano": "C:/Users/agime/Downloads/consensus_full_class_9.tif"
}

rutas_recortadas = {}
for nombre, ruta in archivos_earthenv.items():
    salida = f"mapas_recortados/{nombre}_iberia.tif"
    if os.path.exists(ruta):
        recortar_y_guardar_raster(ruta, salida, bbox_iberia)
        rutas_recortadas[nombre] = salida
    else:
        print(f"Aviso: No se encontró el archivo original {ruta}")

# 3. Fusionar las clases 1, 2, 3 y 4 en un único raster de "Bosque Total"
print("Fusionando clases forestales (1 a 4) en un único raster de bosque...")

rutas_bosques_recortados = [
    rutas_recortadas.get("clase1"),
    rutas_recortadas.get("clase2"),
    rutas_recortadas.get("clase3"),
    rutas_recortadas.get("clase4")
]

# Abrimos la primera clase como referencia espacial y de metadatos
with rasterio.open(rutas_bosques_recortados[0]) as src0:
    meta_bosque = src0.meta.copy()
    # Inicializamos un array acumulador con ceros del tamaño del recorte
    bosque_acumulado = np.zeros((src0.height, src0.width), dtype=np.float32)
    nodata_val = src0.nodata

# Sumar pixel a pixel las 4 clases forestales
for r in rutas_bosques_recortados:
    with rasterio.open(r) as src:
        arr = src.read(1).astype(np.float32)
        # Limpiar valores nulos o negativos convirtiéndolos en 0 para la suma
        if nodata_val is not None:
            arr = np.where((arr == nodata_val) | (arr < 0), 0, arr)
        else:
            arr = np.where(arr < 0, 0, arr)
        bosque_acumulado += arr

# Guardar el raster unificado resultante
ruta_bosque_total = "mapas_recortados/cobertura_arborea_total_iberia.tif"
with rasterio.open(ruta_bosque_total, "w", **meta_bosque) as dest_bosque:
    dest_bosque.write(bosque_acumulado, 1)

print(f"¡Proceso completado! Raster de bosque unificado guardado en: {ruta_bosque_total}")