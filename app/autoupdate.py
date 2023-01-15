import shutil, sys, os
from datetime import datetime
import json
import urllib.request
from zipfile import ZipFile

from app import constants

remote_repo = r"https://gitlab.com/rainlash/lt-maker/-/releases/permalink/latest/downloads/lex_talionis_maker"
remote_latest = r"https://gitlab.com/rainlash/lt-maker/-/releases/permalink/latest"
metadata = "version.txt"

def check_version(a: str, b: str) -> bool:
    """
    Returns True if a > b, False otherwise
    """
    a = a.replace('.', '').replace('-', '')
    b = b.replace('.', '').replace('-', '')
    return a != b

def download_url(url, save_path):
    with urllib.request.urlopen(url) as dl_file:
        with open(save_path, 'wb') as out_file:
            out_file.write(dl_file.read())

def get_redirected_url(url): # https://stackoverflow.com/questions/5538280/determining-redirected-url-in-python
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    request = opener.open(url)
    return request.url

def check_for_update() -> bool:
    version_url = get_redirected_url(remote_latest)
    version_num = version_url.index("releases/") + len("releases/") # Will point to start of release ID
    new_version = version_url[version_num:]
    print(new_version, version_url)

    if os.path.exists(metadata):
        with open(metadata) as fp:
            lines = [l.strip() for l in fp.readlines()]
            cur_version = lines[0]

        print(new_version)
        print(cur_version)
        if check_version(new_version, cur_version):
            print("Needs update! %s %s" % (new_version, cur_version))
            return True
        else:
            print("Does not need update! %s %s" % (new_version, cur_version))
            return False
    else:
        print("Cannot find version.txt, so needs update: %s!" % metadata)
        return True

def copy_and_overwrite(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

# Update all files -- probably buggy as hell
# TODO test once `check_for_update` works
def update() -> bool:
    print("Starting Process! %s" % remote_repo)
    remote_zip = r"remote_tmp.zip"
    download_url(remote_repo, remote_zip)
    print(remote_zip)
    remote_dir = remote_zip.replace('.zip', '/')
    print(remote_dir)
    try:
        with ZipFile(remote_zip, 'r') as z:
            print("Extracting...")
            z.extractall(remote_dir)
        print("Done extracting to %s" % remote_dir)
    except OSError as e:
        print("Failed to fully unzip remote %s to %s! %s" % (remote_zip, remote_dir, e))
        return False

    try:
        os.remove(remote_zip)
    except OSError as e:
        print("Failed to delete zip %s! %s" % (remote_zip, e))
        return False

    print("Executable: %s" % sys.executable)
    local = os.path.dirname(sys.executable)
    print("Local: %s %s" % (local, os.path.abspath(local)))
    cwd = os.path.abspath(os.getcwd())
    print("Current working directory: %s" % cwd)
    # Make backup of current working directory
    current_backup = cwd + '.tmp'
    shutil.copytree(cwd, current_backup)

    try:
        copy_and_overwrite(remote_dir, cwd)
    except OSError as e:
        print("Failed to completely upgrade files when copying %s to %s! %s" % (remote_dir, cwd, e))
        copy_and_overwrite(current_backup, cwd)
        return False
    finally:
        shutil.rmtree(remote_dir)
        shutil.rmtree(current_backup)

    return True
    
if __name__ == '__main__':
    check_for_update()
