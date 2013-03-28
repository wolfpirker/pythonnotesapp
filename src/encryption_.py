"""encryption related methods used for IO operations;
   currently Blowfish is used"""

#import random, hashlib
from Crypto.Cipher import Blowfish
from Crypto import Random
from struct import pack

# Must: pycrypto+bluefish:
	# let users specify a password, use the sha1 hash algorithm and save the
	# encrypted_password to a user specified file

# Nice-To-Have for improved (key) security:
	# use of python-gnupg: http://packages.python.org/python-gnupg/
	# http://code.google.com/p/python-gnupg/
	# as alternative choice to pycrypto+bluefish
	# not a high priority
 

#def get_hexdigest(algo, rand, rand2):
#	return hashlib.sha1('%s%s' % (salt, hash)).hexdigest()
	
#def set_password(self, raw_password):
	#return hashlib.sha256(raw_password).digest()
#    algo = 'sha1'
#   salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
#   hsh = get_hexdigest(algo, salt, raw_password)
#    return '%s$%s$%s' % (algo, salt, hsh)

#def check_password(raw_password, enc_password):
#    """
#    Returns a boolean of whether the raw_password was correct. Handles
#    encryption formats behind the scenes.
#    """
#    algo, salt, hsh = enc_password.split('$')
#    return hsh == get_hexdigest(algo, salt, raw_password)

def encrypt_text(enc_password):
	bs = Blowfish.block_size

# encrypted texts must be decrypted first, before saving to MongoDB collection

# https://www.dlitz.net/software/pycrypto/api/current/
bs = Blowfish.block_size
key = b'An arbitrarily long key'
iv = Random.new().read(bs)
cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
plaintext = b'docendo discimus '
plen = bs - divmod(len(plaintext),bs)[1]
padding = [plen]*plen
padding = pack('b'*plen, *padding)
msg = iv + cipher.encrypt(plaintext + padding)

msg.decode('cp1252') # update collection with this

# retrieve text from connection and use .encode('cp1252') on it

decry_msg = cipher.decrypt(msg)[len(padding)+1:-len(padding)-1]
# if the conversion from Mongos saved text to the original encrypted text works
# it shouldn't be much of a problem! If...!

# repr(msg).replace('\\', '')
# collection.update({'_id': uid}, {"$set": {'body': repr(decodedmsg)}})
# collection.update({'_id': uid}, {"$set": {'body': repr(msg).replace('\\', '#')}})

#eval("'%s'" % myStringVar.get())
# eval("'%s'" % '\\x20\\x01\\x21') # this works but isn't considered very safe
# it happens in RAM
# str(collection.find_one()['body'].replace('#','\\')).strip("'")


