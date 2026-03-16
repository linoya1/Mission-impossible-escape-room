import rsa_cpp

# RSA parameters for Room 4
n, e, d = 3233, 17, 2753

# Encrypt the character 'A' (65) and then decrypt it
msg = 65                          # 'A'
cipher = [pow(msg, e, n)]         # expected: [2790]
dec = rsa_cpp.rsa_decrypt_bytes(cipher, d, n)

print("cipher:", cipher, "| decrypted:", dec)  # expected: cipher: [2790] | decrypted: [65]
