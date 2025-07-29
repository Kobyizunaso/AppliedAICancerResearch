from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
import io
import base64
from datetime import datetime
import os

# Data analysis imports
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test

# Visualization imports
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variable to store current dataset
current_dataset = None
dataset_info = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global current_dataset, dataset_info
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read the file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({'error': 'Unsupported file format. Please use CSV or Excel files.'}), 400
        
        current_dataset = df
        
        # Generate dataset info
        dataset_info = {
            'filename': file.filename,
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'sample_data': df.head().to_dict('records'),
            'uploaded_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'message': 'File uploaded successfully',
            'dataset_info': dataset_info
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/load_sample/<dataset_name>')
def load_sample_dataset(dataset_name):
    global current_dataset, dataset_info
    
    try:
        dataset_path = f'sample_data/{dataset_name}.csv'
        if not os.path.exists(dataset_path):
            return jsonify({'error': 'Sample dataset not found'}), 404
        
        df = pd.read_csv(dataset_path)
        current_dataset = df
        
        dataset_info = {
            'filename': f'{dataset_name}.csv',
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'sample_data': df.head().to_dict('records'),
            'loaded_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'message': f'Sample dataset {dataset_name} loaded successfully',
            'dataset_info': dataset_info
        })
    
    except Exception as e:
        return jsonify({'error': f'Error loading sample dataset: {str(e)}'}), 500

@app.route('/api/dataset_info')
def get_dataset_info():
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    return jsonify(dataset_info)

@app.route('/api/visualizations/correlation_heatmap')
def correlation_heatmap():
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    try:
        # Select only numeric columns
        numeric_cols = current_dataset.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return jsonify({'error': 'Need at least 2 numeric columns for correlation'}), 400
        
        corr_matrix = current_dataset[numeric_cols].corr()
        
        # Create Plotly heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix.round(3).values,
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title='Correlation Heatmap',
            xaxis_title='Features',
            yaxis_title='Features',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return jsonify({'plot': fig.to_json()})
    
    except Exception as e:
        return jsonify({'error': f'Error creating correlation heatmap: {str(e)}'}), 500

