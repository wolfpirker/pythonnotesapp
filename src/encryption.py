"""encryption related methods used for IO operations;
   currently Blowfish is used"""

# pycrypto must be installed to use this module!

#import random, hashlib
from Crypto.Cipher import Blowfish
from Crypto import Random
from struct import pack 

# https://www.dlitz.net/software/pycrypto/api/current/
def encrypt_text(plaintext, password):
	"""method encrypts a text using a password, returns the encrypted text using 
	blowfish encryption"""
	bs = Blowfish.block_size
	# sometimes it will cut off the first character, that's why there is an 
	# additional space
	hexcode = (' ' + plaintext).encode('hex')
	iv = Random.new().read(bs)
	cipher = Blowfish.new(password, Blowfish.MODE_CBC, iv)
	plen = bs - divmod(len(hexcode),bs)[1]
	padding = [plen]*plen
	padding = pack('b'*plen, *padding)
	msg = iv + cipher.encrypt(hexcode + padding)
#text_string_escape = text.decode('string_escape')
	return msg.encode('hex')
	
	# a issue: function will take a unicode string, not a (b') Bytestring
	# possible way to solve this:
		# use of plaintext.encode('hex')
		# below decryption before it's decoded back to utf-8 string it's
		# important to the padding 
		# decrypted_text[len(padding):-len(padding)].decode('hex')
		# Schwierigkeit: Wie dann in MongoDB ablegen!?
		# --> encode('punycode') oder encode('hex') funktioniert
		# ebenso: .encode('base64')
		# nach Zurueckholung dekodieren
		# punycode: not possible to show this in GtkTextBuffer	
		# resultiert in kritischen Fehler!

		# --> why punycode and base64 are not good choices:
			# punycode decryption does sometimes not work correctly (UnicodeEncodeError)
			# base64: validation test via method  below very unreliable
		# --> what about hex:
			# validation test quite reliable, no UnicodeEncodeErrors
			# decode and encode operations faster
			# text longer, that's bearable

		# issue: padding lengths varies sometimes!
		# decry_text[len(padding)*2:-len(padding)]
		# decry_text[len(padding):-len(padding)]
		# falls zu wenig abgeschnitten wurde erscheint "TypeError"


def decrypt_text(enc_text, password):
	"""method decrypts a text using a password, returns the decrypted text using 
	blowfish encryption"""
	bs = Blowfish.block_size
	try: # filesystem case
		enc_text = enc_text[:-1].decode('hex')
	except TypeError: # encryption in Mongo case
		try:
                        enc_text = enc_text.replace('\n','').decode('hex')
                except TypeError:
                        return ("Encrypted Note!")
	iv = Random.new().read(bs)
	cipher = Blowfish.new(password, Blowfish.MODE_CBC, iv)
	decry_text = cipher.decrypt(enc_text)

	bs = Blowfish.block_size # why again???
	plen = bs - divmod(len(decry_text),bs)[1]
	padding = [plen]*plen
	padding = pack('b'*plen, *padding)
	
	# validate password
	#trail = decry_text[-1]
	#print 'the trail: ' + repr(trail)
	#if not validate(trail):
	#	return False

	try: # if possible text from filesystem successfully decrypted
		return decry_text[len(padding):-len(padding)].decode('hex').lstrip(' ')
	except TypeError: # if possible text from Mongo successfully decrypted
                try:
                        return decry_text[48:-8].decode('hex')
                except TypeError: # happens when it still contains non-hexadecimal characters
                        #try:
                        #	return decry_text[len(padding)*2:-len(padding)].decode('hex').lstrip(
                        #		' ')
                        #except TypeError: # if password was not correct
                        print "wrong password; decrypted text contains non-hex characters"
                        return False

		
#def validate(trail): # completely redundant!!!
#	"""via the padding information it's possible to find out, if the password 
#	is very likely correct"""
#	if trail == '\x04' or trail == '\x08' or trail == '\06':
#		return True # password is probably right
#	else:
#		return False # password is wrong

def check_if_encrypted(text): 
	"""returns true if text can be punycode decoded"""
	try:
                text.split('\n')[0].decode('hex')
                # Note: read in mongo module includes a '\n' even in encrypted texts
		print("encrypted")
		return True
	except TypeError:
                try:
                        text[:-1].decode('hex') # TOCHECK: must last character really be cut off?
                        # maybe this case is redundant!?
                        print "in pw validation -> last character cut off"
                except:
                        return False

#def change_password(enc_text, key, new_key):
#	"""change the password of an encrypted text"""
	# following check is redundant if it is sure that this method only can be 
	# called on encrypted texts
#	if not check_if_encrypted(enc_text):
#		return False
#	decry_text = decrypt_text(key, enc_text)
#	if decry_text:
#		new_text = encrypt_text(new_key, decry_text)
#		return new_text
#	else:
#		return False
	
