import re
import requests
import time
# Local packages
import keys


def get_token(name: str, content: str) -> str:
    return re.search(f'<input\s*type="hidden"\s*name="{name}"\s*value="([0-9a-zA-Z_]*)"\s*/>', content)[1]


def pprint_req(req: requests.models.Response) -> None:
    print(req.content.decode('utf-8'))


def get_mem_info_positions(content: str) -> list:
    positions = []
    for i in [1, 2, 3]:
        # Minus 1 because indexes != labels
        positions.append(int(re.search(f'Information_memInfo{i}">Character ([0-9]*)', content)[1]) - 1)
    return positions


def get_logged_in_session() -> (requests.Session, requests.models.Response):
    # Set up session
    sess = requests.Session()

    # Get the first log in page
    req1 = sess.get(r'https://online.lloydsbank.co.uk/personal/logon/login.jsp')
    req1_content = req1.content.decode('utf-8')

    # Get hidden tokens on page to
    data = {
        'submitToken': get_token('submitToken', req1_content),
        'frmLogin:strCustomerLogin_userID': keys.user_id,
        'frmLogin:strCustomerLogin_pwd': keys.main_pw
    }

    # Just wait a little bit, because web servers don't like you hammering them
    time.sleep(2)

    # Log in past page one, and get the "memorable information page"
    req2 = sess.post(r'https://online.lloydsbank.co.uk/personal/primarylogin', data=data)
    req2_content = req2.content.decode('utf-8')
    data2 = {'submitToken': get_token('submitToken', req2_content),
             'frmentermemorableinformation1': 'frmentermemorableinformation1',
             'frmentermemorableinformation1:btnContinue': 'null'
             }

    for i, mem_pos in enumerate(get_mem_info_positions(req2_content)):
        data2[f'frmentermemorableinformation1:strEnterMemorableInformation_memInfo{i+1}'] = '&nbsp;' + keys.mem_info[mem_pos]

    # Just wait a little bit, because web servers don't like you hammering them
    time.sleep(2)

    # Log in past memorable information page? (doesn't work yet)
    req3 = sess.post(r'https://secure.lloydsbank.co.uk/personal/a/logon/entermemorableinformation.jsp', data=data2)

    return sess, req3


if __name__ == '__main__':
    session, main_page = get_logged_in_session()
