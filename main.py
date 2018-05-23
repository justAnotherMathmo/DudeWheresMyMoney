import re
import requests

data = {
    'frmLogin:strCustomerLogin_userID': '',
    'frmLogin:strCustomerLogin_pwd': ''
}
memorable_info = ''


def get_token(name, content):
    return re.search(f'<input\s*type="hidden"\s*name="{name}"\s*value="([0-9a-zA-Z_]*)"\s*/>', content)[1]


def pprint_req(req):
    print(req.content.decode('utf-8'))


def get_mem_info_positions(content):
    positions = []
    for i in [1, 2, 3]:
        # Minus 1 because indexes != labels
        positions.append(int(re.search(f'Information_memInfo{i}">Character ([0-9]*)', content)[1]) - 1)
    return positions


if __name__ == '__main__':
    # Set up session
    sess = requests.Session()

    # Get the first log in page
    req1 = sess.get(r'https://online.lloydsbank.co.uk/personal/logon/login.jsp')
    req1_content = req1.content.decode('utf-8')

    # Get hidden tokens on page to
    data['submitToken'] = get_token('submitToken', req1_content)

    print(data)

    # Log in past page one, and get the "memorable information page"
    req2 = sess.post(r'https://online.lloydsbank.co.uk/personal/primarylogin', data=data)
    req2_content = req2.content.decode('utf-8')
    data2 = {'submitToken': get_token('submitToken', req2_content)}

    for i, mem_pos in enumerate(get_mem_info_positions(req2_content)):
        data2[f'frmentermemorableinformation1:strEnterMemorableInformation_memInfo{i+1}'] = '&amp;nbsp;' + memorable_info[mem_pos]

    print(data2)

    # Log in past memorable information page? (doesn't work yet)
    req3 = sess.post(r'https://online.lloydsbank.co.uk/personal/a/logon/entermemorableinformation.jsp', data=data2,
                     headers=dict(referer=r'https://online.lloydsbank.co.uk/personal/a/logon/entermemorableinformation.jsp'))