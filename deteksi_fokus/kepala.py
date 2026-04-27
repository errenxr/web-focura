import cv2
import numpy as np
import mediapipe as mp
import time
from collections import deque

# ====== MediaPipe Init ======
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# ====== Global State ======
nose_history = deque(maxlen=10)
movement_start_time = None
latest_result = None

# ====== Callback ======
def result_callback(result, output_image, timestamp_ms):
    global latest_result
    latest_result = result

# ====== Options ======
options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="face_landmarker.task"),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=result_callback,
    num_faces=1
)

# ====== Kamera ======
cap = cv2.VideoCapture(0)

# OPTIMASI RASPI
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 30)

# ====== Fungsi ======
def get_head_movement(nose_x, nose_y):
    global movement_start_time

    nose_history.append((nose_x, nose_y))

    if len(nose_history) < 10:
        return "STABLE", 0

    dx = max(p[0] for p in nose_history) - min(p[0] for p in nose_history)
    dy = max(p[1] for p in nose_history) - min(p[1] for p in nose_history)

    moving = dx > 20 or dy > 20  # lebih sensitif untuk Pi

    if moving:
        if movement_start_time is None:
            movement_start_time = time.time()
        duration = time.time() - movement_start_time
        return "MOVING", duration
    else:
        movement_start_time = None
        return "STABLE", 0

def get_eye_direction(landmarks, w):
    left_iris = landmarks[468]
    right_iris = landmarks[473]

    left_eye = landmarks[33]
    right_eye = landmarks[263]

    iris_x = (left_iris.x + right_iris.x) / 2 * w
    eye_center = (left_eye.x + right_eye.x) / 2 * w

    if iris_x < eye_center - 8:
        return "LEFT"
    elif iris_x > eye_center + 8:
        return "RIGHT"
    else:
        return "CENTER"

def is_looking_down(landmarks):
    nose = landmarks[1]
    left_eye = landmarks[33]
    right_eye = landmarks[263]

    eye_y = (left_eye.y + right_eye.y) / 2

    return nose.y > eye_y + 0.025

# ====== MAIN ======
with FaceLandmarker.create_from_options(options) as landmarker:

    timestamp = 0
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # ====== FRAME SKIP (PENTING) ======
        if frame_count % 2 == 0:
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        landmarker.detect_async(mp_image, timestamp)
        timestamp += 1

        # ====== PROSES HASIL ======
        if latest_result and latest_result.face_landmarks:
            landmarks = latest_result.face_landmarks[0]

            h, w, _ = frame.shape

            nose = landmarks[1]
            nose_x = int(nose.x * w)
            nose_y = int(nose.y * h)

            movement, duration = get_head_movement(nose_x, nose_y)
            eye_dir = get_eye_direction(landmarks, w)
            looking_down = is_looking_down(landmarks)

            # ====== LOGIKA FOKUS ======
            if movement == "MOVING" and duration >= 10:
                focus = "NOT FOCUSED"
                color = (0, 0, 255)

            elif looking_down:
                focus = "FOCUSED"
                color = (0, 255, 0)

            else:
                focus = "NOT FOCUSED"
                color = (0, 0, 255)

            # ====== DISPLAY ======
            cv2.putText(frame, f"Eye: {eye_dir}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)

            cv2.putText(frame, f"Move: {movement}", (10, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)

            cv2.putText(frame, f"Time: {duration:.1f}s", (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)

            cv2.putText(frame, f"Focus: {focus}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            cv2.circle(frame, (nose_x, nose_y), 3, (0,0,255), -1)

        cv2.imshow("Focus Detection (Raspi Optimized)", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
