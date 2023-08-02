import requests
import json

token = '9ce864936c03b5c8d260101766cd04be090a7eea'
username = 'farsea'
host = 'www.pythonanywhere.com'
creatdata = {
    "executable": "bash",
    "arguments": "",
    "working_directory": ''
}
url = f'https://{host}/api/v0/user/{username}/consoles/'
headers = {'Authorization': 'Token {}'.format(token)}
res = requests.get(url, headers=headers)
reslist = json.loads(res.text)
if reslist:
    resid = reslist[0]['id']
    data = {
        input: 'git pull'
    }
#     url2 = f'https://{host}/api/v0/user/{username}/consoles/{resid}/send_input/'
#     res2 = requests.post(url2, headers=headers, data=data)
#     print(resid)
    url3 = f'https://{host}/api/v0/user/{username}/consoles/{resid}/get_latest_output/'
    res3 = requests.get(url3, headers=headers)
    print(res3.text)
