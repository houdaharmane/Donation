import mysql.connector

def check_donation(user_id, donation_amount):
    myconn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="estsb",
        database="donation"
    )

    cursor = myconn.cursor()

    query = "SELECT * FROM donations WHERE user_id = %s AND donation_amount = %s"
    cursor.execute(query, (user_id, donation_amount))

    result = cursor.fetchall()

    cursor.close()
    myconn.close()

    return len(result) > 0  # Retourne True si le don existe, False sinon
