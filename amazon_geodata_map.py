import geopandas as gpd
from pandas import to_numeric
import requests
import json
import folium
import branca.colormap as cm
import numpy as np # Importar numpy para is_nan
from shapely.geometry import Polygon, MultiPolygon # Importar para depuração de tipos

geodata_url: str = 'https://siscom.ibama.gov.br/geoserver/publica/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=publica:veg_naofloresta_aml_a&outputFormat=application%2Fjson'
response = requests.get(geodata_url)

if response.status_code == 200:
    try:
        geodata = json.loads(response.content)
        gdf: gpd.GeoDataFrame = gpd.GeoDataFrame.from_features(geodata['features'])
        
        print("--- INÍCIO DA DEPURÇÃO ---")
        print("DataFrame inicial (primeiras 5 linhas):\n", gdf.head())
        print("\nColunas do DataFrame inicial:\n", gdf.columns)
        print("\nContagem de valores por estado:\n", gdf['estado'].value_counts())
        print("\nContagem de valores por ano:\n", gdf['ano'].value_counts())
        
        # 1. Renomear coluna e converter unidades
        gdf = gdf.rename(columns={'hectares': 'area_km2'})
        gdf['area_km2'] = round(gdf['area_km2'] / 100, 2)

        # 2. Remover colunas desnecessárias
        gdf.drop(columns=['imagem', 'antropizad'], inplace=True)

        # 3. Limpeza de dados na coluna 'estado'
        gdf = gdf[~gdf['estado'].isin(['MTL', 'MALL'])]

        # 4. Limpeza e conversão da coluna 'ano'
        # Registrar valores de 'ano' problemáticos antes da remoção
        print("\n--- Verificando valores problemáticos na coluna 'ano' ---")
        problematic_years = gdf[~gdf['ano'].astype(str).str.isnumeric() | 
                                 gdf['ano'].astype(str).isin(['0', '2016L', '23013'])]
        if not problematic_years.empty:
            print("Valores de 'ano' que serão removidos ou coercidos:\n", problematic_years['ano'].value_counts())
        else:
            print("Nenhum valor problemático específico ('0', '2016L', '23013') encontrado na coluna 'ano'.")
            
        gdf = gdf[~gdf['ano'].astype(str).isin(['0', '2016L', '23013'])]
        gdf['ano'] = to_numeric(gdf['ano'], errors='coerce')
        gdf = gdf.dropna(subset=['ano']) # Remove linhas onde 'ano' se tornou NaN
        gdf['ano'] = gdf['ano'].astype(int)

        # 5. Filtrar os anos desejados (2013 a 2016)
        gdf = gdf[(gdf['ano'] >= 2013) & (gdf['ano'] <= 2016)]
        print(f"\nDataFrame após filtrar anos (2013-2016). Total de linhas: {len(gdf)}")
        if gdf.empty:
            print("Atenção: DataFrame vazio após filtrar os anos de 2013 a 2016. Não há dados para mapear.")
            exit()

        # 6. Verificação e Reprojeção do CRS
        print(f"\nCRS inicial do GeoDataFrame: {gdf.crs}")
        if gdf.crs is None:
            print("AVISO: CRS do GeoDataFrame é None. Assumindo EPSG:4326.")
            gdf = gdf.set_crs('EPSG:4326', allow_override=True)
        elif gdf.crs != 'EPSG:4326':
            print(f"Reprojetando de {gdf.crs} para EPSG:4326 (WGS84)...")
            gdf = gdf.to_crs('EPSG:4326')
        else:
            print("CRS já é EPSG:4326. Nenhuma reprojeção necessária.")
            
        # 7. Validação e Correção de Geometrias
        print("\nVerificando e corrigindo geometrias inválidas com buffer(0)...")
        initial_invalid_count = len(gdf[~gdf.geometry.is_valid])
        print(f"Número de geometrias inválidas antes de buffer(0): {initial_invalid_count}")

        gdf['geometry'] = gdf['geometry'].buffer(0)
        
        invalid_geometries_after_buffer = gdf[~gdf.geometry.is_valid]
        if not invalid_geometries_after_buffer.empty:
            print(f"Número de geometrias inválidas RESTANTES após buffer(0): {len(invalid_geometries_after_buffer)}")
            # Opcional: imprimir algumas das geometrias inválidas restantes para inspeção
            # print("Exemplos de geometrias inválidas restantes:\n", invalid_geometries_after_buffer.head())
        else:
            print("Todas as geometrias são válidas após buffer(0).")

        # Remover geometrias inválidas que ainda persistirem
        gdf = gdf[gdf.geometry.is_valid].copy() # .copy() para evitar SettingWithCopyWarning
        print(f"DataFrame após remover geometrias inválidas. Total de linhas: {len(gdf)}")
        if gdf.empty:
            print("Atenção: DataFrame vazio após remover geometrias inválidas. Não há dados para mapear.")
            exit()

        # 8. Depuração de tipos de geometria
        print("\nTipos de geometria presentes no DataFrame final:")
        print(gdf.geometry.geom_type.value_counts())
        
        # 9. Calcular o centro do mapa
        # Garanta que a união de todas as geometrias é válida antes de calcular o centroide
        # E que não seja vazia.
        if not gdf.geometry.is_empty.all(): # Verifica se há pelo menos uma geometria não vazia
            union_geom = gdf.geometry.unary_union
            if union_geom.is_empty:
                 print("AVISO: A união das geometrias está vazia. Definindo centro padrão.")
                 map_center = [-5.0, -55.0] # Centro da Amazônia para um caso de fallback
            else:
                map_center = union_geom.centroid.y, union_geom.centroid.x
                print(f"Centro do mapa calculado: {map_center}")
        else:
            print("AVISO: Todas as geometrias são vazias. Definindo centro padrão.")
            map_center = [-5.0, -55.0] # Centro da Amazônia para um caso de fallback
            
        m = folium.Map(location=map_center, zoom_start=5)

        # 10. Criar colormap para os anos
        unique_years = sorted(gdf['ano'].unique())
        if not unique_years:
            print("AVISO: Nenhuma informação de 'ano' para o colormap. Usando valores padrão.")
            vmin_year = 2013
            vmax_year = 2016
        else:
            vmin_year = min(unique_years)
            vmax_year = max(unique_years)
            print(f"Anos únicos para o colormap: {unique_years}")

        colormap = cm.LinearColormap(['blue', 'green', 'yellow', 'orange', 'red'],
                                     vmin=vmin_year, vmax=vmax_year)

        # 11. Adicionar polígonos ao mapa para cada ano
        polygons_added_count = 0
        for year in unique_years:
            gdf_year = gdf[gdf['ano'] == year]
            if not gdf_year.empty:
                print(f"Adicionando {len(gdf_year)} geometrias para o ano {year}...")
                try:
                    folium.GeoJson(
                        gdf_year.__geo_interface__, # Melhor prática para folium
                        style_function=lambda feature: {
                            'fillColor': colormap(feature['properties']['ano']),
                            'color': 'black', # Cor da borda
                            'weight': 0.5,    # Espessura da borda (pode ajustar)
                            'fillOpacity': 0.6 # Opacidade do preenchimento
                        },
                        popup=folium.GeoJsonPopup(fields=['estado', 'ano', 'area_km2'], aliases=['Estado', 'Ano', 'Área (km²)']) 
                    ).add_to(m)
                    polygons_added_count += len(gdf_year)
                except Exception as geojson_err:
                    print(f"Erro ao adicionar GeoJson para o ano {year}: {geojson_err}")
            else:
                print(f"Nenhuma geometria para o ano {year} após a filtragem e validação.")
        
        if polygons_added_count == 0:
            print("AVISO: Nenhuma geometria foi adicionada ao mapa. Verifique os dados e filtros.")
            print("Causa provável: dados vazios ou inválidos após o pré-processamento.")

        # 12. Adicionar a legenda do colormap
        colormap.caption = 'Supressão de Vegetação por Ano (2013-2016)'
        m.add_child(colormap)

        # 13. Salvar o mapa em um arquivo HTML
        output_filename = "amazonia_suppression_map_2013_2016_detailed_debug.html"
        m.save(output_filename)
        print(f"\nMapa '{output_filename}' gerado com sucesso!")
        print("--- FIM DA DEPURÇÃO ---")

    except json.JSONDecodeError:
        print("Erro: Falha ao decodificar a resposta JSON. A URL pode não ter retornado JSON válido.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o processamento dos dados: {e}")
else:
    print(f"Falha ao recuperar dados da URL: Código de status {response.status_code} - {response.text}.")