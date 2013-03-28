about this program

overall this notesapp app is working. But it has some glitches and the codebase 
is not particulary clean, neither (for it's quite small size) clear. 

which features might be of interest for anyone looking into the code?

Perhaps:
* the encryption of textfile and putting them into a MongoDB collection; and how
the program tests if a note was decrypted successfully (the encryption password is 
only saved into the RAM, not the filesystem or DB)
	- Note: saving encrypted notes to the filesystem is overall much more reliable,
	it can happen that a encrypted note saved on MongoDB is suddently corrupted and 
	so could not be accessed anymore! But it did not happen often.
* the style modification possibilities (even though I didn't polish it much)
* how settings are saved and applied (although this was done better in Theodoratranscode!)
* how to use a MongoDB database for a notes application

Note: instead of uploading installable files to the repository, I will just upload
the program as Anjuta project, because I think the code would need a bit more love, 
before this application could be of use for anyone.  

If anyone ever forks it: make sure to never upload a settings.cfg file with the 
connection information of your MongoDB provider account! The password would be in
cleartext in the settings file! 
One of the TODO's would be to hash the password and accountname. 

Currently I do not have any plans on developing this notes application any further.
