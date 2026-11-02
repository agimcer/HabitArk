import rasterio
from rasterio.windows import from_bounds
from pathlib import Path

# 1. Definir el Bounding Box de la Península Ibérica
# Coordenadas: (Oeste, Sur) a (Este, Norte)
lon_min, lat_min = -9.5, 36.0  
lon_max, lat_max = 3.5, 44.0   

# 2. Configurar directorios
carpeta_origen = Path("C:/Users/agime/Downloads/wc2.1_30s_bio")
directorio_actual = Path(__file__).parent

# Crear la nueva carpeta "carpeta_iberia" justo al lado del script
carpeta_destino = directorio_actual / "carpeta_iberia"
carpeta_destino.mkdir(exist_ok=True)

print("Iniciando recorte espacial...")

# 3. Iterar sobre los 19 archivos
for i in range(1, 20):
    archivo_entrada = carpeta_origen / f"wc2.1_30s_bio_{i}.tif"
    archivo_salida = carpeta_destino / f"iberia_bio_{i}.tif"
    
    if not archivo_entrada.exists():
        print(f"⚠️ No se encontró: {archivo_entrada.name}")
        continue

    with rasterio.open(archivo_entrada) as src:
        # A. Calcular la "ventana" de píxeles que coincide con las coordenadas
        ventana = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)
        
        # B. Extraer a la RAM *únicamente* los píxeles de esa ventana
        datos_recortados = src.read(1, window=ventana)
        
        # C. Copiar los metadatos espaciales y actualizarlos al nuevo tamaño
        metadatos = src.meta.copy()
        metadatos.update({
            "height": ventana.height,
            "width": ventana.width,
            "transform": rasterio.windows.transform(ventana, src.transform)
        })
        
        # D. Guardar el nuevo mapa ibérico en el disco duro
        with rasterio.open(archivo_salida, "w", **metadatos) as dest:
            dest.write(datos_recortados, 1)
            
    print(f"✅ Recortado y guardado: {archivo_salida.name}")

print("\n¡Proceso terminado! Ya puedes borrar la carpeta de 10 GB.")

