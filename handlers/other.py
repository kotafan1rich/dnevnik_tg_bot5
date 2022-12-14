import datetime
import pickle
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from db import Database

db = Database('db_dnevnik_tg_bot.db')

ua = [
    'Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
    'Opera/9.80 (X11; Linux i686; U; ru) Presto/2.8.131 Version/11.11',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
    'Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1',
    'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1',
    'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25'
]


# proxies = ['89.107.197.165:3128', '89.108.74.82:1080']


def get_data(date_f, date_t, user_id):
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={random.choice(ua)}')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--headless')
    # options.add_argument(f'--proxy-server={random.choice(proxies)}')

    driver = webdriver.Chrome(
        executable_path=r'C:\Users\Алексей\PycharmProjects\dnevnik_tg_bot\chrome\chromedriver.exe',
        options=options
    )

    url = 'https://dnevnik2.petersburgedu.ru'
    # url1 = 'https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html'

    login, password = db.get_login_and_password(user_id)[0], db.get_login_and_password(user_id)[1]
    # print(login)
    #
    # print(password)
    driver.get(url=url)
    get_esia = driver.find_element(By.CLASS_NAME, 'button_tone_default')
    driver.execute_script("arguments[0].click();", get_esia)
    time.sleep(5)
    email_esia = driver.find_element(By.ID, 'login')
    passw_esia = driver.find_element(By.ID, 'password')
    email_esia.send_keys(login)
    passw_esia.send_keys(password)
    driver.find_element(By.ID, 'loginByPwdButton').click()
    time.sleep(2)
    pickle.dump(driver.get_cookies(), open(f'cookies/cookies{user_id}', 'wb'))
    driver.get('https://dnevnik2.petersburgedu.ru/estimate')
    cookies1 = driver.get_cookies()
    for cookie in pickle.load(open(f'cookies/cookies{user_id}', 'rb')):
        driver.add_cookie(cookie)

    driver.refresh()
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Access-Control-Allow-Origin': '*',
        'Connection': 'keep-alive',
        'Content-Type': 'text/plain',
        'Referer': 'https://dnevnik2.petersburgedu.ru/estimate',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-agent': random.choice(ua),
        'X-KL-Ajax-Request': 'Ajax_Request',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
        'sec-ch-ua-mobile': '?0',
    }

    params = {
        'p_page': '1',
    }

    cookies = {}
    for cookie in cookies1:
        cookies[cookie['name']] = str(cookie['value'])

    p_educations_response = requests.get('https://dnevnik2.petersburgedu.ru/api/journal/person/related-child-list',
                                         params=params, cookies=cookies, headers=headers).json()
    p_educations = p_educations_response.get('data').get('items')[0].get('educations')[0].get('education_id')

    params = {
        'p_educations[]': p_educations,
        'p_date_from': date_f,
        'p_date_to': date_t,
        'p_limit': '100',
        'p_page': '1',
    }

    response = requests.get('https://dnevnik2.petersburgedu.ru/api/journal/estimate/table', params=params,
                            cookies=cookies, headers=headers).json()

    marks = {}
    marks_info = response.get('data').get('items')
    for i in marks_info:
        if i['subject_name'] != 'Физическая культура':
            marks[i['subject_name']] = []

    for i in marks_info:
        if i['subject_name'] != 'Физическая культура':
            if 'Годовая' not in i['estimate_type_name'] and 'Итоговая' not in i['estimate_type_name'] and 'четверть' not in i['estimate_type_name'] and 'Посещаемость' not in i['estimate_type_name']:
                if 'работа' in i['estimate_type_name'] or 'Работа' in i['estimate_type_name'] or 'Задание' in i['estimate_type_name']:
                    marks[i['subject_name']].append(int(i['estimate_value_name']))

    total_pages = response.get('data').get('total_pages')

    if int(total_pages) > 1:
        if total_pages > 2:
            for i in range(2, total_pages + 1):
                params = {
                    'p_educations[]': p_educations,
                    'p_date_from': date_f,
                    'p_date_to': date_t,
                    'p_limit': '100',
                    'p_page': i,
                }

                response = requests.get('https://dnevnik2.petersburgedu.ru/api/journal/estimate/table', params=params,
                                        cookies=cookies, headers=headers).json()
                marks_info = response.get('data').get('items')

                for j in marks_info:
                    if j['subject_name'] != 'Физическая культура':
                        if 'Годовая' not in j['estimate_type_name'] and 'Итоговая' not in j['estimate_type_name'] and 'четверть' not in j['estimate_type_name'] and 'Посещаемость' not in j['estimate_type_name']:
                            if 'работа' in i['estimate_type_name'] or 'Работа' in i['estimate_type_name'] or 'Задание' in i['estimate_type_name']:
                                marks[i['subject_name']].append(int(i['estimate_value_name']))
        else:
            params = {
                'p_educations[]': p_educations,
                'p_date_from': date_f,
                'p_date_to': date_t,
                'p_limit': '100',
                'p_page': 2,
            }

            response = requests.get('https://dnevnik2.petersburgedu.ru/api/journal/estimate/table', params=params,
                                    cookies=cookies, headers=headers).json()
            marks_info = response.get('data').get('items')

            for j in marks_info:
                if j['subject_name'] != 'Физическая культура':
                    if 'Годовая' not in j['estimate_type_name'] and 'Итоговая' not in j['estimate_type_name'] and 'четверть' not in j['estimate_type_name'] and 'Посещаемость' not in j['estimate_type_name']:
                        if 'работа' in j['estimate_type_name'] or 'Работа' in j['estimate_type_name'] or 'Задание' in j['estimate_type_name']:
                            marks[j['subject_name']].append(int(j['estimate_value_name']))

    data = {'data': marks}

    for i in data['data']:
        try:
            data['data'][i] = round(sum(data['data'][i]) / len(data['data'][i]), 2)
        except ZeroDivisionError:
            data['data'][i] = 'нет оценок'
    if data == {}:
        data = 'нет оценок'
    # driver.close()
    return data


