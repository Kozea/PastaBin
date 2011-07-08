from email.encoders import encode_base64
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from flask import g, current_app
from utils.html2text import html2text
import re
import smtplib

TXT_SIGNATURE = u"""
--
Admin Pastabin
"""

# MAIL
PORT_MAIL = 25
SERVER_MAIL = "smtp.free.fr"
SUPPORT_ADDRESS = 'support@pharminfo.fr'
REPLACEMENT_ADDRESS = 'amardine.david@gmail.com'


class SmtpAgent(object):
    def __init__(self):
        self.__agent = None

    def sendmail(self, recipient, msg, from_field=None):
        if from_field is None:
            from_field = SUPPORT_ADDRESS
#        if current_app.config['DEBUG']:
        # replace adresse in test application
            recipient = REPLACEMENT_ADDRESS
        self.agent.sendmail(from_field, recipient, msg)

    @property
    def agent(self):
        port = PORT_MAIL
        server = SERVER_MAIL
        self.__agent = self.__agent or smtplib.SMTP(server, port)
        return self.__agent

    def sendmail_alternative(self, message="", subject="", recipient="", attachment=None):
        """Takes an HTML message, subject, recipient and optional attachment and send it
        in both text and html forms
        """
        msg = MIMEMultipart('mixed')
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = html2text(subject)
        message_txt = html2text(message, indent_width=2) + TXT_SIGNATURE
        msg['To'] = recipient
        msg_content = MIMEMultipart('alternative')
        msg_content.attach(
            MIMEText(message_txt.encode('utf-8'), 'plain', 'utf-8'))
        msg_content.attach(
            MIMEText(message.encode('utf-8'), 'html', 'utf-8'))
        msg.attach(msg_content)
        if attachment:
            msg.attach(attachment)
        self.sendmail(recipient, msg.as_string())


    def quit(self):
        if self.__agent:
            self.__agent.quit()

