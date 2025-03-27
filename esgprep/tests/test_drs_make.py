from netCDF4 import Dataset
from esgvoc.apps.drs.generator import DrsGenerator


def test_build_directory():
    ds = Dataset("input_files/tas_Amon_CanESM5_historical_r1i1p2f1_gn_185001-201412.nc")
    dg = DrsGenerator("cmip6")
    # for now : 'CMIP6/CMIP/CCCma/CanESM5/historical/[MISSING]/Amon/tas/gn/v20190429'
    # confusion in the vocabulary between member_id and variant_label
    res = dg.generate_directory_from_mapping({**ds.__dict__, **{"member_id":ds.variant_label} })
    print(res) 
    assert(len(res.errors)==0)
