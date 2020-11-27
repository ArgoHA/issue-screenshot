import time, sys, smtplib, os, yaml, configparser, pymysql
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from contextlib import closing


# Логинимся в AppDynamics
def login_apd():
    driver.get('https://link_to_appdynamics.ru') # переходим на страницу ввода логина и пароля
    time.sleep(5)

    write_login = driver.find_element_by_xpath('//*[@id="userNameInput"]') # находим поле воода логина
    write_login.send_keys('login') # вводим login

    write_password = driver.find_element_by_xpath('//*[@id="passwordInput"]')
    write_password.send_keys('password')

    enter = driver.find_element_by_xpath('//*[@id="submitInput"]') # находим кнопку "отправить"
    enter.click() # Нажимаем!
    time.sleep(3)


# Логинимся в Splunk
def login_splunk():
    driver.get('https://link_to_splunk.ru')
    time.sleep(3)

    write_login = driver.find_element_by_xpath('//*[@id="username"]')
    write_login.send_keys('login')

    write_password = driver.find_element_by_xpath('//*[@id="password"]')
    write_password.send_keys('password')

    enter = driver.find_element_by_xpath('/html/body/div[2]/div/div/div[1]/form/fieldset/input[1]')
    enter.click()
    time.sleep(3)


# Делаем скрин шот нужного элемента
def get_a_screenshot():
    element = driver.find_element_by_xpath(xpath)
    try:
        element.screenshot(image_path)
    except:
        print('Не вышло, еще раз')
        time.sleep(1)
        element.screenshot(image_path)


# Отправляем письмом нужное сообщение и прикрепляем скриншот. Дублируем в Teams
def send_an_email():
    host = "mail.ru"
    msg = MIMEMultipart()
    msg['Subject'] = alarm_title # Заголовок письма
    msg['From'] = 'email_to_send_from@mail.ru' # рисуем с какой почты будет отправляться письмо.
    msg['To'] = ','.join(recipients) # Для отображения получателей в письме. По фатку отправляется группе recipients

    # формируем текст и прикрепляем изображение
    msg_text = MIMEText(f'{alarm_text}<br><br><img src="cid:image">', 'html')
    msg.attach(msg_text)
    fp = open(image_path, "rb")
    msg_image = MIMEImage(fp.read())
    fp.close()
    msg_image.add_header('Content-ID', '<image>')
    msg.attach(msg_image)

    server = smtplib.SMTP(host, 587)
    server.starttls()
    server.login('login','password') # логин и пароль от почты, с которой письмо отправляется
    server.sendmail(msg['From'], recipients, msg.as_string())
    time.sleep(3)
    try:
        server.quit()
    except smtplib.SMTPServerDisconnected:
        print('Yeah, it happened.')


while True:
    count_now = 0

    service_ids = []
    alarm_titles = []
    urls = []
    xpaths = []
    recipientss = []
    image_paths = []
    drivers = []
    issues = []

    # подключаемся к базе данных
    with closing(pymysql.connect(host='host.ru', user='user_name', password='password', db='db_name')) as connection:
        connection.autocommit(True) # автокоммит
        with connection.cursor() as first_query: # получаю список групп дашбордов выполнив sql запрос
            sql_1 = "select * from table_name;"
            count_rows = first_query.execute(sql_1)

            # заполняем все необходимые данные
            for row in first_query:
                count_now += 1
                service_ids.append(row[0])
                alarm_titles.append(row[1])
                urls.append(row[2])
                xpaths.append(row[4])
                recipientss.append(row[5].split(','))
                image_paths.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/" + str(service_ids[count_now - 1]) + ".png")

                # создаем виртуальный браузер chrome
                options = webdriver.ChromeOptions()
                options.add_argument('window-size=2100x1440')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.headless = True
                drivers.append(webdriver.Chrome('/opt/chromedriver/chromedriver', options=options))

            first_query.close

        # проверяем в какой системе нужно открыть дашборд и логинимся в нее
        for i in range(len(drivers)):
            driver = drivers[i]
            url = urls[i]

            if 'link_to_splunk.ru' in url:
                login_splunk()
                driver.get(url)

            elif 'link_to_appdynamics.ru' in url:
                login_apd()
                driver.get(url)

        time.sleep(30) # ждем загрузку дашбордов

        # обращаемся к базе данных для проверки сбоев
        for n in range(100):
            with connection.cursor() as second_query:
                for i in range(len(service_ids)): # проходим по каждому сервису

                    # забираем последнюю дату проверки сервиса
                    config = configparser.ConfigParser()
                    config_file_name = sys.argv[0].replace('py', 'ini') # универсальная ссылка на настроечный файл
                    try:
                        config.read(config_file_name)
                        date = config.get(service_ids[i], 'date')
                    except:
                        date = datetime(2020, 1, 1, 1, 11, 11)

                    # Передаем в базу название сервиса и дату последней проверки
                    sql_2 = f"call proc_name('{service_ids[i]}', str_to_date('{date}', '%Y-%m-%d %H:%i:%s'));"
                    second_query.execute(sql_2) # запускаем процедуру sql
                    for row in second_query:
                        new_date = row[0] # дата последней проверки
                        try:
                            config[service_ids[i]]['date'] = str(new_date) # обновляем дату последней проверки
                            with open(config_file_name, 'w') as config_file:
                                config.write(config_file)
                        except: # если сервис новый и ранее не мониторился - автоматически создается новый раздел в ini
                            config.add_section(service_ids[i])
                            config[service_ids[i]]['date'] = str(new_date)
                            with open(config_file_name, 'w') as config_file:
                                config.write(config_file)

                    # Если бд вернула не нулевую ошибку - добавляем ее в список ошибок (их может быть несколько на сервис)
                        if row[1] != None:
                            issues.append(row[1])

                    if len(issues) > 0:
                        for issue in issues: # прохоим по ошибкам
                            issue = issue.replace(',', '<br>')
                            now = datetime.now().strftime('%H:%M') # текущее время
                            alarm_text = f'В {now} обнаружена проблема с:<br>{issue}' # формируем текст сообщения

                            driver = drivers[i] # уточняем какой браузер из открытых нам нужен
                            alarm_title = alarm_titles[i]
                            xpath = xpaths[i]
                            recipients = recipientss[i]
                            image_path = image_paths[i]

                            try: # проверяем не выбило ли из системы, если нужно - логинимся
                                driver.find_element_by_xpath('//*[@id="username"]')
                                login_splunk()
                                driver.get(url)
                                time.sleep(30)
                            except:
                                pass

                            get_a_screenshot() # делаем скрин шот
                            send_an_email() # отправляем письмо

                        issues = [] # очищаем список ошибок в конце цикла

            time.sleep(30) # ждем 30 секунд перед повторым запросом в бд, чтобы не перегружать бд

    # проходим по всем браузерами и закрываем их. Если не заврешить процессы - оперативка быстро закончится
    for driver in drivers:
        driver.quit()
