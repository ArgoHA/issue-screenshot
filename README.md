# issue-screenshot

This script was created to inform responcible people if there is an issue in splunk or appdynamic metrics with screenshots of dashboards. As you can not do that with built in tools (when you need a screenshot of the dashboard), it's done with custom database and python script

Script can open different dashboards in crhome and then check it there's an issue (issues are being written in database). If there is one - script gets a screenshot of needed dashboard, writes a message and sends it vy email and MS Teams.

This script runs on headless virtual server (Cent OS) as a linux daemon.

Скрипт был создан для информирования ответственных в случае проблем с метриками splunk или appdynamics с прикриплением скрин шотов дашборда. Так как стандартные инструменты не позволяют отправлять визуализацию, приходится реализовывать это на python с кастомной базой данных

Скрипт открывает несколько дашбордов в хроме и проверяет не зарегистрированы ли ошибки в базе данных. Если ошибки есть - скрипт формирует скрин шот необходимого дашборда и отправляет электронное письмо и сообщение в MS Teams, прикрепив скрин шот.

Этот скрипт работает на виртуальном сервере без подключенного монитора (Cent OS) как линуксовый сервис

