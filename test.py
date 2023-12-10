#test file to understand how the rsa module works

import rsa

message = "CONTROL:quit"

# Generate RSA key pair
(public_key, private_key) = rsa.newkeys(512)

# encrypt the message
encrypted_message = rsa.encrypt(message.encode(), public_key)

# decrypt the message
decrypted_message = rsa.decrypt(encrypted_message, private_key).decode()
decrypted_message_header = decrypted_message.split(':')[0]
decrypted_message_content = decrypted_message.split(':')[1]

# print the original message, the encrypted message and the decrypted message
print(f"Original message: {message}")
print(f"Encrypted message: {encrypted_message}")
print(f"Decrypted message: {decrypted_message}")
print(f"Decrypted message header: {decrypted_message_header}")
print(f"Decrypted message content: {decrypted_message_content}")





