import argparse
import os
from PIL import Image
import re
import requests
import shutil
import subprocess
import tarfile


class ImageTagger(object):
    def __init__(self, args):
        self.targetDirectory = args.targetDirectory
        self.backupDirectory = args.backupDirectory
        self.isPartialRun = args.partial
        self.md5Regex = re.compile(r'^[a-f0-9]{32}\.\w+$')

    def tagImages(self):
        for subdir, dirs, images in os.walk(self.targetDirectory):
            if not subdir.endswith('/'):
                subdir += '/'
            for image in images:
                try: self.processImage(subdir, image)
                except RuntimeError as error:
                    print(error, flush=True)

    def processImage(self, subdir, image):
        if self.md5Regex.match(image):
            md5, ext = image.split('.')
            tagString = self.getTags(md5)
            if tagString:
                if ext == 'jpg' or ext == 'jpeg':
                    self.processJPG(subdir, image, tagString)
                elif ext == 'png':
                    self.processPNG(subdir, image, tagString)

    def processJPG(self, subdir, image, tagString):
        fullname = subdir + image
        if self.isPartialRun and self.alreadyTagged(fullname):
            return
        print("Attempting to tag {}".format(image), flush=True)
        if self.tagJPG(fullname, tagString):
            original = fullname + "_original"
            self.moveToBackup(original)

    def processPNG(self, subdir, image, tagString):
        fullname = subdir + image
        jpgName = os.path.splitext(fullname)[0] + '.jpg'
        print("Converting {}...".format(image), flush=True)
        if self.convertPNG(fullname, jpgName):
            print("Conversion successful.", flush=True)
            self.moveToBackup(fullname)
        print("Attempting to tag {}".format(os.path.basename(jpgName)), flush=True)
        if self.tagJPG(jpgName, tagString):
            original = jpgName + "_original"
            os.remove(original)

    def alreadyTagged(self, fullname):
        completedProcess = subprocess.run(['exiftool', '-XPKeywords', "{}".format(fullname)], stdout=subprocess.PIPE)
        tags = completedProcess.stdout.decode()
        if completedProcess.stderr:
            raise RuntimeError(completedProcess.stderr)
        if tags: return True
        else: return False

    def getTagsFromDanbooru(self, md5):
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

    def getTagsFromGelbooru(self, md5):
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

    def getTags(self, md5):
        tagString = self.getTagsFromDanbooru(md5)
        if tagString: return tagString
        tagString = self.getTagsFromGelbooru(md5)
        if tagString: return tagString
        return False

    def tagJPG(self, fullname, tagString):
        cmd = 'exiftool -XPKeywords="{}" "{}"'.format(tagString, fullname)
        completedProcess = subprocess.run(cmd, shell=True)
        return completedProcess.returncode == 0

    def convertPNG(self, fullname, jpgName):
        image = Image.open(fullname)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        try:
            image.save(jpgName, quality=100)
            return True
        except:
            print("Error converting {}".format(fullname), flush=True)
            return False

    def moveToBackup(self, fullname):
        try: shutil.move(fullname, self.backupDirectory + os.path.basename(fullname))
        except FileExistsError: 
            os.remove(fullname)

    def prepBackup(self):
        tarballName = self.backupDirectory[:-1] + ".tgz"
        if not os.path.isdir(self.backupDirectory):
            os.mkdir(self.backupDirectory)
        if os.path.exists(tarballName):
            print("Unpacking backup tarball...", flush=True)
            with tarfile.open(tarballName, 'r:gz') as tarball:
                tarball.extractall(self.backupDirectory)
            os.remove(tarballName)

    def compressOriginals(self):
        print("Compressing backup images...", flush=True)
        tarballName = self.backupDirectory[:-1] + ".tgz"
        with tarfile.open(tarballName, 'w:gz') as tarball:
            for subdir, dirs, images in os.walk(self.backupDirectory):
                for image in images:
                    tarball.add(subdir+image, arcname=image)
        shutil.rmtree(self.backupDirectory)

    def run(self):
        self.prepBackup()
        self.tagImages()
        self.compressOriginals()


def parseArgs():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-t', '--target', metavar='<directory>', type=str, dest='targetDirectory', required=False,
            help='directory containing the images to be tagged')
    parser.add_argument('-b', '--backup', metavar='<directory>', type=str, dest='backupDirectory', required=False,
            help='directory where the backup tarball will be located')
    parser.add_argument( '--partial', action="store_true", dest='partial', 
            help="if present, will not tag already tagged images")
    return parser.parse_args()


def main():
    defaultTargetDirectory = "V:/Media/sampleTest/"
    defaultBackupDirectory = "V:/Media/sampleTestOriginals/"

    args = parseArgs()
    if args.targetDirectory is None:
        args.targetDirectory = defaultTargetDirectory
    if not args.targetDirectory.endswith('/'):
        args.targetDirectory += '/'

    if args.backupDirectory is None:
        args.backupDirectory = defaultBackupDirectory
    if not args.backupDirectory.endswith('/'):
        args.backupDirectory += '/'

    imageTagger = ImageTagger(args)
    imageTagger.run()


if __name__ == '__main__':
    main()
