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


def tagImages(targetDirectory, backupDirectory):
    md5Regex = re.compile(r'^[a-f0-9]{32}\..+$')
    for subdir, dirs, images in os.walk(targetDirectory):
        if not subdir.endswith('/'):
            subdir += '/'
        for image in images:
            if md5Regex.match(image):
                md5, ext = image.split('.')
                fullname = subdir + image
                if ext == 'jpg' or ext == 'jpeg':
                    print("Tagging {}...".format(image))
                    if tagJPG(fullname, md5):
                        original = fullname + "_original"
                        try:
                            os.rename(original, backupDirectory + image + "_original")
                        except FileExistsError: pass


def tagJPG(fullname, md5):
    requestURL = "http://danbooru.donmai.us/posts.json?md5={}".format(md5)
    print("Querying: {}".format(requestURL))
    response = requests.get(requestURL)
    print(response)
    if response.json() is None:
        print("No response from danbooru.")
        return False
    tagString = response.json()['tag_string']
    #cmd = 'exiftool -XPKeywords="{}" {}'.format(tagString, fullname)
    cmd = 'exiftool'
    output = subprocess.check_output(cmd)
    print(output.decode().strip())
    return True


def prepBackup(backupDirectory):
    tarballName = backupDirectory[:-1] + ".tgz"
    if not os.path.isdir(backupDirectory):
        os.mkdir(backupDirectory)
    if os.path.exists(tarballName):
        with tarfile.open(tarballName, 'r:gz') as tarball:
            tarball.extractall(backupDirectory)
        os.remove(tarballName)


def compressOriginals(backupDirectory):
    tarballName = backupDirectory[:-1] + ".tgz"
    with tarfile.open(tarballName, 'w:gz') as tarball:
        for subdir, dirs, images in os.walk(backupDirectory):
            for image in images:
                tarball.add(subdir+image, arcname=image)
    shutil.rmtree(backupDirectory)


def main():
    targetDirectory = "V:/Media/sampleTest/"
    backupDirectory = "V:/Media/sampleOriginals/"

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

    tagImages(targetDirectory, backupDirectory)

    compressOriginals(backupDirectory)


if __name__ == '__main__':
    main()
