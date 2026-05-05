import cv2
import numpy as np
import sys
import types
from pathlib import Path


def _prepare_matplotlib_for_mediapipe() -> None:
    try:
        import matplotlib.pyplot  # noqa: F401
        return
    except Exception as import_error:
        if "Application Control policy has blocked this file" not in str(import_error):
            raise import_error

    matplotlib_stub = types.ModuleType("matplotlib")
    pyplot_stub = types.ModuleType("matplotlib.pyplot")

    def _unsupported(*_args, **_kwargs):
        raise RuntimeError("matplotlib plotting is unavailable on this machine")

    pyplot_stub.figure = _unsupported
    pyplot_stub.imshow = _unsupported
    pyplot_stub.show = _unsupported
    pyplot_stub.subplot = _unsupported
    pyplot_stub.title = _unsupported
    pyplot_stub.axis = _unsupported
    pyplot_stub.gca = _unsupported

    matplotlib_stub.pyplot = pyplot_stub
    sys.modules["matplotlib"] = matplotlib_stub
    sys.modules["matplotlib.pyplot"] = pyplot_stub


_prepare_matplotlib_for_mediapipe()
from mediapipe.python.solutions.pose import Pose, PoseLandmark
from mediapipe.python.solutions.hands import Hands




def extract_pose(video_path: str, output_path: str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    pose = Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    hands = Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        pose_result = pose.process(rgb)
        hands_result = hands.process(rgb)

        joints = []

        #BODY (upper body only)
        if pose_result.pose_landmarks:
            lm = pose_result.pose_landmarks.landmark

            def p(idx):
                return [lm[idx].x, lm[idx].y, lm[idx].z]

            # MediaPipe pose indices
            joints.extend([
                p(PoseLandmark.LEFT_SHOULDER),
                p(PoseLandmark.LEFT_ELBOW),
                p(PoseLandmark.LEFT_WRIST),
                p(PoseLandmark.RIGHT_SHOULDER),
                p(PoseLandmark.RIGHT_ELBOW),
                p(PoseLandmark.RIGHT_WRIST),
            ])
        else:
            joints.extend([[0, 0, 0]] * 6)

        # HANDS
        hand_data = {
            "Left": [[0, 0, 0]] * 21,
            "Right": [[0, 0, 0]] * 21,
        }

        if hands_result.multi_hand_landmarks:
            for hand_lms, handedness in zip(
                hands_result.multi_hand_landmarks,
                hands_result.multi_handedness
            ):
                label = handedness.classification[0].label  # "Left" / "Right"
                coords = [
                    [lm.x, lm.y, lm.z]
                    for lm in hand_lms.landmark
                ]
                hand_data[label] = coords

        joints.extend(hand_data["Left"])
        joints.extend(hand_data["Right"])

        frames.append(joints)

    cap.release()

    pose_array = np.array(frames, dtype=np.float32)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, pose_array)

    print(f"Saved pose: {pose_array.shape} → {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_pose.py <input.mp4> <output.npy>")
        sys.exit(1)

    extract_pose(sys.argv[1], sys.argv[2])
