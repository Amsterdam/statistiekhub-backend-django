import pandas as pd
import pytest
from django.core.exceptions import ValidationError

from statistiek_hub.utils.formatters import GEOJSON, SCSV

testgeojson = {
    "type": "FeatureCollection",
    "name": "sql_statement",
    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::28992" } },
    "features": [
    { "type": "Feature", "properties": { "code": "A01f"}, "geometry": { "type": "Polygon", "coordinates": [ [ [ 121181.182, 487312.011 ], [ 121179.256, 487345.803000000014435 ], [ 121180.518, 487371.117000000027474 ], [ 121062.5, 487381.508000000030734 ], [ 121060.131, 487368.90400000003865 ], [ 121056.237, 487356.819000000017695 ], [ 121038.176, 487277.51500000001397 ], [ 121010.554, 487052.617000000027474 ], [ 120989.112, 486886.109 ], [ 120989.888, 486881.76300000003539 ], [ 120990.653, 486877.48499999998603 ], [ 121004.68, 486852.117000000027474 ], [ 121037.134, 486810.831 ], [ 121069.967, 486853.661000000021886 ], [ 121075.887, 486862.930999999982305 ], [ 121081.77, 486874.334000000031665 ], [ 121086.227, 486885.482000000018161 ], [ 121089.633, 486896.995 ], [ 121093.389, 486946.163999999989755 ], [ 121104.353, 486986.232000000018161 ], [ 121118.176, 487028.769000000029337 ], [ 121142.589, 487079.461000000010245 ], [ 121152.07, 487094.709000000031665 ], [ 121160.312, 487111.270000000018626 ], [ 121179.5, 487164.407 ], [ 121182.856, 487176.13900000002468 ], [ 121184.848, 487188.178000000014435 ], [ 121185.447, 487200.87400000001071 ], [ 121183.677, 487268.332 ], [ 121181.182, 487312.011 ] ] ] } },
]}

@pytest.fixture
def csv_file():
    d = {11: None, 12: 7500.0}
    df = pd.DataFrame(d.items(), columns=["id", "test_int"]) 
    return df.to_csv(index=False)

@pytest.fixture
def csv_file_semicolon():
    d = {11: None, 12: 7500.0}
    df = pd.DataFrame(d.items(), columns=["id", "test_int"]) 
    return df.to_csv(index=False, sep=';')


class TestFormatters:
        
    def test_GEOJSON(self):
        gj = GEOJSON()
        ds = gj.create_dataset(testgeojson)
        assert ds.headers == ['code','geom']

    def test_SCSV_raise(self,csv_file):
        sc = SCSV()
        with pytest.raises(ValidationError) as e:
            sc.create_dataset(csv_file)
        assert str(e.value) == "['file is using `,` delimiter, but semicolon_csv format is with `;` delimiter']"
        
    def test_SCSV(self,csv_file_semicolon):
        sc = SCSV()
        ds = sc.create_dataset(csv_file_semicolon)
        assert ds.headers == ['id','test_int']
