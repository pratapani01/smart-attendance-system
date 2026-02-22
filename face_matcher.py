import os
from deepface import DeepFace

DATASET_PATH = "dataset/students"

def find_student(image_path):
    try:
        # Compare image with dataset
        result = DeepFace.find(
            img_path=image_path,
            db_path=DATASET_PATH,
            enforce_detection=False,
            detector_backend="opencv"
        )

        if len(result[0]) > 0:
            identity_path = result[0].iloc[0]['identity']

            # Extract student name from folder
            folder = os.path.basename(os.path.dirname(identity_path))
            roll, name = folder.split("_",1)

            return f"{name} ({roll})"

    except Exception as e:
        print(e)

    return None
