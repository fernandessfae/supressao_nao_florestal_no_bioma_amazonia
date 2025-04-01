import geopandas as gpd
import requests
import json
import os

geodata_url: str = 'https://siscom.ibama.gov.br/geoserver/publica/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=publica:veg_naofloresta_aml_a&outputFormat=application%2Fjson'
response = requests.get(geodata_url)

if response.status_code == 200:
    try:
        geodata = json.loads(response.content)
        gdf: gpd.GeoDataFrame = gpd.GeoDataFrame.from_features(
            geodata['features'])
        print(gdf.head())
        print()
        print(gdf.columns)
        print()
        print(gdf['estado'].value_counts())
        print()
        print(gdf['ano'].value_counts())
        print()
        gdf = gdf.rename(columns={'hectares': 'area_km2'})
        gdf['area_km2'] = round(gdf['area_km2'] / 100, 2)
        gdf.drop(columns=['imagem', 'antropizad'], inplace=True)
        gdf = gdf[gdf['estado'] != 'MTL']
        gdf = gdf[gdf['estado'] != 'MALL']
        gdf = gdf[gdf['ano'] != '0']
        gdf = gdf[gdf['ano'] != '2016L']
        gdf = gdf[gdf['ano'] != '23013']
        
        if not os.path.exists('state_geodata'):
            os.makedirs('state_geodata')
        
        unique_brazil_states: list[str] = gdf['estado'].unique()

        for state in unique_brazil_states:
            state_gdf = gdf[gdf['estado'] == state]
            
            state_csv_path: str = f'state_geodata/{state}_geodata.csv'
            if not os.path.exists(state_csv_path):
                state_gdf.to_csv(f'{state}_geodata.csv', index=False)
                print(f"Data for {state} saved to {state_csv_path}")

    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
else:
    print(f"Failed to retrieve data: {response.status_code} {response.text}.")