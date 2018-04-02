import argparse
import os
import re
import requests
import subprocess


def parseArgs():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-t', '--target', metavar='<directory>', type=str, dest='targetDirectory', required=False,
            help='directory containing the images to be tagged')
    return parser.parse_args()


def tagImages(targetDirectory):
    md5Regex = re.compile(r'^[a-f0-9]{32}\..+$')
    for subdir, dirs, images in os.walk(targetDirectory):
        for image in images:
            if md5Regex.match(image):
                ext = image.split('.')[1]
                if ext == 'jpg' or ext == 'jpeg':
                    print("Tagging {}...".format(image))
                    tagJPG(subdir, image)


def tagJPG(subdir, image):
    md5 = image.split('.')[0]
    requestURL = "http://danbooru.donmai.us/posts.json?md5={}".format(md5)
    response = requests.get(requestURL)
    if response.json() is None:
        return
    tagString = response.json()['tag_string']
    exiftool = 'exiftool.exe' 
    cmd = '{} -XPKeywords="{}" {}'.format(exiftool, tagString, image)
    output = subprocess.check_output(cmd)
    print(output.decode().strip())


def main():
    targetDirectory = "V:/Media/sample/"

    args = parseArgs()
    if args.targetDirectory is not None:
        targetDirectory = args.targetDirectory
    if not targetDirectory.endswith('/'):
        targetDirectory += '/'

    tagImages(targetDirectory)


if __name__ == '__main__':
    #main()
    #inFile = "V:/Media/sample/61180d0fbfd2cbc572825c59a27535b1.jpg"
    image = "00dffc66f544c7748d53b4bd913939bc.jpg"
    md5 = image.split('.')[0]
    requestURL = "http://danbooru.donmai.us/posts.json?md5={}".format(md5)
    #print(requestURL)
    response = requests.get(requestURL)
    #if response.json() is None:
        #return
    tagString = response.json()['tag_string']
    #print(tagString)
    #cmd = "exiftool.exe -XPKeywords {}".format(image)
    exiftool = 'exiftool.exe' 
    cmd = '{} -XPKeywords="{}" {}'.format(exiftool, tagString, image)
    output = subprocess.check_output(cmd)
    print(output)
