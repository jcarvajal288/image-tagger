import argparse
import os
import re
import requests


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
                print("Tagging {}...".format(image))
                tagImage(subdir, image)


def tagImage(subdir, image):
    md5 = image.split('.')[0]
    requestURL = "http://danbooru.donmai.us/posts.json?md5={}".format(md5)
    print(requestURL)
    response = requests.get(requestURL)
    if response.json() is None:
        return
    tagString = response.json()['tag_string']
    print(tagString)


def main():
    targetDirectory = "V:/Media/sample/"

    args = parseArgs()
    if args.targetDirectory is not None:
        targetDirectory = args.targetDirectory
    if not targetDirectory.endswith('/'):
        targetDirectory += '/'

    tagImages(targetDirectory)


if __name__ == '__main__':
    main()
