#
# Copyright 2023 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
 RF Data Get TMYTek API
"""
import shutil
import subprocess
import os
import zipfile


def clone_github_repo(repo_url, tag, target_folder):
    """
    Clone repo to target folder
    :param repo_url: url of repo
    :param tag: tag of branch to be cloned
    :param target_folder: target api folder for GitHub code
    :return: NA
    """
    folder_path = target_folder

    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        raise Exception("ERROR: The folder should be deleted before clone: {}".format(folder_path))
    else:
        subprocess.run(["git", "clone", repo_url, "--branch", tag, target_folder])
        print("Git clone done")


def extract_api_zip_file(target_folder_path, target_zip_relative_path, target_file_name):
    """
    Extract zip file of api
    :param target_folder_path: top level folder of api
    :param target_zip_relative_path: relative path of the target released linux api
    :param target_file_name: target file name of the api
    :return: target api folder after extracting
    """
    target_zip_file = target_folder_path + target_zip_relative_path + target_file_name + ".zip"
    target_extract_folder = target_folder_path + target_zip_relative_path + "driver"
    os.makedirs(target_extract_folder)
    os.chmod(target_extract_folder, 0o777)

    if os.path.exists(target_zip_file):
        with zipfile.ZipFile(target_zip_file, 'r') as zip_ref:
            zip_ref.extractall(target_extract_folder)
            print("API file generated in {}".format(target_extract_folder))
            return target_extract_folder + "/" + target_file_name
    else:
        raise Exception("ERROR: The TMYTek API can't be found: {}".format(target_zip_file))


def copy_api_to_rf_repo(target_root_path, api_folder_path):
    """
        Copy items in the api folder to target rf-recording-api folder
        :param target_root_path: target rf-recording-api folder
        :param api_folder_path: tmytek api folder
        :return: NA
    """
    print("dir path:", target_root_path)
    api_lib = api_folder_path + "/lib"
    target_lib = target_root_path + "/lib"
    api_logging_config_file = api_folder_path + "/logging.conf"
    requirement_txt = api_folder_path + "/requirements.txt"

    shutil.copytree(api_lib, target_lib, dirs_exist_ok=True)  # copy lib
    shutil.copy(api_logging_config_file, target_root_path)  # copy logging.conf
    shutil.copy(requirement_txt, target_lib)  # copy requirements.txt
    print("TMYTek API copy and merge finished")


def main():
    clone_github_repo(github_repo_url, tag, tmytek_api_target_folder)
    api_folder_path = extract_api_zip_file(tmytek_api_target_folder, tmytek_api_relative_path, tmytek_api_file_name)
    script_path = os.path.abspath(__file__)
    dir_path = os.path.dirname(script_path)
    copy_api_to_rf_repo(dir_path, api_folder_path)


if __name__ == "__main__":
    github_repo_url = "https://github.com/tmytek/tlkcore-examples.git"  # Url of GitHub repo for the device
    tag = "v2.0.0"  # Tag version of the repo
    tmytek_api_target_folder = "/home/mmwave/tmytek_api/v200"  # This folder should not exist before running
    tmytek_api_relative_path = "/release/"  # Relative path of the target released linux api
    tmytek_api_file_name = "TLKCore_v1.2.0_Linux_Python3.8-64bit"  # Target file name of the api
    main()
