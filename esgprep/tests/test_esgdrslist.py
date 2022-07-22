#
# l'idée c'est d'avoir un input "folder" ou "file" random dans CMIP6 .. assez profond dans la DRS pour pas durer trop longtemps
# Et le faire fabriquer la DRS par esgdrs dans Fakebdd ...
# Le résultat attendu doit être que /bdd/tout le reste derriere ... doit être identique à /Fakebdd/tout le rente derriere .. pour le rep / file testé
# Comment tester que c'est le même ?
#
# Comment choisir au hasard ?
#
# Soucis :
# L'input est normalement le rep de sortie de la modélisation ... donc contient la derniere version
# 1 Sauf que pour tester le fonctionnement de esgdrs, il nous faut des exemples de trucs déjà bien rangé => donc pour nous : bdd mais pour les autres qui voudrait dev ? ça va etre un autre rep
# 2 dans bdd .. Admettons, on choisit de bien ranger à partir d'un rep : disons : /bdd/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/
#       On va trouver différentes version la dedans ..
#       ls /bdd/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/piControl/r1i1p1f1/Amon/tas/gr/
#       files  latest  v20180802  v20181022  v20181123	v20200326
#       Du coup esgdrs . va considerer que ces différentes versions sont en fait L'UNIQUE derniere version : c'est pas ça qu'on veut ...
#       POSSIBLE SOLUTION :
#       L'idée va etre de select uniquement le "latest" par exemple comme input .. pour tester le bon fonctionnement en cas d'utilisation "normal" ..
#       Et de regarder les versions pour tester le bon fonctionnement (MAJ des liens ... etc) en cas de nouvelles versions
# 3 PB : on sait pas où sont toutes les entrées où il y a plusieurs versions
#       POSSIBLE SOLUTION :
#       - Profiter de la ballade random du cas d'utilisation "normel" pour "logger" les endroits où il y a plusieurs versions ?
#       - Catalogue ?
# Ballade random dans un rep .. on prend le nombre de rep on en prend un hasard .. on rentre dedans ?
from typing import Callable
from hypothesis import given, settings, HealthCheck
from hypothesis.strategies import text, integers, composite, SearchStrategy, lists
import csv
import os, re
from argparse import Namespace
from esgprep.esgdrs import run
from pathlib import Path
from esgprep.tests.TestFolder import TestFolder

@composite
def random_cmip6_path(draw):
    root_path = "/bdd/CMIP6"
    # just to make sure we select different depth path .. but for testing we ll limit to variable_id ? (6 : variable 8: version)
    path_depth = draw(integers(min_value=6,
                               max_value=8))
    current_path = root_path
    for _ in range(path_depth):
        list_dir_in_crt_path = [d for d in list(os.scandir(current_path)) if d.is_dir() and d.name[0] != '.']
        random_pick = draw(integers(0, len(list_dir_in_crt_path) - 1))
        add = list_dir_in_crt_path[random_pick].name
        current_path = current_path + "/" + add
    return current_path

