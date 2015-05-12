import datetime
import urllib2
import argparse
import httplib2
from apiclient import errors
from email.mime.text import MIMEText
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser
import base64
import email
import time
from apiclient import errors


# Parse the command-line arguments (e.g. --noauth_local_webserver)
parser = argparse.ArgumentParser(parents=[argparser])
flags = parser.parse_args()

# Path to the client_secret.json file downloaded from the Developer Console
CLIENT_SECRET_FILE = 'client_secret.json'

# Check https://developers.google.com/gmail/api/auth/scopes
# for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.modify'

# Location of the credentials storage file
STORAGE = Storage('gmail.storage')

# Start the OAuth flow to retrieve credentials
flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
http = httplib2.Http()

# Try to retrieve credentials from storage or run the flow to generate them
credentials = STORAGE.get()
if credentials is None or credentials.invalid:
  credentials = run_flow(flow, STORAGE, flags, http=http)

# Authorize the httplib2.Http object with our credentials
http = credentials.authorize(http)

# Build the Gmail service from discovery
gmail_service = build('gmail', 'v1', http=http)



def ListMessagesMatchingQuery(service, user_id, query=''):
  """List all Messages of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
    Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

  Returns:
    List of Messages that match the criteria of the query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate ID to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query,
                                         pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError, error:
    print 'An error occurred: %s' % error
def ListMessagesWithLabels(service, user_id, label_ids=[]):
  """List all Messages of the user's mailbox with label_ids applied.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_ids: Only return Messages with these labelIds applied.

  Returns:
    List of Messages that have all required Labels applied. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate id to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id,
                                                 labelIds=label_ids,
                                                 pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError, error:
    print 'An error occurred: %s' % error
def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id,format='metadata').execute()

    #	print 'Message snippet: %s' % message['snippet']

    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error
def SendMessage(service, user_id, message):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print 'Message Id: %s' % message['id']
    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error
def CreateMessage(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64 encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.b64encode(message.as_string())}
def GetMimeMessage(service, user_id, msg_id):
  """Get a Message and use it to create a MIME Message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A MIME Message, consisting of data from Message.
  """
  try:
	message = service.users().messages().get(userId=user_id, id=msg_id,
                                             format='raw').execute()

	#print 'Message snippet: %s' % message['snippet']

	msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

	mime_msg = email.message_from_string(msg_str)

    #return mime_msg
	return msg_str
  except errors.HttpError, error:
    print 'An error occurred: %s' % error
def parseDate(date):
    months={'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
    day = int(date[:date.find(' ')])
    date = date[date.find(' ')+1:]
    month = months[date[:date.find(' ')]]
    date = date[date.find(' ')+1:]
    year = int(date[:date.find(' ')])
    date = date[date.find(' ')+1:]
    hour = int(date[:date.find(':')])
    date = date[date.find(':')+1:]
    minute = int(date[:date.find(':')])
    date = date[date.find(':')+1:]
    second = int(date[:date.find(' ')])
    date = date[date.find(' ')+1:]
    return datetime.datetime(year,month,day,hour,minute,second)
def processMessage(message):
    orders = []
    message =message.replace("=\r\n","")
    search_string =   'style=3D"text-decoration: none; color: rgb(0, 102, 153); font: 12px/ 16px Arial, sans-serif"> '
    search_string2 = '<td class=3D"name"'
    start = message.find(search_string2)
    message = message[start+50:]
    start = message.find(search_string)
    while start!= -1:
        start = message.find("www.")
        message = message[start:]
        end = message.find('" sty')
        address= message[:end].replace('=3D','=')
        message = message[end+1:]       
        start = message.find(search_string)
        end = start+len(search_string)+message[start+len(search_string):].find(' </a>')
        item = message[start+len(search_string):end]
        message = message[end:]
        start = message.find('<br /> ')
        category = message[start+7:start+7+message[start+7:].find('<br />')].replace('=\r\n','')
        message = message[message.find('Sold by ')+8:]
        seller = message[:message.find(' <br />')]
        if seller!='Amazon.com LLC':
            seller = seller[seller.find('>')+1:]
            seller = seller[:seller.find('<')]
        message = message[message.find(' <br />')+7:]
        price = message[message.find('<strong>$')+9:message.find('</strong>')]
        if seller=='Amazon.com LLC':
            #print item,category,seller,price
            orders += [[item,category,price,address]]
        message = message[message.find(search_string2):]
        start = message.find(search_string)
    return orders
def parse_date(date):
    year = date[:date.find('-')]
    date = date[date.find('-')+1:]
    month = date[:date.find('-')]
    date = date[date.find('-')+1:]
    day = date[:date.find(' ')]
    date = date[date.find(' ')+1:]
    hour = date[:date.find(':')]
    date = date[date.find(':')+1:]
    minute = date[:date.find(':')]
    date = date[date.find(':')+1:]
    second = date
    datet = datetime.datetime(int(year),int(month),int(day),int(hour),int(minute),int(second))
    return datet
def load_old_keys():
    key_file = open('keys.txt','r')
    old_keys = []
    unparsed_keys = key_file.readlines()
    for line in unparsed_keys:
        old_keys += [parse_date(line)]
    return old_keys
def checkPrice(address):
    opener = urllib2.build_opener()
    opener.addheaders=[('User-agent', 'Mozilla/5.0')]
   
    response = opener.open(address)
    the_page = response.read()
    price = the_page.find("<strong>T")
    the_page = the_page[price-30:price].replace('"','').rstrip(" >")
    price = the_page.find("price")
    price = float(the_page[price+6:])
    return price

matches = ListMessagesMatchingQuery(gmail_service, 'me', query='auto-confirm@amazon.com sold by amazon llc')
order_dict = {}
for match in matches:
    message = GetMimeMessage(gmail_service,'me',match['id'])
    date_message = GetMessage(gmail_service,'me',match['id'])
    date = date_message['payload']['headers'][1]['value']
    date = date[date.find('        ')+13:]
    items = processMessage(message)
    if len(items)>0:
        order_dict[parseDate(date)]= items

old_orders = load_old_keys()
orders_to_check = []
current = datetime.datetime.today()
output = open('keys.txt','a')
for key in order_dict.keys():
    diff = current - key
    if diff.days<=7:
        if key not in old_orders:
            message = CreateMessage("ogothe@gmail.com","ogothe@gmail.com","Amazon Order Tracker","Amazon Order from "+str(key)+" is now being tracked. ")
            SendMessage(gmail_service,'me',message)
            print str(key)
            output.write(str(key)+"\n")
        orders_to_check += [order_dict[key]]
output.close()

while True:
    for order in orders_to_check:
        for item in order:
            if len(item)>0:
                #print item[3]
				new_price = checkPrice("http://"+item[3])
				print new_price,item[2]
				if float(new_price) < float(item[2]):
					message = CreateMessage("ogothe@gmail.com","ogothe@gmail.com","Amazon Price Drop","The price of "+item[0]+" has dropped from $" + str(item[2]) + " to $" +str(new_price) + ".")
					SendMessage(gmail_service,'me',message)
					item[2]=new_price
    time.sleep(60*60*12)




