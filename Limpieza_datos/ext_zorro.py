import requests
import polars as pl
import time

url = "https://api.gbif.org/v1/occurrence/search"
params = {
    "taxonKey": 5219243,
    "decimalLatitude": "36.0,44.0",
    "decimalLongitude": "-9.5,3.5",
    "hasCoordinate": "true",
    "year": "2000,2026",
    "coordinateUncertaintyInMeters": "0,1000",
    "limit": 300,
    "offset": 0
}

all_records = []
end_of_records = False

print("Fetching data directly from GBIF API...")

while not end_of_records:
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"API Error {response.status_code}: {response.text}")
        print(f"Failed URL: {response.url}")
        break
        
    data = response.json()
    results = data.get("results", [])
    
    if not results:
        break
        
    for record in results:
        extracted_data = {
            "gbif_id": str(record.get("gbifID", "")),
            "id_especie": record.get("speciesKey"),
            "latitud_obs": record.get("decimalLatitude"),
            "longitud_obs": record.get("decimalLongitude"),
            "incertidumbre_m": record.get("coordinateUncertaintyInMeters"),
            "anio": record.get("year"),
            "mes": record.get("month")
        }
        all_records.append(extracted_data)
        
    params["offset"] += params["limit"]
    end_of_records = data.get("endOfRecords", True)
    print(f"Fetched {len(all_records)} records so far...")
    
    time.sleep(0.5)

if all_records:
    df_observations = pl.DataFrame(all_records)
    df_observations = df_observations.drop_nulls(subset=["latitud_obs", "longitud_obs", "id_especie"])
    df_observations.write_parquet("data/observaciones_zorro.parquet")
    print(f"\nSuccessfully saved {df_observations.height} records.")
else:
    print("\nNo records fetched. Check the API status or parameters.")