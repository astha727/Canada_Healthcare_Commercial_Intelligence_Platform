condition_therapy_mapping = {
    "Diabetes mellitus (types combined), excluding gestational diabetes": "Antidiabetic",
    "Hypertension": "Antihypertensive",
    "Ischemic heart disease": "Cardiovascular",
    "Acute myocardial infarction": "Cardiovascular",
    "Heart failure": "Heart failure therapy",
    "Stroke": "Antithrombotic / secondary prevention",
    "Asthma": "Respiratory",
    "Chronic obstructive pulmonary disease": "Respiratory",
    "Osteoarthritis": "Analgesic / anti-inflammatory",
    "Osteoporosis": "Bone health",
    "Rheumatoid arthritis": "Immunomodulatory / anti-inflammatory",
    "Multiple sclerosis": "Disease-modifying therapy",
    "Parkinsonism, including Parkinson disease": "Parkinson's therapy",
    "Epilepsy": "Antiepileptic",
    "Dementia, including Alzheimer disease": "Cognitive disorder therapy",
    "Schizophrenia": "Antipsychotic"
}

import pandas as pd
from pathlib import Path



project_root = Path(__file__).resolve().parents[2]

drug_path = (
    project_root
    / "Data"
    / "processed"
    / "drug_product_master.csv"
)

drug_products = pd.read_csv(
    drug_path,
    dtype={
        "Product_ID": "string",
        "DRUG_CODE": "string",
        "DIN": "string",
        "AI_Group_No": "string"
    }
)


diagnosis_path = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_patient_diagnoses.csv"
)

diagnoses = pd.read_csv(diagnosis_path)


diagnosis_conditions = set(
    diagnoses["Condition"].unique()
)

mapping_conditions = set(
    condition_therapy_mapping.keys()
)


print("Diagnosis conditions:", len(diagnosis_conditions))
print("Mapped conditions:", len(mapping_conditions))

print("\nMissing from mapping:")
print(diagnosis_conditions - mapping_conditions)

print("\nMapping conditions not in diagnoses:")
print(mapping_conditions - diagnosis_conditions)





therapy_keywords = {
    "Antidiabetic": ["METFORMIN", "INSULIN", "GLIPIZIDE", "GLYBURIDE"],
    "Antihypertensive": ["LISINOPRIL", "LOSARTAN", "AMLODIPINE"],
    "Cardiovascular": ["ATORVASTATIN", "ROSUVASTATIN", "CLOPIDOGREL"],
    "Heart failure therapy": ["FUROSEMIDE", "CARVEDILOL", "SPIRONOLACTONE"],
    "Antithrombotic / secondary prevention": ["ASPIRIN", "CLOPIDOGREL", "WARFARIN"],
    "Respiratory": ["SALBUTAMOL", "BUDESONIDE", "FORMOTEROL"],
    "Analgesic / anti-inflammatory": ["NAPROXEN", "DICLOFENAC", "IBUPROFEN"],
    "Bone health": ["ALENDRONATE", "RISEDRONATE", "CALCITONIN"],
    "Immunomodulatory / anti-inflammatory": ["METHOTREXATE", "LEFLUNOMIDE"],
    "Disease-modifying therapy": ["INTERFERON", "GLATIRAMER"],
    "Parkinson's therapy": ["LEVODOPA", "CARBIDOPA", "PRAMIPEXOLE"],
    "Antiepileptic": ["LEVETIRACETAM", "VALPROATE", "CARBAMAZEPINE"],
    "Cognitive disorder therapy": ["DONEPEZIL", "RIVASTIGMINE", "MEMANTINE"],
    "Antipsychotic": ["RISPERIDONE", "OLANZAPINE", "QUETIAPINE"]
}


selected_products = {
    "Antidiabetic": [
        "11727",   # Glyburide
        "62536",   # Metformin
        "74296"    # Metformin
    ],

    "Antihypertensive": [
        "75765",   # Amlodipine
        "77062",   # Lisinopril
        "79542"    # Losartan
    ],

    "Cardiovascular": [
        "73770",   # Clopidogrel
        "78058",   # Atorvastatin
        "82362"    # Rosuvastatin
    ],

    "Heart failure therapy": [
        "2333",    # Furosemide
        "5646",    # Spironolactone
        "70034"    # Carvedilol
    ],

    "Antithrombotic / secondary prevention": [
        "19474",   # Aspirin
        "61080",   # Aspirin 81MG
        "66470"    # Warfarin
    ],

    "Respiratory": [
        "13550",   # Salbutamol
        "49895",   # Budesonide
        "69769"    # Salbutamol
    ],

    "Analgesic / anti-inflammatory": [
        "4980",    # Naproxen
        "5432",    # Ibuprofen
        "5917"     # Ibuprofen 600MG
    ],

    "Bone health": [
        "73098",   # Alendronate
        "78367"    # Risedronate
    ],

    "Immunomodulatory / anti-inflammatory": [
        "19681",   # Methotrexate injection
        "44161",   # Methotrexate
        "74173"    # Leflunomide
    ],

    "Disease-modifying therapy": [
        "103009"   # Glatiramer acetate
    ],

    "Parkinson's therapy": [
        "68471",   # Levodopa/carbidopa
        "77772"    # Pramipexole
    ],

    "Antiepileptic": [
        "75964",   # Levetiracetam
        "9242"     # Carbamazepine
    ],

    "Cognitive disorder therapy": [
        "80779",   # Donepezil
        "80653",   # Memantine
        "82234"    # Rivastigmine
    ],

    "Antipsychotic": [
        "73690",   # Risperidone
        "76239"    # Olanzapine
    ]
}

for therapy_class, product_codes in selected_products.items():

    matches = drug_products[
        drug_products["DRUG_CODE"].isin(product_codes)
    ]

    print(f"\n{therapy_class}")
    print("Selected:", len(matches))

    print(
        matches[
            [
                "Product_ID",
                "DRUG_CODE",
                "DIN",
                "Brand_Name",
                "AI_Group_No"
            ]
        ].to_string(index=False)
    )


mapping_rows = []

for therapy_class, product_ids in selected_products.items():

    for product_code in product_ids:

        mapping_rows.append({
            "Therapy_Class": therapy_class,
            "Product_ID": f"PROD_{product_code}"
        })


therapy_product_mapping = pd.DataFrame(mapping_rows)


therapy_product_mapping = therapy_product_mapping.merge(
    drug_products[
        [
            "Product_ID",
            "DIN",
            "Brand_Name",
            "AI_Group_No"
        ]
    ],
    on="Product_ID",
    how="left",
    validate="many_to_one"
)


print("Therapy-product mapping:", therapy_product_mapping.shape)
print("Missing DIN:", therapy_product_mapping["DIN"].isna().sum())
print("Unique Product_ID:", therapy_product_mapping["Product_ID"].nunique())
print("Duplicate Product_ID rows:", therapy_product_mapping["Product_ID"].duplicated().sum())


therapy_product_mapping.to_csv(
    project_root
    / "Data"
    / "processed"
    / "therapy_product_mapping.csv",
    index=False
)


print("Exported: Data/processed/therapy_product_mapping.csv")