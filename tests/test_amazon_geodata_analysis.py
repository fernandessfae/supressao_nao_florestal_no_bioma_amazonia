import unittest
import sys
import os

dir_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(dir_root)

from amazon_geodata_analysis import (
    file_csv_exists, read_geodataframe,
    read_geodataframe_fiona, columns_in_geodataframe)


class TestIsFileCSVExists(unittest.TestCase):
    def test_file_csv_exists(self):
        self.assertTrue(file_csv_exists(
            dir_root, 'state_geodata', 'AC_geodata.csv'))

    def test_file_csv_not_exists(self):
        self.assertFalse(file_csv_exists(
            dir_root, 'state_geodata', 'non_existent_file.txt'))


class TestReadGeoDataFrameFiona(unittest.TestCase):
    def test_read_geodataframe_fiona(self):
        self.assertTrue(read_geodataframe_fiona(
            dir_root, 'state_geodata', 'AC_geodata.csv'))


class TestReadGeoDataFrame(unittest.TestCase):
    def test_read_geodataframe(self):
        import geopandas as gpd
        self.assertIsInstance(read_geodataframe(
            dir_root, 'state_geodata', 'AC_geodata.csv'), gpd.GeoDataFrame)

class TestColumnsInGeoDataFrame(unittest.TestCase):
    def test_columns_in_geodataframe(self):
        import geopandas as gpd
        gdf = read_geodataframe(
            dir_root, 'state_geodata', 'AC_geodata.csv')
        self.assertTrue(columns_in_geodataframe(gdf, ['ano','area_km2']))
        self.assertFalse(columns_in_geodataframe(gdf, 'data'))
        

if __name__ == '__main__':
    unittest.main(verbosity=2)


