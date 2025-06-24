import pandas as pd
import geopandas as gpd
import os
import fiona
from shapely import wkt

def file_csv_exists(*args: str) -> bool:
    file_path: str = os.path.join(*args)
    if not file_path.endswith('.csv'):
        return False
    return True

def read_geodataframe_fiona(*args: str) -> bool:
    file_path = os.path.join(*args)
    try:
        with fiona.open(file_path) as collection:
            for feature in collection:
                print(feature)
        return True
    except Exception as e:
        print(f"Error to read file using fiona: {e}")
        return False

def read_geodataframe(*args: str) -> gpd.GeoDataFrame | None:

    file_path: str = os.path.join(*args)
    
    if not file_csv_exists(file_path):
        raise ValueError(f"The CSV file {file_path} is not exits.")
        return None
    
    df: pd.DataFrame = pd.read_csv(file_path, encoding='latin-1')
    if 'geometry' not in df.columns:
        raise ValueError(
            f"The CSV file {file_path} does not contain a 'geometry' column.")
        return None
    
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs='EPSG:4326')
    return gdf

def columns_in_geodataframe(
    gdf: gpd.GeoDataFrame, columns: list[str]) -> bool:
    for column in columns:
        if column not in gdf.columns:
            print(f"Column '{column}' not found in GeoDataFrame.")
            return False
    return True

def geodataframe_analysis_by_state(gpd: gpd.GeoDataFrame) -> None:
    if not columns_in_geodataframe(gpd, ['ano', 'area_km2']):
        print("Required columns are missing in the GeoDataFrame.")
        return None
    
    count_by_year = gpd['ano'].value_counts().sort_index()
    print("1. Contagem de ocorrências por ano (número de registros):\n",
          count_by_year)
    print()

    total_area_by_year = gpd.groupby('ano')['area_km2'].sum().reset_index()
    total_area_by_year.columns = ['Ano', 'Area_Total_km2']
    print("2. Somatório da área suprimida por ano:\n", total_area_by_year)
    print()

    return None


if __name__ == "__main__":
    gpd_ac_geodata: gpd.GeoDataFrame = read_geodataframe(
        'state_geodata', 'AC_geodata.csv')
    gpd_am_geodata: gpd.GeoDataFrame = read_geodataframe(
        'state_geodata', 'AM_geodata.csv')
    gpd_ap_geodata: gpd.GeoDataFrame = read_geodataframe(
        'state_geodata', 'AP_geodata.csv')
    gpd_ma_geodata: gpd.GeoDataFrame = read_geodataframe(
        'state_geodata', 'MA_geodata.csv')
    gpd_mt_geodata: gpd.GeoDataFrame = read_geodataframe(
        'state_geodata', 'MT_geodata.csv')
    gpd_pa_geodata: gpd.GeoDataFrame = read_geodataframe(
        'state_geodata', 'PA_geodata.csv')
    gpd_ro_geodata: gpd.GeoDataFrame = read_geodataframe(
        'state_geodata', 'RO_geodata.csv')
    gpd_rr_geodata: gpd.GeoDataFrame = read_geodataframe(
        'state_geodata', 'RR_geodata.csv')
    gpd_to_geodata: gpd.GeoDataFrame = read_geodataframe(
        'state_geodata', 'TO_geodata.csv')

    geodataframe_analysis_by_state(gpd_ac_geodata)
    geodataframe_analysis_by_state(gpd_am_geodata)
    geodataframe_analysis_by_state(gpd_ap_geodata)
    geodataframe_analysis_by_state(gpd_ma_geodata)
    geodataframe_analysis_by_state(gpd_mt_geodata)
    geodataframe_analysis_by_state(gpd_pa_geodata)
    geodataframe_analysis_by_state(gpd_ro_geodata)
    geodataframe_analysis_by_state(gpd_rr_geodata)
    geodataframe_analysis_by_state(gpd_to_geodata)