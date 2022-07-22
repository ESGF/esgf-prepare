
from esgprep.tests.TestFolder import TestFolder
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
#clean()
#esgdrs_make("/home/ltroussellier/Bureau/dev/bddFromCiclad/scenario1/etape1", "CMIP6", root_reconstruct, "v19000101")
#esgdrs_make("/home/ltroussellier/Bureau/dev/bddFromCiclad/scenario1/etape2", "CMIP6", root_reconstruct, "v19000102")
# AH ... on upgrade pas from latest ...
clean()