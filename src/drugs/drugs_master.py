import pandas as pd
from pathlib import Path


# PROJECT PATHS

project_root = Path(__file__).resolve().parents[2]

drug_path = project_root / "Data" / "raw" / "drug.txt"
output_path = project_root / "Data" / "processed" / "drug_product_master.csv"


# SOURCE COLUMNS

drug_columns = [
    "DRUG_CODE",
    "PRODUCT_CATEGORIZATION",
    "CLASS",
    "DRUG_IDENTIFICATION_NUMBER",
    "BRAND_NAME",
    "DESCRIPTOR",
    "PEDIATRIC_FLAG",
    "ACCESSION_NUMBER",
    "NUMBER_OF_AIS",
    "LAST_UPDATE_DATE",
    "AI_GROUP_NO",
    "CLASS_F",
    "BRAND_NAME_F",
    "DESCRIPTOR_F"
]


# LOAD DPD PRODUCT DATA

drugs = pd.read_csv(
    drug_path,
    header=None,
    names=drug_columns,
    dtype={
        "DRUG_CODE": "string",
        "DRUG_IDENTIFICATION_NUMBER": "string",
        "AI_GROUP_NO": "string"
    }
)


# FILTER TO HUMAN PRODUCTS

human_drugs = drugs[
    drugs["CLASS"] == "Human"
].copy()


# CREATE INTERNAL PRODUCT ID

human_drugs["Product_ID"] = (
    "PROD_" +
    human_drugs["DRUG_CODE"]
)


# SELECT PLATFORM FIELDS

drug_product_master = human_drugs[
    [
        "Product_ID",
        "DRUG_CODE",
        "DRUG_IDENTIFICATION_NUMBER",
        "BRAND_NAME",
        "DESCRIPTOR",
        "PRODUCT_CATEGORIZATION",
        "AI_GROUP_NO",
        "PEDIATRIC_FLAG",
        "LAST_UPDATE_DATE"
    ]
].copy()


# RENAME SOURCE FIELDS

drug_product_master = drug_product_master.rename(
    columns={
        "DRUG_IDENTIFICATION_NUMBER": "DIN",
        "BRAND_NAME": "Brand_Name",
        "DESCRIPTOR": "Descriptor",
        "PRODUCT_CATEGORIZATION": "Product_Categorization",
        "AI_GROUP_NO": "AI_Group_No",
        "PEDIATRIC_FLAG": "Pediatric_Flag",
        "LAST_UPDATE_DATE": "Last_Update_Date"
    }
)


# QA

print("Drug product master:", drug_product_master.shape)
print(
    "Unique Product_ID:",
    drug_product_master["Product_ID"].nunique()
)
print(
    "Unique DIN:",
    drug_product_master["DIN"].nunique()
)
print(
    "Missing Product_ID:",
    drug_product_master["Product_ID"].isna().sum()
)
print(
    "Missing DIN:",
    drug_product_master["DIN"].isna().sum()
)


# EXPORT

drug_product_master.to_csv(
    output_path,
    index=False
)

print("Exported:", output_path)