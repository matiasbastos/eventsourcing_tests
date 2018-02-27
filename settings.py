import os

# Cipher key (random bytes encoded with Base64).
cipher_key = '+NNE1++Jb0kTIwpo9qMDv9LHJy39USmp0M7+vEkeWf8='
# os.environ['CIPHER_KEY'] = cipher_key

# SQLAlchemy-style database connection string. 
os.environ['DB_URI'] = 'mysql://root:password@127.0.0.1/eventsourcing'
