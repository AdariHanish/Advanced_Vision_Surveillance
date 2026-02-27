import mysql.connector
import pickle
import datetime


def connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",
        database="surveillance"
    )


def save_alert(alert_type, image_path):
    conn = connect()
    cursor = conn.cursor()

    query = """
        INSERT INTO alerts (type, timestamp, image_path)
        VALUES (%s, %s, %s)
    """

    cursor.execute(query, (alert_type, datetime.datetime.now(), image_path))
    conn.commit()

    cursor.close()
    conn.close()


def save_face(face_id, name, embedding):
    conn = connect()
    cursor = conn.cursor()

    emb = pickle.dumps(embedding)

    query = """
        INSERT INTO known_faces (id, name, embedding)
        VALUES (%s, %s, %s)
    """

    cursor.execute(query, (face_id, name, emb))
    conn.commit()

    cursor.close()
    conn.close()


def get_faces():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, embedding FROM known_faces")
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


def log_event(face_id, name, event_type):
    conn = connect()
    cursor = conn.cursor()

    query = """
        INSERT INTO logs (id, name, type, timestamp)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (face_id, name, event_type, datetime.datetime.now()))
    conn.commit()

    cursor.close()
    conn.close()