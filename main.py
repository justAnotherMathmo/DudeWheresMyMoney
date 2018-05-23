import re
import requests

data = {
    'frmLogin:strCustomerLogin_userID': '',
    'frmLogin:strCustomerLogin_pwd': ''
}


def get_token(name, content):
    return re.search(f'<input\s*type="hidden"\s*name="{name}"\s*value="([0-9a-zA-Z_]*)"\s*/>', content)[1]


def pprint_req(req):
    print(req.content.decode('utf-8'))


if __name__ == '__main__':
    sess = requests.Session()

    req1 = sess.get(r'https://online.lloydsbank.co.uk/personal/logon/login.jsp')

    req_content = req1.content.decode('utf-8')
    data['submitToken'] = get_token('submitToken', req_content)
    data['dclinkjourid'] = get_token('dclinkjourid', req_content)

    print(data)

    req2 = sess.post(r'https://online.lloydsbank.co.uk/personal/primarylogin', data=data)

    pprint_req(req2)