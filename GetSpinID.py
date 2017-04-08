from bs4 import BeautifulSoup
import urllib2
import argparse
import sqlite3
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

spinURL = 'http://www.wheelspinid.com/spin/pastnos.php'
conn = sqlite3.connect('spinid.db', detect_types=sqlite3.PARSE_DECLTYPES)
c = conn.cursor()

class SpinObject(object):
    def __init__(self, spinID, showDate):
        self.spinid = spinID
        self.showdate = showDate
    def __str__(self):
        return self.spinid + ' was the spinID for ' + str(self.showdate)

    def HasAlreadyRetrieved(self):
        returnValue = False
        sql = 'select spinid from spinid where spinid = ? or showdate = ?'
        c.execute(sql, (self.spinid, datetime.date(self.getYear(), self.getMonth(), self.getDay())))
        data=c.fetchall()
        if len(data) == 0:
            print 'SpinID not retrieved yet for: ' + str(self)
        else:
            print 'SpinID ALREADY retrieved for: ' + str(self)
            returnValue = True
        return returnValue

    def Persist(self):
        sql = 'insert into spinid (spinid, showdate) values (?, ?)'
        c.execute(sql, (self.spinid, datetime.date(self.getYear(), self.getMonth(), self.getDay())))
        conn.commit()

    def getMonth(self):
        parts = self.showdate.split('-')
        if len(parts) == 3:
            month = parts[0]
            return int(month)
        else:
            return None
    def getDay(self):
        parts = self.showdate.split('-')
        if len(parts) == 3:
            day = parts[1]
            return int(day)
        else:
            return None
    def getYear(self):
        parts = self.showdate.split('-')
        if len(parts) == 3:
            year = '20' + str(parts[2])
            return int(year)
        else:
            return None


def ConnectToDB():
    sql = 'create table if not exists spinid (spinid VARCHAR(255), showdate DATE)'
    c.execute(sql)

    c.execute(sql)
    conn.commit()

def sendEmail(newspin):
    Body = '<html><p>' + str(newspin) + '</p></html>'
    Body = Body.encode('ascii','ignore')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "WoF"
    msg['From'] = 'noreply@example.com'
    recipients = []
    parts = args['recipient'].split(',')
    for recipient in parts:
        recipients = []
        recipients.append(recipient)
        msg['BCC'] = ", ".join(recipients)

    #     # Create the body of the message (a plain-text and an HTML version).
        text = Body
        html = Body
    #     # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
    #
    #     # Attach parts into message container.
    #     # According to RFC 2046, the last part of a multipart message, in this case
    #     # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)
    #
        smtpserver = smtplib.SMTP(args['smtpserver'],timeout=10)
    #     # Send the message via local SMTP server.
        if args['smtpuser'] != "":
            print('Starting TTLS with user %s' % args['smtpuser'])
            smtpserver.starttls()
            smtpserver.login(args['smtpuser'], args['smtppassword'])
    #     # sendmail function takes 3 arguments: sender's address, recipient's address
    #     # and message to send - here it is sent as one string.
            smtpserver.sendmail('noreply@example.com', recipients, msg.as_string())
            smtpserver.quit()


def GetSpinID():
    request = urllib2.Request(spinURL)
    response = urllib2.urlopen(request)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')
    headers = soup.find_all('span', {'class': 'header2'})
    if len(headers) == 1:
        spans = soup.find_all('span', recursive = False)
        for span in spans:
            if span.text.find('$5,000 Prize'):
                spinid = span.text[:10].strip()
                header = headers[0].text[30:].strip()
                newspin = SpinObject(spinid, header)
                print newspin
                if not newspin.HasAlreadyRetrieved():
                    sendEmail(newspin)
                    newspin.Persist()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grabs SpinID, sends it.")
    parser.add_argument('-recipient','--recipient',help='Email Recipient', required=True)
    parser.add_argument('-smtpuser','--smtpuser',help='SMTP User', required=False)
    parser.add_argument('-smtppassword','--smtppassword',help='SMTP Password', required=False)
    parser.add_argument('-smtpserver','--smtpserver',help='SMTP Server', required=True)
    ConnectToDB()

    args = vars(parser.parse_args())

    GetSpinID()