@app.route('/api/visualizations/survival_curve')
def survival_curve():
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    try:
        # Look for time and event columns
        time_col = None
        event_col = None
        
        for col in current_dataset.columns:
            if any(keyword in col.lower() for keyword in ['time', 'duration', 'survival', 'days', 'months']):
                time_col = col
            elif any(keyword in col.lower() for keyword in ['event', 'death', 'censored', 'status', 'outcome']):
                event_col = col
        
        if time_col is None or event_col is None:
            return jsonify({'error': 'Could not find time and event columns for survival analysis'}), 400
        
        # Prepare data
        df_survival = current_dataset[[time_col, event_col]].dropna()
        
        # Kaplan-Meier estimation
        kmf = KaplanMeierFitter()
        kmf.fit(df_survival[time_col], df_survival[event_col])
        
        # Create survival curve
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=kmf.timeline,
            y=kmf.survival_function_.iloc[:, 0],
            mode='lines',
            name='Survival Probability',
            line=dict(color='#1f77b4', width=3)
        ))
        
        # Add confidence intervals
        fig.add_trace(go.Scatter(
            x=kmf.timeline,
            y=kmf.confidence_interval_.iloc[:, 0],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_trace(go.Scatter(
            x=kmf.timeline,
            y=kmf.confidence_interval_.iloc[:, 1],
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(31, 119, 180, 0.2)',
            line=dict(width=0),
            name='95% Confidence Interval',
            hoverinfo='skip'
        ))
        
        fig.update_layout(
            title=f'Kaplan-Meier Survival Curve',
            xaxis_title=f'Time ({time_col})',
            yaxis_title='Survival Probability',
            plot_bgcolor='white',
            paper_bgcolor='white',
            yaxis=dict(range=[0, 1])
        )
        
        return jsonify({'plot': fig.to_json()})
    
    except Exception as e:
        return jsonify({'error': f'Error creating survival curve: {str(e)}'}), 500

@app.route('/api/visualizations/outcome_distribution')
def outcome_distribution():
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    try:
        # Look for treatment and outcome columns
        treatment_col = None
        outcome_col = None
        
        for col in current_dataset.columns:
            if any(keyword in col.lower() for keyword in ['treatment', 'therapy', 'drug', 'intervention']):
                treatment_col = col
            elif any(keyword in col.lower() for keyword in ['outcome', 'response', 'result', 'status']):
                outcome_col = col
        
        if treatment_col is None or outcome_col is None:
            return jsonify({'error': 'Could not find treatment and outcome columns'}), 400
        
        # Create grouped bar chart
        df_clean = current_dataset[[treatment_col, outcome_col]].dropna()
        
        # Calculate cross-tabulation
        crosstab = pd.crosstab(df_clean[treatment_col], df_clean[outcome_col])
        
        fig = go.Figure()
        
        for outcome in crosstab.columns:
            fig.add_trace(go.Bar(
                name=str(outcome),
                x=crosstab.index,
                y=crosstab[outcome]
            ))
        
        fig.update_layout(
            title=f'Outcome Distribution by {treatment_col}',
            xaxis_title=treatment_col,
            yaxis_title='Count',
            barmode='group',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return jsonify({'plot': fig.to_json()})
    
    except Exception as e:
        return jsonify({'error': f'Error creating outcome distribution: {str(e)}'}), 500

@app.route('/api/ml/predict', methods=['POST'])
def run_ml_model():
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    try:
        data = request.json
        model_type = data.get('model_type', 'logistic_regression')
        target_column = data.get('target_column')
        feature_columns = data.get('feature_columns', [])
        
        if not target_column or target_column not in current_dataset.columns:
            return jsonify({'error': 'Invalid target column'}), 400
        
        # Prepare data
        df = current_dataset.copy()
        
        # If no features specified, use all numeric columns except target
        if not feature_columns:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            feature_columns = [col for col in numeric_cols if col != target_column]
        
        if len(feature_columns) == 0:
            return jsonify({'error': 'No valid feature columns found'}), 400
        
        # Handle missing values
        df = df[feature_columns + [target_column]].dropna()
        
        if len(df) < 10:
            return jsonify({'error': 'Not enough data points for training (minimum 10 required)'}), 400
        
        X = df[feature_columns]
        y = df[target_column]
        
        # Encode categorical target if necessary
        le = None
        if y.dtype == 'object':
            le = LabelEncoder()
            y = le.fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        if model_type == 'logistic_regression':
            model = LogisticRegression(random_state=42)
        elif model_type == 'decision_tree':
            model = DecisionTreeClassifier(random_state=42)
        elif model_type == 'random_forest':
            model = RandomForestClassifier(random_state=42, n_estimators=100)
        else:
            return jsonify({'error': 'Unsupported model type'}), 400
        
        model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test_scaled)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        
        # Get feature importance (if available)
        feature_importance = None
        if hasattr(model, 'feature_importances_'):
            feature_importance = dict(zip(feature_columns, model.feature_importances_))
        elif hasattr(model, 'coef_'):
            feature_importance = dict(zip(feature_columns, abs(model.coef_[0])))
        
        # Generate confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Decode predictions if target was encoded
        if le is not None:
            y_test_decoded = le.inverse_transform(y_test)
            y_pred_decoded = le.inverse_transform(y_pred)
            unique_labels = le.classes_
        else:
            y_test_decoded = y_test
            y_pred_decoded = y_pred
            unique_labels = np.unique(np.concatenate([y_test, y_pred]))
        
        return jsonify({
            'model_type': model_type,
            'accuracy': float(accuracy),
            'feature_importance': feature_importance,
            'confusion_matrix': cm.tolist(),
            'unique_labels': unique_labels.tolist(),
            'test_size': len(y_test),
            'predictions_sample': {
                'actual': y_test_decoded[:10].tolist(),
                'predicted': y_pred_decoded[:10].tolist()
            }
        })
    
    except Exception as e:
        return jsonify({'error': f'Error running ML model: {str(e)}'}), 500

@app.route('/api/analysis/summary')
def generate_summary():
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    try:
        df = current_dataset
        
        # Basic statistics
        summary = {
            'dataset_overview': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
                'categorical_columns': len(df.select_dtypes(include=['object']).columns),
                'missing_data_percentage': round((df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2)
            },
            'data_quality': {
                'complete_rows': len(df.dropna()),
                'duplicate_rows': df.duplicated().sum(),
                'columns_with_missing_data': df.columns[df.isnull().any()].tolist()
            }
        }
        
        # Generate insights
        insights = []
        
        # Missing data insight
        if summary['dataset_overview']['missing_data_percentage'] > 5:
            insights.append(f"High missing data detected ({summary['dataset_overview']['missing_data_percentage']}%). Consider data cleaning strategies.")
        
        # Duplicate data insight
        if summary['data_quality']['duplicate_rows'] > 0:
            insights.append(f"Found {summary['data_quality']['duplicate_rows']} duplicate rows that may need attention.")
        
        # Column type insights
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # Check for potential outliers
            for col in numeric_cols[:3]:  # Check first 3 numeric columns
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))]
                if len(outliers) > 0:
                    insights.append(f"Column '{col}' has {len(outliers)} potential outliers.")
        
        # Correlation insights
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = abs(corr_matrix.iloc[i, j])
                    if corr_val > 0.8 and not pd.isna(corr_val):
                        high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
            
            if high_corr_pairs:
                insights.append(f"High correlations found between: {', '.join([f'{pair[0]}-{pair[1]} ({pair[2]:.2f})' for pair in high_corr_pairs[:3]])}")
        
        summary['insights'] = insights
        
        return jsonify(summary)
    
    except Exception as e:
        return jsonify({'error': f'Error generating summary: {str(e)}'}), 500

@app.route('/api/available_datasets')
def get_available_datasets():
    """Get list of available sample datasets"""
    sample_datasets = [
        {
            'name': 'breast_cancer_survival',
            'description': 'Breast cancer patient survival data with treatment outcomes',
            'features': ['Age', 'Tumor Size', 'Treatment Type', 'Survival Time', 'Status']
        },
        {
            'name': 'lung_cancer_treatment',
            'description': 'Lung cancer treatment response data',
            'features': ['Patient ID', 'Age', 'Stage', 'Treatment', 'Response', 'Progression Free Survival']
        }
    ]
    
    return jsonify({'datasets': sample_datasets})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)