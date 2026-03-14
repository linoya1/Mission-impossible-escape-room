import rsa_cpp

# פרמטרי ה-RSA של חדר 4
n, e, d = 3233, 17, 2753

# נצפין את התו 'A' (65) ואז נפענח
msg = 65                          # 'A'
cipher = [pow(msg, e, n)]         # צפוי: [2790]
dec = rsa_cpp.rsa_decrypt_bytes(cipher, d, n)

print("cipher:", cipher, "| decrypted:", dec)  # צריך להדפיס: cipher: [2790] | decrypted: [65]
