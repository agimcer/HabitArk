import polars as pl
import psycopg2
from psycopg2.extras import execute_values

df_region = pl.read_parquet("data/malla_maestra_iberia.parquet")

ordered_columns = [
    "id_celda", "fila", "columna", "latitud", "longitud", 
    "elevacion", "pendiente", "bio1", "bio2", "bio3", "bio4", 
    "bio5", "bio6", "bio7", "bio8", "bio9", "bio10", "bio11", 
    "bio12", "bio13", "bio14", "bio15", "bio16", "bio17", 
    "bio18", "bio19", "agricultura", "matorral", "urbano", 
    "clase1", "clase2", "clase3", "clase4"
]

# Esto ordenará los datos y lanzará un ColumnNotFoundError si falta alguna variable
df_region = df_region.select(ordered_columns)

records = df_region.rows()

db_config = {
    "dbname": "habitark_db",
    "user": "postgres",
    "password": "postgres", 
    "host": "localhost",
    "port": "5432" 
}

insert_query = """
    INSERT INTO region (
        id_celda, fila, columna, latitud, longitud, 
        elevacion, pendiente, bio1, bio2, bio3, bio4, 
        bio5, bio6, bio7, bio8, bio9, bio10, bio11, 
        bio12, bio13, bio14, bio15, bio16, bio17, 
        bio18, bio19, agricultura, matorral, urbano, 
        clase1, clase2, clase3, clase4
    ) VALUES %s
"""

print(f"Inserting {len(records)} rows with {len(records[0])} columns...")

with psycopg2.connect(**db_config) as conn:
    with conn.cursor() as cur:
        execute_values(cur, insert_query, records, page_size=10000)
    conn.commit()
    
print("Data insertion completed.")