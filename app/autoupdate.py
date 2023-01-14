import shutil, sys, os
from datetime import datetime
import json
import urllib.request
from zipfile import ZipFile

from app import constants

remote_repo = r"https://gitlab.com/rainlash/lt-maker/-/releases/permalink/latest/downloads/lex_talionis_maker"
remote_latest = r"https://gitlab.com/rainlash/lt-maker/-/releases/permalink/latest"
remote_latest_evidence = r"https://gitlab.com/rainlash/lt-maker/-/releases/permalink/latest/evidence"

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

    # Determine what date the release was released
    # According to Gitlab documentation,
    # this should work
    # However, it always 404s
    # Maybe one day Gitlab will fix their bugs
    resp = urllib.request.urlopen(remote_latest_evidence)
    content = resp.read()
    data = json.loads(content)
    release = data.get('release')
    created_at_date = release.get('created_at')
    released_at = datetime.fromisoformat(created_at_date)

    # Determine what date the current version of the engine was released
    current_year, current_month, current_day = constants.VERSION.split('.')
    current_day = current_day[:2]

    if released_at.year != int(current_year) or released_at.month != int(current_month) or released_at.day != int(current_day):
        print("Needs update! %s %s" % (released_at.date(), constants.VERSION[:-1]))
        return True
    else:
        print("Does not need update! %s %s" % (released_at.date(), constants.VERSION[:-1]))
        return False

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
