from ultralytics import YOLO

model = YOLO(
    "models/plant_disease.pt"
)

def detect_disease(image_path):

    results = model.predict(
        image_path
    )

    return results