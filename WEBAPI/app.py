from flask import Flask, jsonify, request
import pyodbc
import bcrypt
import secrets
import jwt
import random

app = Flask(__name__)

server = 'DESKTOP-SB4CB6T\\SQLEXPRESS' 
database = 'login' 
conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
cursor.execute('SELECT @@version;')
row = cursor.fetchone()
print(row[0])

@app.route('/api/girisyap', methods=['POST'])
def girisyap():

    data = request.json
    kullanici_adi = data['kullanici_adi']
    sifre = data['sifre']

    query = f"SELECT id, kullanıcı_adı, şifre FROM kullanıcılar WHERE kullanıcı_adı = '{kullanici_adi}'"
    cursor.execute(query)
    result = cursor.fetchone()

    if result is None:
        return jsonify({'message': 'Kullanıcı adı veya şifre yanlış!'})

    if not bcrypt.checkpw(sifre.encode('utf-8'), result[2].encode('utf-8')):
        return jsonify({'message': 'Kullanıcı adı veya şifre yanlış!'})

    token = jwt.encode({'kullanici_id': result[0], 'kullanici_adı': result[1]}, 'gizlianahtar')

    query = f"INSERT INTO tokenlar (kullanıcı_id, token) VALUES ({result[0]}, '{token}')"
    cursor.execute(query)
    conn.commit()

    return jsonify({'token': token})

@app.route('/api/kullanici_ekle', methods=['POST'])
def kullanici_ekle():
 
    data = request.json
    id = random.randint(1,1000)
    kullanici_adı = data['kullanici_adı']
    sifre = data['sifre']
    ad = data['ad']
    soyad = data['soyad']

    hashlenmis_sifre = bcrypt.hashpw(sifre.encode('utf-8'), bcrypt.gensalt())

    query = f"INSERT INTO kullanıcılar (id, kullanıcı_adı, şifre, ad, soyad) VALUES ({id}, '{kullanici_adı}', '{hashlenmis_sifre.decode('utf-8')}', '{ad}', '{soyad}')"

    cursor.execute(query)
    conn.commit()

    return jsonify({'message': 'Kullanıcı eklendi!'})


@app.route('/api/kullanıcıları_listele', methods=['GET'])
def kullanıcıları_listele():

    query = "SELECT * FROM kullanıcılar"

    cursor.execute(query)
    rows = cursor.fetchall()

    kullanıcılar = []
    for row in rows:
        kullanıcı = {
            'id': row[0],
            'kullanici_adı': row[1],
            'ad': row[3],
            'soyad': row[4]
        }
        kullanıcılar.append(kullanıcı)

    return jsonify(kullanıcılar)

@app.route('/api/kullanici_sil', methods=['POST'])
def kullanici_sil():

    data = request.json
    kullanici_adı = data['kullanici_adı']
    
    query = f"DELETE FROM tokenlar WHERE kullanıcı_id = (SELECT id FROM kullanıcılar WHERE kullanıcı_adı = '{kullanici_adı}')"
    cursor.execute(query)
    
    query = f"DELETE FROM kullanıcılar WHERE kullanıcı_adı = '{kullanici_adı}'"
    cursor.execute(query)
    conn.commit()

    return jsonify({'message': 'Kullanıcı silindi!'})


@app.route('/api/kullanici_guncelle', methods=['POST'])
def kullanici_guncelle():

    data = request.json
    kullanici_adi = data['kullanici_adı']
    yeni_kullanici_adi = data['yeni_kullanici_adi']
    yeni_ad = data['yeni_ad']
    yeni_soyad = data['yeni_soyad']

    query = f"UPDATE kullanıcılar SET kullanıcı_adı = '{yeni_kullanici_adi}' , ad = '{yeni_ad}', soyad = '{yeni_soyad}' WHERE kullanıcı_adı = '{kullanici_adi}'"

    cursor.execute(query)
    conn.commit()

    return jsonify({'message': 'Kullanıcı güncellendi!'})


def token_olustur(kullanici_adi, sifre):

    query = f"SELECT id, kullanıcı_adı, şifre FROM kullanıcılar WHERE kullanıcı_adı = '{kullanici_adi}'"
    cursor.execute(query)
    result = cursor.fetchone()

    if result is None or not bcrypt.checkpw(sifre.encode('utf-8'), result[2].encode('utf-8')):
        return None

    payload = {
        'kullanici_id': result[0],
        'kullanici_adı': result[1]
    }
    secret = secrets.token_urlsafe(32)  
    token = jwt.encode(payload, secret, algorithm='HS256')

    query = f"INSERT INTO tokenlar (kullanıcı_id, token, secret) VALUES ({result[0]}, '{token.decode('utf-8')}', '{secret}')"
    cursor.execute(query)
    conn.commit()
    return token.decode('utf-8')

if __name__ == '__main__':
    app.run(debug=True)




