import streamlit as st
import pandas as pd
import os

# File path for the Base Table
BASE_TABLE_PATH = r"C:\Users\Administrator\Desktop\SMS Coding\Base table.xlsx"

# Cache base table to avoid reloading
@st.cache_data
def load_base_table():
    return pd.read_excel(BASE_TABLE_PATH)

# Cache uploaded data with deduplication
@st.cache_data(ttl=3600, persist=True)
def get_uploaded_data(key, file, base_table):
    df = pd.read_excel(file)
    table_rules = base_table[base_table['Table_name'] == key]
    column_map = dict(zip(table_rules['Column_name_in_source'], table_rules['Column_name_in_site']))
    df = df[list(column_map.keys())].rename(columns=column_map)
    dedup_col = {
        'Slab data': 'Slab ID 2',
        'Caster level 2': 'Slab ID 1',
        'EMS': 'Slab ID 3',
        'RHD Complete': 'Heat ID 4',
    }.get(key)
    if dedup_col:
        df = df.drop_duplicates(subset=[dedup_col])
    return df

st.set_page_config(page_title="SMS Data Upload", layout="wide")
st.title("SMS Data Uploader")

base_table = load_base_table()

tabs = st.tabs(["Slab data", "Caster level 2", "EMS", "RHD Complete"])

uploaded_data = {}

# Iterate over each tab
for i, table_name in enumerate(["Slab data", "Caster level 2", "EMS", "RHD Complete"]):
    with tabs[i]:
        st.subheader(f"Upload {table_name} file")
        file = st.file_uploader(f"Upload {table_name} Excel file", type=['xlsx'], key=table_name)
        if file:
            data = get_uploaded_data(table_name, file, base_table)
            uploaded_data[table_name] = data
            st.write("Preview:")
            st.dataframe(data.head())

st.write("Raw columns in uploaded file:", df.columns.tolist())
st.write("Expected columns:", list(column_map.keys()))

# Special logic for EMS tab (after loading all tabs)
if all(tbl in uploaded_data for tbl in ["EMS", "Caster level 2"]):
    ems_df = uploaded_data["EMS"]
    caster_df = uploaded_data["Caster level 2"]
    merged_df = ems_df.merge(
        caster_df[["Slab cut time 1", "Slab ID 1"]],
        how='left',
        left_on='Slab cut time 3',
        right_on='Slab cut time 1'
    )
    merged_df['Slab ID 1 from caster'] = merged_df['Slab ID 1']
    merged_df.drop(columns=['Slab cut time 1', 'Slab ID 1'], inplace=True)
    uploaded_data["EMS"] = merged_df

    with tabs[2]:
        st.subheader("EMS Table with Slab ID 1 Merged")
        st.dataframe(merged_df.head())
