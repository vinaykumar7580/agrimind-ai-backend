from app.ml.disease_detector import detect_disease

def disease_agent(image_path):

    result = detect_disease(image_path)

    return result