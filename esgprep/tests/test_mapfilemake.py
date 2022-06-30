import re
from argparse import Namespace
from typing import Callable
from hypothesis import given, settings, HealthCheck
from hypothesis.strategies import text, integers, composite, SearchStrategy

from esgprep.esgmapfile import run
from esgprep.tests.MapFileData import MapFileData, mapfiledataread, compare
import csv


@composite
def cmip6mapfilepath(draw: Callable[[SearchStrategy[int]], int], min_value: int = 1, max_value: int = 1_151_851):
    rand_val = draw(integers(min_value, max_value))
    return get_mapfile_source_cmip6(rand_val)


def get_mapfile_source_cmip6(pick: int):
    cmip6_all_path = "/climserv-home/ltroussellier/dev/FakeInEsgprep/bddCMIP6MapFile.csv"
    proj = "CMIP6"

    print("Opening CMIP6 mapfile number ", pick)
    # Pick the mapfile in the mapfilelistfile
    with open(cmip6_all_path, newline='') as f:
        data = list(csv.reader(f))
        path = data[pick][0]

    # What is the directory and filename of the mapfile
    directory = "/".join(path.split("/")[2:-1])
    filename = path.split("/")[-1]

    # root dir where are the netcdf files of this mapfile (deduce from the mapfile name)
    nc_dir = "/bdd/" + proj + "/" + "/".join(filename.split(".")[1:-1])
    print("netcdfFile root dir from picked mapfile", nc_dir)

    return directory, filename, nc_dir


#@given(text(), text())
#@settings(max_examples=1)
#def test_compare(path1: str, path2: str) -> None:
#    assert type(compare(path1, path2)) == bool


@given(cmip6mapfilepath())
@settings(max_examples=10, suppress_health_check=(HealthCheck.too_slow,), deadline=None)
def test_compare_map(infos):
    directory, filename, nc_dir = infos
    #print(directory, filename, nc_dir)
    # Need real mapfile infos
    real_mapfile_info = mapfiledataread("/bdd/"+directory+"/"+filename)

    print("realMapfile: ", real_mapfile_info)
    # Need netcdfiles in DRS from a specific root dir
    # Not really in fact ... we need it just to generate the mapfile
    # what we need is the root of those file to pass it to esgmapfile
    # is nc_dir is enough ?

    # Need Generate mapfile
    print("MAPFILE GENERATION")
    arg = Namespace(cmd='make', i='/esg/config/esgcet', log=None, debug=False, project='cmip6',
              mapfile='{dataset_id}.v{version}.map', outdir='/home/ltroussellier/dev_esgprep/esgprep/mapfiles',
              all_versions=False, version=None, latest_symlink=False, ignore_dir=re.compile('^.*/(files|\\.[\\w]*).*$'),
              include_file=['^.*\\.nc$'], exclude_file=['^\\..*$'], max_processes=1, color=False, no_color=False,
              directory=[nc_dir], no_checksum=False,
              checksums_from=None, tech_notes_url=None, tech_notes_title=None, no_cleanup=False, prog='esgmapfile')

    run(arg)
    # assert real and fake have same infos besides dir path
    print("---------------------------------------")
    print("COMPARASON BETWEEN REAL AND RECONSTRUCT")
    print("---------------------------------------")
    # filename example = CMIP6.C4MIP.IPSL.IPSL-CM6A-LR.1pctCO2-bgc.r1i1p1f1.Omon.umo.gn.20180914.map
    # filename in out dir = mapfiles/CMIP6.C4MIP.IPSL.IPSL-CM6A-LR.1pctCO2-bgc.r1i1p1f1.Omon.umo.gn.v20180914.map
    # we need to remove the "v" from version or not .. bug ?
    # m_fake_filename = filename[0:filename.rindex("v")]+filename[filename.rindex("v")+1:]
    # fake_mapfile_info = mapfiledataread("mapfiles/"+m_fake_filename)
    # fake_mapfile_info = mapfiledataread("mapfiles/" + filename)
    fake_mapfile_info = mapfiledataread(arg.outdir+"/" + filename)
    print("---------------------------------------")
    print("THE REAL: ", real_mapfile_info)
    print("THE FAKE: ", fake_mapfile_info)
    print("---------------------------------------")

    testBool = real_mapfile_info == fake_mapfile_info
    print("ON FINAL IL SONT EGAUX : ",testBool)
    print("---------------------------------------")
    assert testBool
