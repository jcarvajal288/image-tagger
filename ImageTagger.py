import argparse
import os
import re
import requests

danbooru = 'http://danbooru.donmai.us'
imageMD5 = '00dffc66f544c7748d53b4bd913939bc'
requestURL = "{}/posts.json?md5={}".format(danbooru, imageMD5)

print(requestURL)

response = requests.get(requestURL)
print(response.json()['tag_string'])

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
                filepath = subdir + os.sep + image
                print(filepath)


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
