import argparse
import os
import re
import requests
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


def tagImages(targetDirectory, tarball):
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
                        tarball.add(original)
                        os.remove(original)


def tagJPG(fullname, md5):
    requestURL = "http://danbooru.donmai.us/posts.json?md5={}".format(md5)
    print(requestURL)
    response = requests.get(requestURL)
    print(response)
    if response.json() is None:
        print("No response from danbooru.")
        return False
    tagString = response.json()['tag_string']
    exiftool = 'exiftool.exe' 
    cmd = '{} -XPKeywords="{}" {}'.format(exiftool, tagString, fullname)
    output = subprocess.check_output(cmd)
    print(output.decode().strip())
    return True


def main():
    targetDirectory = "V:/Media/sample/"
    backupDirectory = "V:/Media/"

    args = parseArgs()
    if args.targetDirectory is not None:
        targetDirectory = args.targetDirectory
    if not targetDirectory.endswith('/'):
        targetDirectory += '/'

    if args.backupDirectory is not None:
        backupDirectory = args.backupDirectory
    if not backupDirectory.endswith('/'):
        backupDirectory += '/'

    with tarfile.open(backupDirectory + "taggedImageBackup.tar", "w") as tarball:
        tagImages(targetDirectory, tarball)


if __name__ == '__main__':
    main()
