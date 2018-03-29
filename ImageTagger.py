import requests

danbooru = 'http://danbooru.donmai.us'
imageMD5 = '00dffc66f544c7748d53b4bd913939bc'
requestURL = "{}/posts.json?md5={}".format(danbooru, imageMD5)

print(requestURL)

response = requests.get(requestURL)
print(response.json()['tag_string'])
