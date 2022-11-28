import time
from argparse import Namespace
import re

import pytest
from esgprep._exceptions import DuplicatedDataset
from esgprep.esgdrs import run
from pathlib import Path
from esgprep.tests.post_test_folder import Post_Test_Folder
from datetime import datetime
import shutil

# l'idée ici .. c'est de faire une procédure de test :

# on a des files incoming dans une architecture de fichiers qu'on ne maitrise pas :
# pour moi ça sera ici :
root_path_incoming_files = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd"
# exemple de dataset mono-fichier :
one_file_dataset_path_v1 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr/v20180912"
one_file_dataset_path_v2 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr/v20191003"
# exemple de dataset multi-files:
multi_file_dataset_path_v1 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn/v20190725"
multi_file_dataset_path_v2 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn/v20191112"
multi_file_dataset_path_v3 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn/v20200331"
# autre exemple mutil-files :
multi_file_dataset_2_path_v1 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/NCC/NorESM2-LM/piControl/r1i1p1f1/AERmon/od550lt1aer/gn/v20190815"
multi_file_dataset_2_path_v2 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/NCC/NorESM2-LM/piControl/r1i1p1f1/AERmon/od550lt1aer/gn/v20190920"
multi_file_dataset_2_path_v3 = "/home/ltroussellier/Bureau/dev/bddFromCiclad/bdd/CMIP6/CMIP/NCC/NorESM2-LM/piControl/r1i1p1f1/AERmon/od550lt1aer/gn/v20210118"

# on veut tester

##### make tous les arguments possibles
root_reconstruct = "/home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd"


def get_args(incoming_folder: str, project: str, root_drs: str,
             version_name: str = 'v{}'.format(datetime.now().strftime('%Y%m%d')),
             proc: int = 1,
             mode: str = "symlink",
             rescan: bool = True):
    return Namespace(cmd='make',
                     log=None, debug=False,
                     action='upgrade',
                     directory=[incoming_folder],
                     project=project, ignore_dir=re.compile('^.*/(files|\\.[\\w]*).*$'), include_file=['^.*\\.nc$'],
                     exclude_file=['^\\..*$'],
                     color=False, no_color=False,
                     max_processes=proc,
                     root=root_drs,
                     version=version_name,
                     set_value=None, set_key=None,
                     rescan=rescan,
                     commands_file=None, overwrite_commands_file=False, upgrade_from_latest=False,
                     ignore_from_latest=None, ignore_from_incoming=None,
                     copy=True if mode == "copy" else False,
                     link=True if mode == "link" else False,
                     symlink=True if mode == "symlink" else False,
                     no_checksum=False, checksums_from=None, quiet=False,
                     prog='esgdrs')


Namespace(cmd='make', i='/esg/config/esgcet', log=None, debug=False, action='upgrade',
          directory=['/home/ltroussellier/Bureau/dev/bddFromCiclad/scenario1/etape1'], project='cmip6',
          ignore_dir=re.compile('^.*/(files|\\.[\\w]*).*$'), include_file=['^.*\\.nc$'], exclude_file=['^\\..*$'],
          color=False, no_color=False, max_processes=4,
          root='/home/ltroussellier/Bureau/dev/bddFromCiclad/reconstruct_bdd',
          version='v20220722', set_value=None, set_key=None, rescan=False, commands_file=None,
          overwrite_commands_file=False,
          upgrade_from_latest=False, ignore_from_latest=None, ignore_from_incoming=None, copy=False, link=False,
          symlink=False, no_checksum=False, checksums_from=None, quiet=False, prog='esgdrs')


def esgdrs_make(incoming_folder: str, project: str, root_drs: str,
                version_name: str = 'v{}'.format(datetime.now().strftime('%Y%m%d')),
                proc=1, mode: str = "symlink", rescan: bool = True):
    # get the Namespace to "simulate" argument command line
    arg = get_args(incoming_folder, project, root_drs, version_name, proc, mode, rescan)
    # run the drs make with thoses arguments
    run(arg)


def esgdrs_remove(folder, version_name,proc = 1):
    arg = Namespace(cmd='remove',
                    log=None, debug=False, action='upgrade',
                    directory=[folder],
                    project='cmip6', ignore_dir=re.compile('^.*/(files|\\.[\\w]*).*$'), include_file=['^.*\\.nc$'],
                    exclude_file=['^\\..*$'],
                    color=False, no_color=False, max_processes=proc,
                    rescan=True, dataset_list=None, dataset_id=None,
                    version=version_name, all_versions=False, prog='esgdrs')
    run(arg)


def esgdrs_latest(folder):
    arg = Namespace(cmd='latest',
                    log=None, debug=False, action='upgrade',
                    directory=[folder],
                    project='cmip6', ignore_dir=re.compile('^.*/(files|\\.[\\w]*).*$'), include_file=['^.*\\.nc$'],
                    exclude_file=['^\\..*$'],
                    color=False, no_color=False, max_processes=1, rescan=True, prog='esgdrs')
    run(arg)


def clean():
    if Path(root_reconstruct + "/CMIP6").exists():
        shutil.rmtree(root_reconstruct + "/CMIP6")


def is_same_path_and_good_folder_structure(dataset_version_path):
    ###### Same path until dataset ? ######
    # where does our incoming dataset come from
    dataset_control_folder = Path(dataset_version_path).parent.as_posix()
    dataset_control_folder_without_root = dataset_control_folder.split(root_path_incoming_files + "/CMIP6/")[1]
    print("incoming dataset folder : ", dataset_control_folder)
    print("incoming dataset DRS : ", dataset_control_folder_without_root)

    # where does it has to be reconstruct :
    dataset_reconstruct_folder = root_reconstruct + "/CMIP6/" + dataset_control_folder_without_root
    print("reconstruct dataset DRS folder : ", dataset_control_folder_without_root)
    assert Path(dataset_reconstruct_folder).exists()
    print("------ GOT the same DRS path between Control and Reconstruct ---------")

    ##### Folder is correctly constructed
    folder_test = Post_Test_Folder(Path(dataset_reconstruct_folder))
    folder_test.test()


