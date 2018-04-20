import argparse
import os
from PIL import Image
import re
import requests
import shutil
import subprocess
import tarfile


def parseArgs():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-t', '--target', metavar='<directory>', type=str, dest='targetDirectory', required=False,
            help='directory containing the images to be tagged')
    parser.add_argument('-b', '--backup', metavar='<directory>', type=str, dest='backupDirectory', required=False,
            help='directory where the backup tarball will be located')
    parser.add_argument( '--partial', action="store_true", dest='partial', 
            help="if present, will not tag already tagged images")
    return parser.parse_args()


def tagImages(targetDirectory, backupDirectory, isPartialRun):
    md5Regex = re.compile(r'^[a-f0-9]{32}\.\w+$')
    for subdir, dirs, images in os.walk(targetDirectory):
        if not subdir.endswith('/'):
            subdir += '/'
        for image in images:
            fullname = subdir + image
            try:
                if md5Regex.match(image):
                    md5, ext = image.split('.')
                    if ext == 'jpg' or ext == 'jpeg':
                        if isPartialRun and alreadyTagged(fullname):
                            continue
                        print("Attempting to tag {}".format(image), flush=True)
                        if tagJPG(fullname, md5):
                            print("Tag successful.", flush=True)
                            original = fullname + "_original"
                            moveToBackup(original, backupDirectory)
                    elif ext == 'png':
                        jpgName = os.path.splitext(fullname)[0] + '.jpg'
                        print("Converting {}...".format(image), flush=True)
                        if convertPNG(fullname, jpgName):
                            print("Conversion successful.", flush=True)
                            moveToBackup(fullname, backupDirectory)
                        print("Attempting to tag {}".format(os.path.basename(jpgName)), flush=True)
                        if tagJPG(jpgName, md5):
                            print("Tag successful.", flush=True)
                            original = jpgName + "_original"
                            os.remove(original)
            except RuntimeError as error:
                print(error, flush=True)


def alreadyTagged(fullname):
    completedProcess = subprocess.run(['exiftool', '-XPKeywords', "{}".format(fullname)], stdout=subprocess.PIPE)
    tags = completedProcess.stdout.decode()
    if completedProcess.stderr:
        raise RuntimeError(completedProcess.stderr)
    if tags:
        return True
    else: return False


def queryDanbooru(md5):
    requestURL = "http://danbooru.donmai.us/posts.json?md5={}".format(md5)
    print("Querying: {}".format(requestURL), flush=True)
    response = requests.get(requestURL)
    print(response, flush=True)
    if not response.ok:
        return False
    elif response.json() is None:
        print("No response from danbooru.", flush=True)
        return False
    else: return response.json()['tag_string']


def queryGelbooru(md5):
    requestURL = "http://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&tags=md5:{}".format(md5)
    print("Querying: {}".format(requestURL), flush=True)
    response = requests.get(requestURL)
    print(response, flush=True)
    if not response.ok:
        return False
    elif response.text == '':
        print("No response from gelbooru.", flush=True)
        return False
    else: return response.json()[0]['tags']


def tagJPG(fullname, md5):
    tagString = queryDanbooru(md5)
    if not tagString:
        tagString = queryGelbooru(md5)
    if not tagString:
        return False
    cmd = 'exiftool -XPKeywords="{}" "{}"'.format(tagString, fullname)
    completedProcess = subprocess.run(cmd, shell=True)
    return completedProcess.returncode == 0


def convertPNG(fullname, jpgName):
    image = Image.open(fullname)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    try:
        image.save(jpgName, quality=100)
        return True
    except:
        print("Error converting {}".format(fullname), flush=True)
        return False


def moveToBackup(fullname, backupDirectory):
    try: shutil.move(fullname, backupDirectory + os.path.basename(fullname))
    except FileExistsError: 
        os.remove(fullname)


def prepBackup(backupDirectory):
    tarballName = backupDirectory[:-1] + ".tgz"
    if not os.path.isdir(backupDirectory):
        os.mkdir(backupDirectory)
    if os.path.exists(tarballName):
        print("Unpacking backup tarball...", flush=True)
        with tarfile.open(tarballName, 'r:gz') as tarball:
            tarball.extractall(backupDirectory)
        os.remove(tarballName)


def compressOriginals(backupDirectory):
    print("Compressing backup images...", flush=True)
    tarballName = backupDirectory[:-1] + ".tgz"
    with tarfile.open(tarballName, 'w:gz') as tarball:
        for subdir, dirs, images in os.walk(backupDirectory):
            for image in images:
                tarball.add(subdir+image, arcname=image)
    shutil.rmtree(backupDirectory)


def main():
    targetDirectory = "V:/Media/sampleTest/"
    backupDirectory = "V:/Media/sampleTestOriginals/"

    args = parseArgs()
    if args.targetDirectory is not None:
        targetDirectory = args.targetDirectory
    if not targetDirectory.endswith('/'):
        targetDirectory += '/'

    if args.backupDirectory is not None:
        backupDirectory = args.backupDirectory
    if not backupDirectory.endswith('/'):
        backupDirectory += '/'

    prepBackup(backupDirectory)

    tagImages(targetDirectory, backupDirectory, args.partial)

    compressOriginals(backupDirectory)


if __name__ == '__main__':
    main()
