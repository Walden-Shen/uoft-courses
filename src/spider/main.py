from Database import *
import json
import requests
import re
from urllib.parse import urlencode
from bs4 import BeautifulSoup

DB_PATH = '../../database.info'

BASE_URL = 'http://coursefinder.utoronto.ca/course-search/search/courseSearch/course/search?'
DETAIL_BASE_URL = 'http://coursefinder.utoronto.ca/course-search/search/courseInquiry?methodToCall=start&viewId=CourseDetails-InquiryView&courseId='

headers = {
    'Referer': 'http://coursefinder.utoronto.ca/course-search/search/courseSearch?viewId=CourseSearch-FormView&methodToCall=start',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}

all_courses_params = {
    'queryText': '',
    'requirements': '',
    'campusParam': 'St. George,Scarborough,Mississaga'
}

COMMIT_BUFFER = 15

def get_all_courses_json():
    url = BASE_URL + urlencode(all_courses_params)
    session = requests.session()
    try:
        session.get(url, headers=headers) # DON'T delete this line, otherwise you will get 403
        r = session.get(url, headers=headers) 
        if r.status_code == 200:
            return r.json()
        else:
            print('Error:', r.status_code)
    except requests.ConnectionError as e:
        print('Error', e.args)
        return None

def parse_json(json):
    for course in json['aaData']:
        detail_url = re.search("coursedetails/(.*?)'>", course[1]).group(1)
        url = DETAIL_BASE_URL + detail_url
        info_dict = parse_course_detail(get_course_detail(url))

        info_dict['cID'] = re.search(">(.*?)<", course[1]).group(1)
        info_dict['cName'] = course[2]
        info_dict['credits'] = course[3]
        info_dict['campus'] = course[4].strip(' ')
        info_dict['department'] = course[5].strip(' ')
        info_dict['term'] = course[6]
        info_dict['division'] = course[7].strip(' ')
        
        yield info_dict

def get_course_detail(url):
    try:
        r = requests.get(url, headers = headers)
        if r.status_code == 200:
            return r.text
        else:
            print('Error:', r.status_code)
    except requests.ConnectionError as e:
        print('Error: ', e.args)
        return None

def parse_course_detail(html):
    soup = BeautifulSoup(html, 'lxml')
    prerequisites = soup.find('span', attrs = {'id': "u50"})
    exclusion = soup.find('span', attrs = {'id': 'u68'})
    br = soup.find('span', attrs = {'id': 'u122'})
    table = soup.find_all('span', attrs = {'id': re.compile("^u2(45|54|63|72|81|90)_line\d$")})
    clean_pattern = re.compile(' \n|\n|\r')
    return {
            "prerequisites": prerequisites.getText().strip('\r\n') if prerequisites is not None else None,
            "exclusion": exclusion.getText().strip('\r\n') if exclusion is not None else None,
            "br": br.getText().strip('\r\n') if br is not None else None,
            "lecNum": [re.sub(clean_pattern, '', table[6 * i].getText()) for i in range(len(table) // 6)],
            "lecTime": [re.sub(clean_pattern, '', table[1 + 6 * i].getText()) for i in range(len(table) // 6)],
            "instructor": [re.sub(clean_pattern, '', table[2 + 6 * i].getText()) for i in range(len(table) // 6)],
            "location": [re.sub(clean_pattern, '', table[3 + 6 * i].getText()) for i in range(len(table) // 6)],
            "size": [re.sub(clean_pattern, '', table[4 + 6 * i].getText()) for i in range(len(table) // 6)],
            "currentEnrollment": [re.sub(clean_pattern, '', table[5 + 6 * i].getText()) for i in range(len(table) // 6)]
            }


if __name__ == '__main__':
    init_db(DB_PATH)

    connection = get_connection(DB_PATH)
    cursor = connection.cursor()

    count = 0 
    for course_dict in parse_json(get_all_courses_json()):
        insert_data(cursor, course_dict)
        count += 1
        if count == COMMIT_BUFFER:
            commit_data(connection)
            count = 0
    
    connection.close()