def test_default():
    clean()
    # DRS creation
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v00000001")

    # what do we expect :
    # same structure as in root_path_incoming_files but in root_reconstruct
    # thus, we ll look that the path on the reconstruct is the same as the control one
    # and we ll test that the dataset folder is "fine" link d***** v***** etc ..
    is_same_path_and_good_folder_structure(one_file_dataset_path_v1)

    clean()


def test_one_version_after_another():
    clean()
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20180912")
    is_same_path_and_good_folder_structure(one_file_dataset_path_v1)
    esgdrs_make(one_file_dataset_path_v2, "CMIP6", root_reconstruct, "v20191003")
    is_same_path_and_good_folder_structure(one_file_dataset_path_v2)
    #clean()


def test_no_version_supply():
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct)
    is_same_path_and_good_folder_structure(one_file_dataset_path_v1)
    clean()


def test_supply_same_dataset_2_times():
    clean()
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20180912")
    is_same_path_and_good_folder_structure(one_file_dataset_path_v1)
    with pytest.raises(DuplicatedDataset) as e_info:
        esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20180912")
    is_same_path_and_good_folder_structure(one_file_dataset_path_v1)
    # ODO : il devrait y avoir un probleme ... et il y en a pas ... ???
    clean()


def test_not_rescan():
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v00000001",1, "symlink", True)
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v00000001",1, "symlink", False)
    is_same_path_and_good_folder_structure(one_file_dataset_path_v1)
    # OK Skip the second one ...
    # but still the folder is correctly formatted
    clean()




def test_multifile():
    clean()
    esgdrs_make(multi_file_dataset_2_path_v1, "CMIP6", root_reconstruct, "v20190815", 1, "symlink", True)
    esgdrs_make(multi_file_dataset_2_path_v2, "CMIP6", root_reconstruct, "v20190920", 1, "symlink", True)
    # esgdrs_make(multi_file_dataset_2_path_v3, "CMIP6", root_reconstruct, "v20210118", 1, "symlink", True)

    is_same_path_and_good_folder_structure(multi_file_dataset_2_path_v1)
    # OK Skip the second one ...
    # but still the folder is correctly formatted

    #clean()


# il faut tester l'histoire des liens de fichiers dans le cas où les fichiers sont les mêmes entre les versions

def test_temp():
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v19800101")
    esgdrs_make(one_file_dataset_path_v2, "CMIP6", root_reconstruct, "v19810101")
    clean()


def test_multiproc():
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v19800101", 2)
    is_same_path_and_good_folder_structure(one_file_dataset_path_v1)
    clean()


def test_monoproc_multifile():
    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 1)
    is_same_path_and_good_folder_structure(multi_file_dataset_path_v1)
    clean()


def test_multiproc_multifile():
    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 4)
    is_same_path_and_good_folder_structure(multi_file_dataset_path_v1)
    clean()

def test_multiproc_multifile_time():
    start = time.time()
    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 1)
    time1 = time.time() - start
    clean()

    start = time.time()
    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 2)
    time2 = time.time() - start
    clean()

    start = time.time()
    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 3)
    time3 = time.time() - start
    clean()

    start = time.time()
    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 4)
    time4 = time.time() - start
    clean()
    print("AU FINAL : ", time1, time2, time3, time4)

def test_remove():
    clean()
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v19800101")
    esgdrs_make(one_file_dataset_path_v2, "CMIP6", root_reconstruct, "v20191003")
    esgdrs_remove(root_reconstruct + "/cmip6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr", "v19800101")
    is_same_path_and_good_folder_structure(one_file_dataset_path_v2)
    esgdrs_remove(root_reconstruct+"/cmip6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr", "v20191003")
    clean()
    # pb le latest reste si c'était le dernier à remove => grave docteur ?

def test_multiproc_remove_time():

    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 4)
    start = time.time()
    esgdrs_remove(root_reconstruct + "/cmip6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn", "v20190725",1)
    time1 = time.time() - start
    clean()

    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 4)
    start = time.time()
    esgdrs_remove(root_reconstruct + "/cmip6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn",
                  "v20190725", 2)
    time2 = time.time() - start
    clean()

    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 4)
    start = time.time()
    esgdrs_remove(root_reconstruct + "/cmip6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn",
                  "v20190725", 3)
    time3 = time.time() - start
    clean()

    esgdrs_make(multi_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20190725", 4)
    start = time.time()
    esgdrs_remove(root_reconstruct + "/cmip6/CMIP/EC-Earth-Consortium/EC-Earth3/historical/r21i1p1f1/Omon/volo/gn",
                  "v20190725", 4)
    time4 = time.time() - start
    clean()

    print("AU FINAL : ",time1,time2,time3,time4)

def test_latest():
    clean()
    esgdrs_make(one_file_dataset_path_v1, "CMIP6", root_reconstruct, "v20180912")
    esgdrs_make(one_file_dataset_path_v2, "CMIP6", root_reconstruct, "v20191003")
    esgdrs_remove(root_reconstruct + "/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr", "v20180912")
    esgdrs_latest(root_reconstruct + "/CMIP6")
    folder_test = Post_Test_Folder(Path(root_reconstruct + "/CMIP6/CFMIP/IPSL/IPSL-CM6A-LR/amip-m4K/r1i1p1f1/Amon/n2oglobal/gr"))
    folder_test.test()
    #clean()
