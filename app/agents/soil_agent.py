from app.loaders.excel_loader import read_excel

def analyze_soil(file_path):

    df = read_excel(file_path)

    return {
        "ph": df["ph"].mean(),
        "nitrogen": df["nitrogen"].mean(),
        "phosphorus": df["phosphorus"].mean(),
        "potassium": df["potassium"].mean()
    }