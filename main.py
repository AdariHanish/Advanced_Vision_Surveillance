import subprocess
import time
import cv2
import os
import datetime

# ===============================
# CONFIG
# ===============================

WEAPON_CLASSES = [
    "Rifle",
    "knife",
    "pistol",
    "shot-gun",
    "submachine-gun"
]

ABSENCE_THRESHOLD = 10
ALERT_COOLDOWN = 10
FACE_COOLDOWN = 10

last_alert_time = {}
last_face_save_time = {}

# ===============================
# MYSQL SERVICE AUTO START
# ===============================

def start_mysql_service():
    try:
        check = subprocess.run(
            ["sc", "query", "MySQL96"],
            capture_output=True,
            text=True,
            shell=True
        )

        if "RUNNING" in check.stdout:
            print("MySQL96 is already running.")
        else:
            subprocess.run(["net", "start", "MySQL96"], shell=True)
            time.sleep(2)
    except:
        pass

start_mysql_service()

# ===============================
# IMPORT MODULES
# ===============================

from detection_module import detect_objects, detect_weapons
from face_module import recognize_face, register_face, delete_face
from suspicious_module import check_loiter, check_running
from database import log_event, save_alert
from alert_module import send_email_alert

# ===============================
# SNAPSHOT STRUCTURE
# ===============================

base_snapshot_path = "snapshots"

faces_base_path = os.path.join(base_snapshot_path, "faces")
os.makedirs(os.path.join(faces_base_path, "known"), exist_ok=True)
os.makedirs(os.path.join(faces_base_path, "unknown"), exist_ok=True)

weapons_base_path = os.path.join(base_snapshot_path, "weapons")
for weapon in WEAPON_CLASSES:
    os.makedirs(os.path.join(weapons_base_path, weapon, "known"), exist_ok=True)
    os.makedirs(os.path.join(weapons_base_path, weapon, "unknown"), exist_ok=True)

# ===============================
# CAMERA SETUP (FULL HD + STABLE)
# ===============================

def init_camera():
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cam.set(cv2.CAP_PROP_FPS, 30)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    return cam

cap = init_camera()

if not cap.isOpened():
    print("Error: Cannot open camera")
    exit()

cv2.namedWindow("Advanced Vision Surveillance", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Advanced Vision Surveillance", 1280, 720)

previous_positions = {}
active_people = {}

prev_time = 0  # FPS tracker

print("\n===== Advanced Vision Surveillance System =====")
print("Press R to Register Face")
print("Press D to Delete Face")
print("Press Q to Quit\n")

# ===============================
# MAIN LOOP
# ===============================

while True:

    ret, frame = cap.read()
    if not ret:
        break

    current_time = datetime.datetime.now()
    timestamp_str = current_time.strftime("%Y%m%d_%H%M%S")
    now = time.time()

    # ================= FACE RECOGNITION =================
    face_id, face_name = recognize_face(frame)

    if face_id:
        cv2.putText(frame,
                    f"{face_name} ({face_id})",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 0, 0),
                    2)

        if face_id not in active_people:
            active_people[face_id] = current_time
            log_event(face_id, face_name, "ENTRY")
        else:
            active_people[face_id] = current_time

        # Face snapshot cooldown
        face_key = face_id if face_id != "UNKNOWN" else "UNKNOWN"

        if face_key not in last_face_save_time or \
           now - last_face_save_time[face_key] > FACE_COOLDOWN:

            last_face_save_time[face_key] = now

            folder = "known" if face_id != "UNKNOWN" else "unknown"

            face_snapshot_path = os.path.join(
                faces_base_path,
                folder,
                f"{face_key}_{timestamp_str}.jpg"
            )

            cv2.imwrite(face_snapshot_path, frame)

    # ================= OBJECT DETECTION =================
    object_results = detect_objects(frame)
    detected_objects = []
    person_index = 1

    for r in object_results:
        for box in r.boxes:

            cls = int(box.cls[0])
            name = r.names[cls]
            conf = float(box.conf[0])

            if conf < 0.35:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            center = ((x1 + x2) // 2, (y1 + y2) // 2)

            detected_objects.append(f"{name} ({conf:.2f})")

            if name == "person":
                label = f"Person {person_index}"
                person_index += 1
                color = (0, 255, 0)

                person_id = f"{x1}_{y1}"

                if check_loiter(person_id):
                    cv2.putText(frame, "LOITERING",
                                (x1, y2 + 20),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (0, 0, 255), 2)

                if person_id in previous_positions:
                    if check_running(previous_positions[person_id], center):
                        cv2.putText(frame, "RUNNING",
                                    (x1, y2 + 40),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6, (0, 0, 255), 2)

                previous_positions[person_id] = center
            else:
                label = f"{name} {conf:.2f}"
                color = (255, 255, 0)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, color, 2)

    if detected_objects:
        print(f"[{current_time.strftime('%H:%M:%S')}] Objects:",
              ", ".join(detected_objects))

    # ================= WEAPON DETECTION =================
    weapons = detect_weapons(frame)

    for weapon_name, bbox in weapons:

        x1, y1, x2, y2 = bbox

        cv2.rectangle(frame, (x1, y1), (x2, y2),
                      (0, 0, 255), 3)
        cv2.putText(frame, weapon_name,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 0, 255),
                    2)

        if weapon_name in last_alert_time and \
           now - last_alert_time[weapon_name] < ALERT_COOLDOWN:
            continue

        last_alert_time[weapon_name] = now

        category = "known" if face_id and face_id != "UNKNOWN" else "unknown"
        person_info = face_name if face_id and face_id != "UNKNOWN" else "Unknown"

        save_folder = os.path.join(
            weapons_base_path,
            weapon_name,
            category
        )

        snapshot_path = os.path.join(
            save_folder,
            f"{weapon_name}_{timestamp_str}.jpg"
        )

        cv2.imwrite(snapshot_path, frame)
        save_alert("WEAPON DETECTED", snapshot_path)

        try:
            send_email_alert(
                "🚨 Weapon Detected!",
                f"Weapon: {weapon_name}\nPerson: {person_info}\nTime: {current_time}",
                snapshot_path
            )
        except:
            pass

    # ================= FPS DISPLAY =================
    new_time = time.time()
    fps = 1 / (new_time - prev_time) if prev_time != 0 else 0
    prev_time = new_time

    cv2.putText(frame, f"FPS: {int(fps)}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2)

    # ================= DISPLAY =================
    display_frame = cv2.resize(frame, (1280, 720))
    cv2.imshow("Advanced Vision Surveillance", display_frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('r'):
        register_face(cap)

    elif key == ord('d'):
        cap.release()
        delete_face()
        cap = init_camera()

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()