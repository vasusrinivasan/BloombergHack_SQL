FAILURE = 1
SUCCESS = 0

carrier_lookup = { 'att':'txt.att.net',
				   'at&t':'txt.att.net',
				   'verizon':'vtext.com',
				   'boost':'myboostmobile.com',
				   'virgin':'vmobl.com'}

import smtplib

username = 'ticker.watch.app@gmail.com'
password = 'thankyoupepsi'
from_addr = 'ticker.watch.app@gmail.com'
to_addr  = None

def current_time() :
    return time.time()

def send_text(number, carrier, msg):
	# Check for valid number
	to_addr = str(number) + '@'
	if (len(str(number)) != 10):
		return FAILURE
	# Build to_addr
	if (carrier not in carrier_lookup):
		return FAILURE
	else:
		to_addr += carrier_lookup[carrier]
	# Mail message
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(username,password)
	server.sendmail(from_addr, to_addr, msg)
	server.quit()
	return SUCCESS