# put aside to not test that with pytest
@settings(max_examples=2, suppress_health_check=(HealthCheck.too_slow,), deadline=None)
@given(random_cmip6_path())
def aside_test_normal_esgdrs(path: str):
    root_path_real_drs = "/bdd"
    root_path_reconstruct_drs = "/home/ltroussellier/FakeBdd"

    print("TEST : ", path)  # root path to files that need to be ordered in DRS (i.e root path output of model)

    print("------ DRS CREATION -------")
    auto_esgdrs_dir(path, root_path_reconstruct_drs)

    # what we want to be produced for each dataset :
    #       * files folder with d******/file.nc ..
    #       * v***** folder with file simlink to file.nc
    #       * latest folder with file simlink to last file.nc

    # Since symlink link are NOT visible from bdd .. we can't test it directly
    # what things HAVE TO be the same between reconstruct and real ?
    #       * latest                              <= Always there
    #       * path between cmip6/ ... /v******    <= to see if pyessv , esgdrs have well decoded information from files
    #       * name of files                       <= name have to be same

    # what things ARE different ?
    #       * v****** <= versions are different because we need to test adding new version not on the same day
    #       * files   <= files folder is present only if it's published and not replica
    #       * symlink <= to avoid duplicate file .. the "root file" is not copy, it's only a symlink
    print("-----------------------------------------------------------------------------")
    print("------ DO WE HAVE WHAT WE WANT --------------")
    print("-----------------------------------------------------------------------------")

    # PB .. we only have the root path .. we dont know before where it has to be .. unless
    # we know from the root path esgdrs has find every dataset in subfolder ( on bdd : already in DRS )
    # thus : we can walk in bdd .. from root path .. to find .. where is the "latest" folder for instance
    # then compare with what we have reconstructed
    # CARREFUL with glob .. from member_id to get all folder with a latest folder takes 30s ...

    # all the path where we 'normaly' found some files contains a latest folder
    all_path_with_latest_folder = list(Path(path).glob('**/latest'))

    # just to deal with pyessv cmip6 lower case : these 2 lines will be deleted soon
    root_path_real_drs = root_path_real_drs + "/CMIP6"
    root_path_reconstruct_drs = root_path_reconstruct_drs + "/cmip6"

    # list of all presumed path esgdrs have created in which there is a latest and a v****** and files
    all_presumed_path = [Path(pp.parent).as_posix().replace(root_path_real_drs, root_path_reconstruct_drs) for pp in all_path_with_latest_folder]
    print(all_presumed_path)

    for pp in all_presumed_path:
        folder_test = TestFolder(Path(pp))
        print("-----------------------------")
        print("--- TESTING : ", pp," -------")

        assert folder_test.exists() 
        print("--- Exist -------")
        assert folder_test.contains_at_least_the_3_folders()
        print("--- HAS files,latest, and at least version folders -------")

        assert folder_test.is_there_same_number_of_files_in_d_and_v()
        print("--- HAS same number of files/d******** and v******** -------")

        assert folder_test.is_there_symlink_between_v_and_d()
        print("--- HAS symlink between files/d********/* and v********/* -------")

        assert folder_test.is_there_symlink_between_latest_and_latest_version()
        print("--- HAS symlink between latest and the latest v******** -------")
        print("---EVERYTHING FINE")
    print("-----------------------------------------------------------------------------")
    print("-----------------------------------------------------------------------------")





@composite
def random_cmip6_multiversion_dataset(draw):
    list_multi_versions_dataset_path = "/climserv-home/ltroussellier/dev/FakeInEsgprep/dataset_multiversion.csv"
    with open(list_multi_versions_dataset_path, newline='') as f:
        data = list(csv.reader(f))
    random_pick = draw(integers(1, len(data) - 1))
    keyvalues = data[random_pick]
    return "/bdd/"+"/".join(data[random_pick][:-1])

"""
@settings(max_examples=10, suppress_health_check=(HealthCheck.too_slow,), deadline=None)
@given(random_cmip6_multiversion_dataset())
def test_multi_version_dataset_esgdrs(path):
    listversion = [d.name for d in os.scandir(path) if d.is_dir() and d.name[0]=="v"]
    print("---------")
    print("pour ce dataset : ",path, "nous avons ces versions : ", listversion)
"""


def auto_esgdrs_dir(dir_source: str, root_path_drs: str):
    print("DRS GENERATION")
    arg = Namespace(cmd='make',
                    i='/esg/config/esgcet',
                    log=None, debug=False,
                    action='upgrade',
                    directory=[dir_source],
                    project='CMIP6', ignore_dir=re.compile('^.*/(files|\\.[\\w]*).*$'), include_file=['^.*\\.nc$'],
                    exclude_file=['^\\..*$'],
                    color=False, no_color=False,
                    max_processes=1,
                    root=root_path_drs,
                    version='v19810101',
                    set_value=None, set_key=None,
                    rescan=True,
                    commands_file=None, overwrite_commands_file=False, upgrade_from_latest=False,
                    ignore_from_latest=None, ignore_from_incoming=None,
                    copy=False, link=False, symlink=True,
                    no_checksum=False, checksums_from=None, quiet=False,
                    prog='esgdrs')

    run(arg)
