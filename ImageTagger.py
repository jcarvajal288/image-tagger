import argparse
import os
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
    print("Starting tagging run...", flush=True)
    md5Regex = re.compile(r'^[a-f0-9]{32}\..+$')
    for subdir, dirs, images in os.walk(targetDirectory):
        if not subdir.endswith('/'):
            subdir += '/'
        for image in images:
            try:
                if md5Regex.match(image):
                    md5, ext = image.split('.')
                    fullname = subdir + image
                    if ext == 'jpg' or ext == 'jpeg':
                        if isPartialRun and alreadyTagged(fullname):
                            continue
                        print("Tagging {}...".format(image), flush=True)
                        if tagJPG(fullname, md5):
                            original = fullname + "_original"
                            try: os.rename(original, backupDirectory + image + "_original")
                            except FileExistsError: pass
            except RuntimeError as error:
                print(error, flush=True)



def alreadyTagged(fullname):
    tags = subprocess.check_output(['exiftool', '-XPKeywords', fullname])
    if tags.startwith("Error"):
        raise RuntimeError(tags)
    else: return len(tags) != 0


def queryDanbooru(md5):
    requestURL = "http://danbooru.donmai.us/posts.json?md5={}".format(md5)
    print("Querying: {}".format(requestURL), flush=True)
    response = requests.get(requestURL)
    print(response, flush=True)
    if response.json() is None:
        print("No response from danbooru.", flush=True)
        return False
    if not response.ok:
        return False


def tagJPG(fullname, md5):
    response = queryDanbooru(md5)
    if not response:
        return False
    tagString = response.json()['tag_string']
    cmd = 'exiftool -XPKeywords="{}" {}'.format(tagString, fullname)
    returnCode = subprocess.call(cmd, shell=True)
    return returnCode == 0


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