def get_m_result(quater: int, user_id):
    year = int(datetime.datetime.now().year)
    month_now = int(datetime.datetime.now().month)
    if quater > 5:
        return 'четверть длжна быть меньше или равна 5, чтобы получить результат'
    if 5 < month_now < 9:
        if quater == 1:
            date_from = f'01.09.{year - 1}'
            date_to = f'30.10.{year - 1}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
        elif quater == 2:
            date_from = f'05.11.{year - 1}'
            date_to = f'31.12.{year - 1}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
        if quater == 3:
            date_from = f'10.01.{year}'
            date_to = f'25.03.{year}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
        elif quater == 4:
            date_from = f'06.04.{year}'
            date_to = f'30.05.{year}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
        elif quater == 5:
            date_from = f'01.09.{year - 1}'
            date_to = f'30.05.{year}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
    else:
        if quater == 1:
            date_from = f'01.09.{year}'
            date_to = f'30.10.{year}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
        elif quater == 2:
            date_from = f'05.11.{year}'
            date_to = f'31.12.{year}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
        elif quater == 3:
            date_from = f'10.01.{year + 1}'
            date_to = f'25.03.{year + 1}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
        elif quater == 4:
            date_from = f'01.04.{year + 1}'
            date_to = f'30.05.{year + 1}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
        else:
            date_from = f'01.09.{year}'
            date_to = f'30.05.{year + 1}'
            result: dict = get_data(date_t=date_to, date_f=date_from, user_id=user_id).get('data')
            sort_result = dict(sorted(result.items()))
            res = f'{quater} четверть\n\n'
            for i, j in sort_result.items():
                res += f'{i}: {j}\n'
            res = res.replace('Основы безопасности жизнедеятельности', 'ОБЖ').replace('Изобразительное искусство',
                                                                                      'ИЗО')
            return res
