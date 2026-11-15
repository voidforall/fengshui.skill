"""Full-city map contracts: complete partition, real source snapshots and safe rendering."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/city-wuxing-map'
SPEC=importlib.util.spec_from_file_location('city_generator',SKILL/'scripts/generate.py')
generator=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(generator)
MODEL_SPEC=importlib.util.spec_from_file_location('city_model',SKILL/'scripts/city_model.py')
model=importlib.util.module_from_spec(MODEL_SPEC);MODEL_SPEC.loader.exec_module(model)
try:
    from shapely.geometry import shape,Point
except ImportError:
    shape=None

SOURCE=[{'title':'Test data','url':'https://www.openstreetmap.org/copyright'}]

def polygon(x1,y1,x2,y2):
    return {'type':'Polygon','coordinates':[[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]]]}

def fixture():
    regions=[]
    for i in range(2):
        a={'primary':'土' if i==0 else '木','secondary':[], 'confidence':'低',
           'confidence_reason':'Synthetic fixture, not a real geography claim.',
           'reason':'Test interpretation','facts':['Synthetic land-cover measurement'],
           'limitations':'Test only','sources':SOURCE}
        regions.append({'id':f'cell-{i}','name':f'Test region {i}','geometry':polygon(i,50,i+1,51),
                        'label_position':[i+.5,50.5],'boundary':{'kind':'统计分区','description':'Synthetic partition','sources':SOURCE},
                        'preferred_method':'function','analyses':{'landscape':copy.deepcopy(a),'function':copy.deepcopy(a)},'evidence':[]})
    return {'schema_version':3,'city':'Test city','subtitle':'Test','summary':'Synthetic fixture',
            'reviewed_at':'2026-11-15','coordinate_note':'WGS84 test geometry',
            'coverage':{'kind':'full-city','name':'Test scope','geometry':polygon(0,50,2,51),'sources':SOURCE,'cell_size_m':1000,'focus':[.5,50.5]},'regions':regions}


@unittest.skipIf(shape is None,'Install city-wuxing-map/requirements.txt for GIS coverage tests')
class TestCityMap(unittest.TestCase):
    def setUp(self):self.data=fixture()

    def test_complete_partition_is_proven_from_geometries(self):
        generator.validate(self.data)
        report=generator.validate_coverage(self.data)
        self.assertAlmostEqual(100,report['coverage_percent'])
        self.assertAlmostEqual(0,report['overlap_percent'])
        self.assertAlmostEqual(0,report['outside_percent'])

    def test_missing_overlap_and_outside_cannot_be_called_full_city(self):
        cases=[]
        gap=fixture();gap['regions'].pop();gap['coverage_report']={'coverage_percent':100};cases.append(gap)
        overlap=fixture();extra=copy.deepcopy(overlap['regions'][0]);extra['id']='extra';overlap['regions'].append(extra);cases.append(overlap)
        outside=fixture();extra=copy.deepcopy(outside['regions'][0]);extra.update(id='outside',geometry=polygon(3,50,4,51),label_position=[3.5,50.5]);outside['regions'].append(extra);cases.append(outside)
        for data in cases:
            with self.subTest(kind=len(data['regions'])):
                with self.assertRaisesRegex(ValueError,'全城分区不完整'):generator.validate(data)

    def test_each_unit_requires_both_classifications_and_confidence(self):
        for mutate in (lambda r:r['analyses'].pop('landscape'),
                       lambda r:r['analyses']['function'].update(confidence=''),
                       lambda r:r['analyses']['function'].update(primary=''),
                       lambda r:r['analyses']['function'].update(secondary=['土']),
                       lambda r:r['analyses']['function'].update(sources=[]),
                       lambda r:r['boundary'].update(sources=[])):
            data=fixture();mutate(data['regions'][0])
            with self.assertRaises(ValueError):generator.validate(data)

    def test_legacy_points_and_partial_regions_are_rejected(self):
        for data in ({'city':'London','places':[{'lat':51.5,'lon':0}]},dict(fixture(),schema_version=2)):
            with self.assertRaisesRegex(ValueError,'全城数据'):generator.validate(data)
        self.data['coverage']['kind']='selected-examples'
        with self.assertRaisesRegex(ValueError,'真实城市'):generator.validate(self.data)

    def test_bad_coordinates_and_invalid_topology_are_rejected(self):
        invalid=[{'type':'Point','coordinates':[0,51]},
                 {'type':'Polygon','coordinates':[]},
                 {'type':'Polygon','coordinates':[[[0,50],[1,51],[0,51],[1,50],[0,50]]]},
                 {'type':'Polygon','coordinates':[[[0,50],[1,50],[2,50],[0,50]]]},
                 polygon(0,90,1,91)]
        for geometry in invalid:
            data=fixture();data['regions'][0]['geometry']=geometry
            with self.assertRaises(ValueError):generator.validate(data)

    def test_multipolygon_with_hole_can_be_completed_by_another_region(self):
        outer=polygon(0,50,2,52)['coordinates'][0]
        hole=polygon(.5,50.5,1.5,51.5)['coordinates'][0]
        self.data['coverage']['geometry']=polygon(0,50,2,52)
        self.data['regions'][0].update(geometry={'type':'MultiPolygon','coordinates':[[outer,hole]]},label_position=[.25,50.25])
        self.data['regions'][1].update(geometry=polygon(.5,50.5,1.5,51.5),label_position=[1,51])
        generator.validate(self.data)
        self.assertAlmostEqual(100,generator.validate_coverage(self.data)['coverage_percent'])

    def test_search_configuration_and_standalone_script(self):
        self.data['search']={'country_code':'fr','placeholder':'75001 / Paris','hint':'Adresse locale'}
        output=generator.render(self.data)
        self.assertIn('createLookup',output)
        self.assertNotIn('__SEARCH_JS__',output)
        self.assertIn('id="search-form"',output)
        self.data['search']['photon_url']='javascript:alert(1)'
        with self.assertRaises(ValueError): generator.validate(self.data)
        self.data['search']={'country_code':'United Kingdom'}
        with self.assertRaises(ValueError): generator.validate(self.data)

    def test_data_cannot_escape_json_script_or_title(self):
        payload='</script><script>alert("injected")</script>'
        self.data['city']=payload;self.data['regions'][0]['analyses']['function']['reason']=payload
        output=generator.render(self.data);self.assertNotIn(payload,output)
        content=output.split('<script id="city-data" type="application/json">',1)[1].split('</script>',1)[0]
        self.assertEqual(payload,json.loads(content)['regions'][0]['analyses']['function']['reason'])
        self.assertAlmostEqual(100,json.loads(content)['coverage_report']['coverage_percent'])

    def test_custom_city_runs_as_standalone_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            temp=Path(directory);installed=temp/'city-wuxing-map'
            shutil.copytree(SKILL,installed,ignore=shutil.ignore_patterns('__pycache__'))
            source=temp/'custom.json';output=temp/'out/map.html';source.write_text(json.dumps(self.data))
            result=subprocess.run([sys.executable,str(installed/'scripts/generate.py'),'--input',str(source),'--output',str(output)],cwd=temp,capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertIn('Test city',output.read_text())
            self.assertIn('coverage_percent',output.read_text())

    def test_failed_cli_preserves_source_and_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'city.json';output=Path(directory)/'map.html'
            source.write_text(json.dumps(self.data));original=source.read_bytes()
            cmd=[sys.executable,str(SKILL/'scripts/generate.py'),'--input',str(source)]
            result=subprocess.run(cmd+['--output',str(source)],capture_output=True)
            self.assertEqual(2,result.returncode);self.assertEqual(original,source.read_bytes())
            self.data['regions'].pop();source.write_text(json.dumps(self.data));output.write_text('keep existing result')
            result=subprocess.run(cmd+['--output',str(output)],capture_output=True)
            self.assertEqual(2,result.returncode);self.assertEqual('keep existing result',output.read_text())

    def test_custom_basemap_needs_attribution_and_xyz(self):
        for settings in (dict(generator.DEFAULT_BASEMAP,url='https://example.com/static.png'),
                         dict(generator.DEFAULT_BASEMAP,attribution=''),
                         dict(generator.DEFAULT_BASEMAP,url='javascript:alert(1)')):
            self.data['basemap']=settings
            with self.assertRaises(ValueError):generator.validate(self.data)

    def test_frozen_city_examples_are_complete_and_match_template(self):
        for slug in ('london','new-york'):
            with self.subTest(city=slug):
                data=json.loads((SKILL/'examples'/f'{slug}.json').read_text())
                generator.validate(data)
                self.assertGreater(len(data['regions']),500)
                self.assertEqual(set('金木水火土'),{r['analyses']['function']['primary'] for r in data['regions']})
                for method in ('landscape','function'):
                    for r in data['regions']:
                        self.assertIn(r['analyses'][method]['primary'],'金木水火土')
                        self.assertIn(r['analyses'][method]['confidence'],('低','中','高'))
                self.assertEqual(generator.render(data),(ROOT/'docs/examples'/f'{slug}-wuxing.html').read_text())
                for name,spec in data['model']['source_manifest']['files'].items():
                    self.assertEqual(spec['sha256'],hashlib.sha256((SKILL/'examples/sources'/name).read_bytes()).hexdigest())

    def test_outer_city_points_are_covered_not_only_the_old_landmarks(self):
        cases={
            'london':[(-.45,51.52),(.22,51.57),(-.10,51.36),(-.10,51.65),(-.1278,51.5074)],
            'new-york':[(-74.15,40.58),(-73.82,40.72),(-73.87,40.85),(-73.95,40.65),(-74.006,40.7128)],
        }
        for slug,points in cases.items():
            data=json.loads((SKILL/'examples'/f'{slug}.json').read_text())
            polygons=[shape(r['geometry']) for r in data['regions']]
            for lon,lat in points:
                point=Point(lon,lat)
                self.assertTrue(shape(data['coverage']['geometry']).covers(point),(slug,lon,lat))
                self.assertTrue(any(p.covers(point) for p in polygons),(slug,lon,lat))


class TestFullCityModel(unittest.TestCase):
    def metrics(self,**values):
        result=dict(water=0,vegetation=0,open=0,built=1,commercial_industrial=0,retail=0,culture_area=0,culture_count=0,sample_count=400,sampling='50m多数分类统计',area_km2=1,function_basis='OSM用地及设施')
        result.update(values);return result

    def test_five_elements_have_traceable_decision_inputs(self):
        cases=[('水',dict(water=1,built=0)),('木',dict(vegetation=1,built=0)),('土',{}),
               ('金',dict(commercial_industrial=.8)),('火',dict(retail=.8))]
        for expected,values in cases:
            self.assertEqual(expected,model.analyse(self.metrics(**values),'function')['primary'])

    def test_one_point_does_not_define_an_entire_urban_unit(self):
        self.assertEqual('土',model.analyse(self.metrics(culture_count=1),'function')['primary'])
        self.assertEqual('火',model.analyse(self.metrics(culture_count=5),'function')['primary'])

    def test_planning_proxy_and_small_samples_lower_confidence(self):
        a=model.analyse(self.metrics(commercial_industrial=1,function_basis='规划许可用途（非现状）'),'function')
        self.assertEqual('低',a['confidence']);self.assertIn('许可用途',a['confidence_reason'])
        b=model.analyse(self.metrics(water=1,built=0,sample_count=1,sampling='边界小单元代表点补样'),'landscape')
        self.assertEqual('低',b['confidence'])

    def test_landcover_mode_does_not_invent_commerce(self):
        a=model.analyse(self.metrics(commercial_industrial=1),'landscape')
        b=model.analyse(self.metrics(commercial_industrial=1),'function')
        self.assertEqual('土',a['primary']);self.assertEqual('金',b['primary'])

if __name__=='__main__':unittest.main()
