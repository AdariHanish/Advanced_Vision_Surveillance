from ultralytics import YOLO

# ==============================
# LOAD MODELS
# ==============================

# Fast object detection model
object_model = YOLO("yolov8m.pt")

# Your trained weapon model
weapon_model = YOLO("models/weapon_model.pt")

# Weapon classes ONLY
WEAPON_CLASSES = [
    "Rifle",
    "knife",
    "pistol",
    "shot-gun",
    "submachine-gun"
]

# ==============================
# OBJECT DETECTION
# ==============================

def detect_objects(frame):
    """
    Returns YOLO results for object detection
    IMPORTANT: No stream=True (causes missing boxes)
    """
    results = object_model(frame, conf=0.6, imgsz=1280, verbose=False)
    return results


# ==============================
# WEAPON DETECTION
# ==============================

def detect_weapons(frame):
    results = weapon_model(frame, conf=0.75, imgsz=1280, verbose=False)

    weapons = []

    for r in results:

        if r.boxes is None:
            continue

        for box in r.boxes:

            # ===== VERY IMPORTANT FIX =====
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)

            cls = int(box.cls[0].cpu().numpy())
            conf = float(box.conf[0].cpu().numpy())

            name = r.names[cls]

            if name in WEAPON_CLASSES and conf >= 0.75:
                weapons.append((name, (x1, y1, x2, y2)))

    return weapons