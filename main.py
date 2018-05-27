# Native Python imports
import datetime as dt
from io import StringIO
import re
import requests
import time
# 3rd Party Packages
import pandas as pd
import matplotlib.pyplot as plt
# Local packages
import keys

base_url_insecure = r'https://online.lloydsbank.co.uk'
base_url_secure = r'https://secure.lloydsbank.co.uk'
start_date = dt.date(2018, 1, 1)
end_date = dt.date(2018, 5, 1)
download_days_at_once = 30


def _sleep() -> None:
    time.sleep(2)


def get_token(name: str, content: str) -> str:
    return re.search(f'<input\s*type="hidden"\s*name="{name}"\s*value="([0-9a-zA-Z_]*)"\s*/>', content)[1]


def pprint_req(req: requests.models.Response) -> None:
    print(req.text)


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
    req1 = sess.get(base_url_insecure + r'/personal/logon/login.jsp')
    req1_content = req1.content.decode('utf-8')

    # Get hidden tokens on page to
    data = {
        'submitToken': get_token('submitToken', req1_content),
        'frmLogin:strCustomerLogin_userID': keys.user_id,
        'frmLogin:strCustomerLogin_pwd': keys.main_pw
    }

    # Just wait a little bit, because web servers don't like you hammering them
    _sleep()

    # Log in past page one, and get the "memorable information page"
    req2 = sess.post(base_url_insecure + r'/personal/primarylogin', data=data)
    req2_content = req2.content.decode('utf-8')
    data2 = {'submitToken': get_token('submitToken', req2_content),
             'frmentermemorableinformation1': 'frmentermemorableinformation1',
             'frmentermemorableinformation1:btnContinue': 'null'
             }

    for i, mem_pos in enumerate(get_mem_info_positions(req2_content)):
        data2[f'frmentermemorableinformation1:strEnterMemorableInformation_memInfo{i+1}'] = '&nbsp;' + keys.mem_info[mem_pos]

    # Just wait a little bit, because web servers don't like you hammering them
    _sleep()

    # Log in past memorable information page? (doesn't work yet)
    req3 = sess.post(base_url_secure + r'/personal/a/logon/entermemorableinformation.jsp', data=data2)

    try:
        assert '<title>Lloyds Bank - Personal Account Overview</title>' in req3.text
    except AssertionError:
        raise AssertionError('Something\'s gone wrong and we\'re not in the main page...')

    return sess, req3


def get_all_accounts(main_page_text: str) -> list:
    return re.findall('<a id="lnkAccName[a-zA-Z0-9-_]*"\s*href="(.*?)"\s*title=".*?"\s*data-wt-ac="(.*?)"', main_page_text)


def dl_csv(session: requests.Session, page_text: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    # First ensure we're not looking over too many days
    num_days = (end - start).days
    if num_days > download_days_at_once:
        # Split range if too long, as too many transactions makes Lloyds sad
        midpoint = start + (end - start) / 2
        return pd.concat([
            dl_csv(session, page_text, start, midpoint),
            dl_csv(session, page_text, midpoint + dt.timedelta(1), end),
        ]).reset_index(drop=True)

    # form_http = re.search('<form id="accStatement:export-statement-form.*?<.form>', page_text, flags=re.DOTALL)[0]
    # req = session.post(base_url_secure + r'/personal/a/viewproductdetails/viewproductdetailsdesktopress.js',
    req = session.get(base_url_secure + r'/personal/a/viewproductdetails/ress/m44_exportstatement_fallback.jsp')
    # req = session.post(base_url_secure + r'/personal/a/viewproductdetails/viewproductdetailsdesktopress.js',
    _sleep()
    req = session.post(base_url_secure + r'/personal/a/viewproductdetails/ress/m44_exportstatement_fallback.jsp',
                       data={
                           # 'exportDateRange': 'between',
                           'exportDateRange': 'between',
                           'searchDateFrom': start.strftime('%d/%m/%Y'),
                           # 'export-date-range-from':  start.strftime('%d/%m/%Y'),
                           # 'from':  start.strftime('%d/%m/%Y'),
                           'searchDateTo': end.strftime('%d/%m/%Y'),
                           # 'export-date-range-to':    end.strftime('%d/%m/%Y'),
                           # 'to':    end.strftime('%d/%m/%Y'),
                           'export-format': 'Internet banking text/spreadsheet (.CSV)',
                           'submitToken': get_token('submitToken', req.text),
                           'export-statement-form': 'export-statement-form',
                           # 'accStatement:export-statement-form': 'accStatement:export-statement-form',
                           # 'export-statement-form:btnQuickTransferRetail': 'Export'
                           'export-statement-form:btnQuickTransferRetail': 'Export'
                       })

    # In case we're dling lots of csvs
    _sleep()
    try:
        return pd.read_csv(StringIO(req.text), parse_dates=['Transaction Date'], dayfirst=True).sort_values('Transaction Date')
    except ValueError:
        # There were no transactions in the range
        return pd.DataFrame()


if __name__ == '__main__':
    session, main_page = get_logged_in_session()

    accounts = get_all_accounts(main_page.text)

    print('Accounts:  ', [a[1] for a in accounts])

    account_data = {}
    for url_end, acc in accounts:
        url = base_url_secure + url_end

        account_page = session.get(url)
        # print(account_page.text)
        # print('=========================================\n' * 10)
        account_data[acc] = dl_csv(session, account_page.text, start_date, end_date)
        account_data[acc]['Account'] = acc

    data = pd.concat([account_data[acc] for acc in account_data]).sort_values('Transaction Date').reset_index(drop=True)
    print(data)
