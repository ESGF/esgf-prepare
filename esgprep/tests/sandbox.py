import shutil

import pyessv

from esgprep.tests.TestFolder import Post_Test_Folder
from pathlib import Path


# Scenario 1 :
## On construit la DRS d'un dataset d'input .. avec comme version 1980
#make upgrade /home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr/v20180912 -p cmip6 --max-processes 1 --root /home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd/ --symlink --version 19800101

# On test
#pp = "/home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd/cmip6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr"
#TestFolder(Path(pp)).test()

## On construit la DRS du autre version du meme dataset d'input .. avec comme version 1981
#make upgrade /home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr/v20191003 -p cmip6 --max-processes 1 --root /home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd/ --symlink --version 19810101

# On test
#pp = "/home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd/cmip6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr"
#TestFolder(Path(pp)).test()

# OK maintenant on a fait une erreur .. c'est pas la version 1981 .. mais la version 1982 .. comment on change la version ? sans tout avoir a faire à la main :
# Hyp : on a toujours acces au rep de départ ...
# on peut remove la version 1981 et recreer la version 1982

from esgprep.tests.test_local import esgdrs_make,root_reconstruct,one_file_dataset_path_v1,one_file_dataset_path_v2,clean,esgdrs_remove,esgdrs_latest
"""
clean()
esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v19800101")
esgdrs_make(one_file_dataset_path_v2, "CMIP6", root_reconstruct, "v19810101")
esgdrs_remove()
esgdrs_latest()
"""

"""
clean()
dataset_root = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/AERmon/od550dust/gr"
v1 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/AERmon/od550dust/gr/v20180802"
v2 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/AERmon/od550dust/gr/v20181022"
v3 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/AERmon/od550dust/gr/v20181123"
v4 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/AERmon/od550dust/gr/v20200326"
esgdrs_make(v1, "CMIP6", root_reconstruct, "v19000101")
esgdrs_make(v2, "CMIP6", root_reconstruct, "v19000102")
esgdrs_make(v3, "CMIP6", root_reconstruct, "v19000103")
esgdrs_make(v4, "CMIP6", root_reconstruct, "v19000104")

print("ON VA ESSAYER DE SUPPRIMER")
#/home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd/cmip6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/AERmon/od550dust/gr/v00000003
#print(root_reconstruct+"/bdd/cmip6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/AERmon/od550dust/gr")
esgdrs_remove("/home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd/cmip6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/AERmon/od550dust/gr", "v19000103")
"""

# OK ... On va essayer autrement ..
def DoWork():
    clean()
    esgdrs_make("/home/ltroussellier/Bureau/dev/bddFromCiclad/scenario1/etape1", "CMIP6", root_reconstruct, "v20180802")

def DoWork2():
    clean()
    esgdrs_make("/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn/v20190725","CMIP6",root_reconstruct,"v20190725")

def current():
    one_file_dataset_path_v1 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr/v20180912"
    one_file_dataset_path_v2 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr/v20191003"
    clean()
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20180912")
    esgdrs_make(one_file_dataset_path_v2, "CMIP6", root_reconstruct, "v20191003")

def test():
    t = pyessv.parse_namespace("compil:cmip6:version:v20191003", strictness=4)
    print(t)
    t = pyessv.parse_namespace("compil:cmip6:version:v20200224", strictness=4)
    print(t)

def test2():
    d = Path("/home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr/latest").resolve()
    print(d)

def test3():
    clean()
    multi_file_dataset_2_path_v1 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/NCC/NorESM2-LM/piControl/r1i1p1f1/AERmon/od550lt1aer/gn/v20190815"
    multi_file_dataset_2_path_v2 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/NCC/NorESM2-LM/piControl/r1i1p1f1/AERmon/od550lt1aer/gn/v20190920"
    multi_file_dataset_2_path_v3 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/NCC/NorESM2-LM/piControl/r1i1p1f1/AERmon/od550lt1aer/gn/v20210118"

    multi_file_dataset_path_v1 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn/v20190725"
    multi_file_dataset_path_v2 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn/v20191112"
    #multi_file_dataset_path_v3 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn/v20200331"
    esgdrs_make(multi_file_dataset_2_path_v1, "CMIP6", root_reconstruct, "v20190815", 1, "symlink", rescan = True)
    esgdrs_make(multi_file_dataset_2_path_v2, "CMIP6", root_reconstruct, "v20190920", 1, "symlink", rescan = True)
    esgdrs_make(multi_file_dataset_2_path_v3, "CMIP6", root_reconstruct, "v20210118", 1, "symlink", rescan = True)
def clean():
    if Path(root_reconstruct + "/CMIP6").exists():
        shutil.rmtree(root_reconstruct + "/CMIP6")

test3()
#test2()
#current()

# compil:cmip6:version:v20180912
# compil:cmip6:version:v20191003

# OYYY :  Namespace(cmd='make', log=None, debug=False, action='upgrade', directory=['/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr/v20180912'], project='CMIP6', ignore_dir=re.compile('^.*/(files|\\.[\\w]*).*$'), include_file=['^.*\\.nc$'], exclude_file=['^\\..*$'], color=False, no_color=False, max_processes=1, root='/home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd', version='v20180912', set_value=None, set_key=None, rescan=True, commands_file=None, overwrite_commands_file=False, upgrade_from_latest=False, ignore_from_latest=None, ignore_from_incoming=None, copy=False, link=False, symlink=True, no_checksum=False, checksums_from=None, quiet=False, prog='esgdrs')
# OYYY :  Namespace(cmd='make', log=None, debug=False, action='upgrade', directory=['/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr/v20191003'], project='CMIP6', ignore_dir=re.compile('^.*/(files|\\.[\\w]*).*$'), include_file=['^.*\\.nc$'], exclude_file=['^\\..*$'], color=False, no_color=False, max_processes=1, root='/home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd', version='v20191003', set_value=None, set_key=None, rescan=True, commands_file=None, overwrite_commands_file=False, upgrade_from_latest=False, ignore_from_latest=None, ignore_from_incoming=None, copy=False, link=False, symlink=True, no_checksum=False, checksums_from=None, quiet=False, prog='esgdrs')


#esgdrs_make("/home/ltroussellier/Bureau/dev/bddFromCiclad/scenario1/etape2", "CMIP6", root_reconstruct, "v19000102")
# AH ... on upgrade pas from latest ...
#clean()


"""
import pyessv
pyessv.load("compil")
print(pyessv.get_cached()[0]["CMIP6"])
terms = pyessv.parse_identifer(pyessv.get_cached()[0]["CMIP6"], pyessv.IDENTIFIER_TYPE_FILENAME, "od550dust_AERmon_IPSL-CM6A-LR_piControl_r1i1p1f1_gr_187001-234912.nc")
print(terms)
"""