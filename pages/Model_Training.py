import streamlit as st
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import joblib
import os
import pandas as pd

from backend.ml_utils import read_data, get_embeddings, create_embeddings, split_train_test__data, get_score

# Ensure models directory exists
os.makedirs("models", exist_ok=True)

# Initialize session state
session_defaults = {
    'cleaned_data': None,
    'sentences_train': None,
    'sentences_test': None,
    'labels_train': None,
    'labels_test': None,
    'svm_classifier': None,
    'embeddings': None
}
for key, default_value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

st.title("🤖 Let's Build Our SVM Model")

# Create tabs
tab_titles = ['Data Preprocessing', 'Model Training', 'Model Evaluation', 'Save Model']
tabs = st.tabs(tab_titles)

# ---------------- Tab 1: Data Preprocessing ---------------- #
with tabs[0]:
    st.header('🧹 Data Preprocessing')
    st.write('Upload your CSV and generate sentence embeddings.')

    data = st.file_uploader("📂 Upload CSV file", type="csv")

    if st.button("🔄 Load Data", key="data"):
        if data is None:
            st.error("⚠️ Please upload a CSV file first.")
        else:
            with st.spinner('🔄 Processing data...'):
                our_data = read_data(data)
                if st.session_state['embeddings'] is None:
                    st.session_state['embeddings'] = get_embeddings()
                st.session_state['cleaned_data'] = create_embeddings(our_data, st.session_state['embeddings'])
            st.success('✅ Data loaded and embeddings created!')

# ---------------- Tab 2: Model Training ---------------- #
with tabs[1]:
    st.header('🛠️ Model Training')
    st.write('Train an SVM classifier with the embedded data.')

    if st.session_state['svm_classifier'] is not None:
        st.warning("⚠️ A model already exists. Retraining will overwrite it.")

    if st.button("📈 Train Model", key="model"):
        if (
            st.session_state['cleaned_data'] is None
            or isinstance(st.session_state['cleaned_data'], pd.DataFrame) and st.session_state['cleaned_data'].empty
        ):
            st.error("❌ Please preprocess the data first in Tab 1.")
        else:
            with st.spinner('⏳ Training model...'):
                st.session_state['sentences_train'], st.session_state['sentences_test'], \
                st.session_state['labels_train'], st.session_state['labels_test'] = split_train_test__data(
                    st.session_state['cleaned_data'])

                st.session_state['svm_classifier'] = make_pipeline(
                    StandardScaler(), SVC(class_weight='balanced')
                )
                st.session_state['svm_classifier'].fit(
                    st.session_state['sentences_train'],
                    st.session_state['labels_train']
                )
            st.success("✅ Model trained successfully!")

# ---------------- Tab 3: Model Evaluation ---------------- #
with tabs[2]:
    st.header('📊 Model Evaluation')
    st.write('Evaluate your model and try a sample prediction.')

    if st.button("📏 Evaluate Model", key="Evaluation"):
        if not st.session_state['svm_classifier']:
            st.error("❌ Please train the model first.")
        else:
            with st.spinner('🔍 Evaluating...'):
                accuracy_score = get_score(
                    st.session_state['svm_classifier'],
                    st.session_state['sentences_test'],
                    st.session_state['labels_test']
                )
                st.success(f"✅ Validation accuracy: {round(100 * accuracy_score, 2)}%")

    st.subheader("🔍 Try a Sample Prediction")
    text = st.text_input("✍️ Write a task description:")
    if text:
        st.write(f"Your text: *{text}*")
        if st.session_state['embeddings'] is None:
            st.session_state['embeddings'] = get_embeddings()
        query_result = st.session_state['embeddings'].embed_query(text)
        if not st.session_state['svm_classifier']:
            st.error("❌ Please train the model first.")
        else:
            result = st.session_state['svm_classifier'].predict([query_result])
            st.write("📌 **Module it belongs to:**", result[0])
            st.success("✅ Prediction complete!")

# ---------------- Tab 4: Save Model ---------------- #
with tabs[3]:
    st.header('💾 Save Model')
    st.write('Save your trained model based on the selected domain.')

    domain = st.selectbox(
        "📁 Project Domain",
        ["Game Development", "Web Development", "App Development", "Custom"]
    )

    # Determine model path
    if domain == "Game Development":
        model_path = "models/game_dev.pkl"
    elif domain in ["Web Development", "App Development"]:
        model_path = "models/web_dev.pkl"
    else:
        model_path = "models/modelsvm.pkl"

    if st.button("💾 Save Model", key="save"):
        if not st.session_state['svm_classifier']:
            st.error("❌ No model found. Please train the model first.")
        else:
            with st.spinner('💾 Saving model...'):
                joblib.dump(st.session_state['svm_classifier'], model_path)
            st.success(f"✅ Model saved successfully to `{model_path}`")

            # Offer download button
            with open(model_path, "rb") as file:
                st.download_button(
                    label="📥 Download Saved Model",
                    data=file,
                    file_name=model_path.split("/")[-1],
                    mime="application/octet-stream"
                )
