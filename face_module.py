import cv2
import numpy as np
import uuid
import insightface
import pickle
from database import save_face, get_faces, connect

# ===============================
# INSIGHTFACE INIT
# ===============================

app = insightface.app.FaceAnalysis()
app.prepare(ctx_id=0)

SIMILARITY_THRESHOLD = 0.65  # slightly higher for better accuracy

# ===============================
# LOAD KNOWN FACES (CACHE)
# ===============================

known_face_cache = []

def load_faces():
    global known_face_cache
    known_face_cache = []

    faces = get_faces()

    for face_id, name, db_embedding in faces:
        embedding = pickle.loads(db_embedding)

        # normalize embedding
        embedding = embedding / np.linalg.norm(embedding)

        known_face_cache.append((face_id, name, embedding))

# Load once at start
load_faces()

# ===============================
# FACE RECOGNITION
# ===============================

def recognize_face(frame):

    faces = app.get(frame)

    if not faces:
        return None, None

    for face in faces:
        embedding = face.embedding
        embedding = embedding / np.linalg.norm(embedding)

        best_match = None
        highest_similarity = 0

        for face_id, name, db_embedding in known_face_cache:
            similarity = np.dot(embedding, db_embedding)

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = (face_id, name)

        if highest_similarity > SIMILARITY_THRESHOLD:
            return best_match

    return "UNKNOWN", "Unknown Person"

# ===============================
# FACE REGISTRATION
# ===============================

def register_face(cap):

    print("\n--- FACE REGISTRATION MODE ---")
    name = input("Enter Name: ")

    print("Look at the camera and press SPACE to capture...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.putText(frame, "Press SPACE to Capture Face",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)

        cv2.imshow("Register Face", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # SPACE key

            faces = app.get(frame)

            if not faces:
                print("No face detected. Try again.")
                continue

            face = faces[0]
            embedding = face.embedding
            embedding = embedding / np.linalg.norm(embedding)

            face_id = str(uuid.uuid4())[:8]

            save_face(face_id, name, embedding)

            print(f"Face Registered Successfully with ID: {face_id}")

            # Reload cache after registration
            load_faces()

            break

        elif key == 27:  # ESC
            print("Registration Cancelled.")
            break

    cv2.destroyWindow("Register Face")

# ===============================
# DELETE FACE (DB SAFE)
# ===============================
def delete_face():

    from database import get_faces, connect

    faces = get_faces()

    if not faces:
        print("❌ No registered faces found.")
        return

    print("\n=== REGISTERED FACES ===")

    for index, (face_id, name, _) in enumerate(faces, start=1):
        print(f"{index}. {name} (ID: {face_id})")

    try:
        choice = int(input("\nSelect number to delete: "))

        if choice < 1 or choice > len(faces):
            print("❌ Invalid selection.")
            return

        selected_face_id = faces[choice - 1][0]
        selected_name = faces[choice - 1][1]

    except:
        print("❌ Invalid input.")
        return

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM known_faces WHERE id = %s", (selected_face_id,))
    conn.commit()

    cursor.close()
    conn.close()

    print(f"✅ {selected_name} (ID: {selected_face_id}) deleted successfully.")

    # Reload cache
    load_faces()