import bcrypt

def hash_pwd(pwd):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd.encode('utf-8'), salt)
    return hashed.decode('utf-8')

plain = input('输入管理员密码：')
res = hash_pwd(plain)
print("明文：", plain)
print("bcrypt密文：", res)