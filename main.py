import getpass
import string
import requests
import traceback
import sys
import pprint

# настройка базового адреса
base_url = 'http://localhost/inframanager/'


def encrypt_pass(password, key):
    retval = ''
    for i in password:
        xorred = chr(ord(i) ^ key)
        retval += xorred if xorred in string.printable \
            else r'\x{:2x}'.format(ord(xorred))
    return retval


def auth_payload():
    user_login = input('\nлогин пользователя: ')
    user_pass = getpass.getpass(prompt='пароль: ', stream=sys.stdout)
    payload = {'loginName': user_login,
               'passwordEncrypted': encrypt_pass(user_pass, 13)}
    return payload


def regcall_payload(urglist, calltypelist):
    while True:
        print('\nвыберите индекс срочности заявки:')
        for index, element in enumerate(urglist):
            print(index, element['Name'])
        session_urgency = input()
        if session_urgency not in \
                [str(n) for n in range(0, len(urglist))]:
            print('\nнекорректное значение!')
            continue
        else:
            break

    while True:
        print('\nвыберите индекс типа заявки:')
        for index, element in enumerate(calltypelist):
            print(index, element['Name'])
        session_calltype = input()
        if session_calltype not in \
                [str(n) for n in range(0, len(calltypelist))]:
            print('\nнекорректное значение!')
            continue
        else:
            break

    return int(session_urgency), int(session_calltype)


def conn_err_handler():
    for i in traceback.format_exception_only(*(sys.exc_info()[:-1])):
        print(f'\n{i.rstrip()}')
    while err_handling := input('\nпопробовать еще раз (Y/N): '):
        if err_handling == 'Y' or err_handling == 'y':
            return
        elif err_handling == 'N' or err_handling == 'n':
            print('\nзавершение работы..')
            sys.exit()
        else:
            continue


# Signin
payload1 = auth_payload()
while True:
    try:
        response_signin = requests.post(base_url +
                                        'accountApi/SignIn',
                                        data=payload1)
        if dict(response_signin.headers)['Content-Type'] == \
                'application/json; charset=utf-8' and \
                response_signin.json().get('Success') is True:
            break
        else:
            while auth_handling := input('\nаутентификация не прошла, '
                                         'попробовать еще раз (Y/N): '):
                if auth_handling == 'Y' or auth_handling == 'y':
                    payload1 = auth_payload()
                    break
                elif auth_handling == 'N' or auth_handling == 'n':
                    print('\nзавершение работы..')
                    sys.exit()
                else:
                    continue
    except requests.RequestException:
        conn_err_handler()
        continue

session_headers = {'Cookie':
                       dict(response_signin.headers)['Set-Cookie'][-787:-55]
                       + 'enableWindowsAutoLogon=1'}

# GetAuthenticationInfo
while True:
    try:
        response_authinfo = requests.get(base_url +
                                         'accountApi/GetAuthenticationInfo',
                                         headers=session_headers)
        break
    except requests.RequestException:
        conn_err_handler()
        continue

session_userid = response_authinfo.json().get('UserID')

# GetUrgencyList
while True:
    try:
        response_urglist = requests.get(base_url +
                                        'sdApi/GetUrgencyList',
                                        headers=session_headers)
        break
    except requests.RequestException:
        conn_err_handler()
        continue

session_urglist = response_urglist.json()

# GetCallTypeListForClient
while True:
    try:
        response_calltypelist = requests.get(base_url +
                                             'sdApi/GetCallTypeListForClient',
                                             headers=session_headers)
        break
    except requests.RequestException:
        conn_err_handler()
        continue

session_calltypelist = response_calltypelist.json()
session_callsettings = regcall_payload(session_urglist,
                                       session_calltypelist)

# registerCall
payload2 = {
    'UserID': session_userid,
    'CallTypeID': session_calltypelist[session_callsettings[1]]['ID'],
    'UrgencyID': session_urglist[session_callsettings[0]]['ID'],
    'CallSummaryName': 'Тестовое описание',
    'HTMLDescription': 'Тестовое полное описание',
    'ServiceItemID': '',
    'ServiceAttendanceID': ''
}
while True:
    try:
        response_regcall = requests.post(base_url +
                                         'sdApi/registerCall',
                                         data=payload2,
                                         headers=session_headers)
        if dict(response_regcall.headers)['Content-Type'] == \
                'application/json; charset=utf-8' and \
                response_regcall.json().get('Type') == 0:
            print('')
            pprint.pprint(response_regcall.json(), sort_dicts=False)
        else:
            print('\nрегистрация заявки не выполнена')
        break
    except requests.RequestException:
        conn_err_handler()
        continue

# SignOut
while True:
    try:
        response_signout = requests.post(base_url +
                                         'accountApi/SignOut',
                                         headers=session_headers)
        if dict(response_signout.headers)['Content-Type'] == \
                'application/json; charset=utf-8' and \
                response_signout.json() is True:
            print('\nвыход выполнен, завершение работы..')
            break
        else:
            while auth_handling := input('\nвыход не выполнен, '
                                         'попробовать еще раз (Y/N): '):
                if auth_handling == 'Y' or auth_handling == 'y':
                    break
                elif auth_handling == 'N' or auth_handling == 'n':
                    print('\nзавершение работы..')
                    sys.exit()
                else:
                    continue
    except requests.RequestException:
        conn_err_handler()
        continue
