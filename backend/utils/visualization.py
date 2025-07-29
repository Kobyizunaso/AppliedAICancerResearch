"""
Visualization utilities for cancer data analysis
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import json
import base64
from io import BytesIO

class CancerDataVisualizer:
    """
    Comprehensive visualization toolkit for cancer data analysis
    """
    
    def __init__(self, save_folder=None):
        self.save_folder = Path(save_folder) if save_folder else None
        if self.save_folder:
            self.save_folder.mkdir(parents=True, exist_ok=True)
        
        # Color schemes for different cancer types
        self.cancer_colors = {
            'breast': ['#FF69B4', '#FF1493', '#DC143C'],
            'lung': ['#87CEEB', '#4682B4', '#191970'],
            'colorectal': ['#FFA500', '#FF8C00', '#FF4500'],
            'general': ['#32CD32', '#228B22', '#006400']
        }
    
    def create_survival_curve(self, survival_data, title="Kaplan-Meier Survival Curve"):
        """
        Create interactive survival curve visualization
        """
        timeline = survival_data['timeline']
        survival_function = survival_data['survival_function']
        ci_lower = survival_data.get('confidence_interval_lower', [])
        ci_upper = survival_data.get('confidence_interval_upper', [])
        
        fig = go.Figure()
        
        # Main survival curve
        fig.add_trace(go.Scatter(
            x=timeline,
            y=survival_function,
            mode='lines',
            name='Survival Probability',
            line=dict(color='blue', width=3),
            hovertemplate='Time: %{x}<br>Survival: %{y:.3f}<extra></extra>'
        ))
        
        # Confidence interval
        if ci_lower and ci_upper:
            fig.add_trace(go.Scatter(
                x=timeline + timeline[::-1],
                y=ci_upper + ci_lower[::-1],
                fill='toself',
                fillcolor='rgba(0,100,80,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='95% Confidence Interval',
                showlegend=True
            ))
        
        # Median survival line
        median_survival = survival_data.get('median_survival')
        if median_survival:
            fig.add_vline(
                x=median_survival,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Median Survival: {median_survival:.1f} months"
            )
        
        fig.update_layout(
            title=title,
            xaxis_title="Time (months)",
            yaxis_title="Survival Probability",
            hovermode='x unified',
            template='plotly_white',
            width=800,
            height=500
        )
        
        return fig.to_json()
    
    def create_feature_importance_plot(self, feature_importance, title="Feature Importance"):
        """
        Create feature importance visualization
        """
        if not feature_importance:
            return None
        
        features, importances = zip(*feature_importance[:15])  # Top 15 features
        
        fig = go.Figure(go.Bar(
            x=list(importances),
            y=list(features),
            orientation='h',
            marker_color='lightblue',
            hovertemplate='%{y}: %{x:.3f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Importance Score",
            yaxis_title="Features",
            template='plotly_white',
            height=max(400, len(features) * 25),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig.to_json()
    
    def create_correlation_heatmap(self, df, title="Feature Correlation Heatmap"):
        """
        Create correlation heatmap for numeric features
        """
        # Select only numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return None
        
        # Calculate correlation matrix
        corr_matrix = numeric_df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            hovertemplate='%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            template='plotly_white',
            width=600,
            height=600
        )
        
        return fig.to_json()
    
    def create_distribution_plots(self, df, columns=None, cancer_type='general'):
        """
        Create distribution plots for specified columns
        """
        if columns is None:
            # Select numeric columns
            columns = df.select_dtypes(include=[np.number]).columns.tolist()[:6]
        
        if not columns:
            return None
        
        # Create subplots
        n_cols = min(3, len(columns))
        n_rows = (len(columns) + n_cols - 1) // n_cols
        
        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            subplot_titles=columns,
            vertical_spacing=0.12
        )
        
        colors = self.cancer_colors.get(cancer_type, self.cancer_colors['general'])
        
        for i, col in enumerate(columns):
            row = i // n_cols + 1
            col_idx = i % n_cols + 1
            
            # Create histogram
            fig.add_trace(
                go.Histogram(
                    x=df[col].dropna(),
                    name=col,
                    marker_color=colors[0],
                    opacity=0.7,
                    showlegend=False
                ),
                row=row,
                col=col_idx
            )
        
        fig.update_layout(
            title="Feature Distributions",
            template='plotly_white',
            height=300 * n_rows,
            showlegend=False
        )
        
        return fig.to_json()
    
    def create_treatment_response_plot(self, treatment_data):
        """
        Create treatment response comparison visualization
        """
        treatments = list(treatment_data.keys())
        accuracies = [treatment_data[t]['metrics']['accuracy'] for t in treatments]
        
        fig = go.Figure(data=[
            go.Bar(
                x=treatments,
                y=accuracies,
                marker_color='lightgreen',
                hovertemplate='Treatment: %{x}<br>Accuracy: %{y:.3f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="Treatment Response Prediction Accuracy",
            xaxis_title="Treatment Type",
            yaxis_title="Prediction Accuracy",
            template='plotly_white',
            yaxis=dict(range=[0, 1])
        )
        
        return fig.to_json()
    
    def create_patient_risk_stratification(self, df, risk_scores, cancer_type='general'):
        """
        Create patient risk stratification visualization
        """
        # Create risk categories
        risk_categories = pd.cut(risk_scores, bins=3, labels=['Low', 'Medium', 'High'])
        
        # Count patients in each category
        risk_counts = risk_categories.value_counts()
        
        colors = self.cancer_colors.get(cancer_type, self.cancer_colors['general'])
        
        fig = go.Figure(data=[
            go.Pie(
                labels=risk_counts.index,
                values=risk_counts.values,
                marker_colors=colors,
                hovertemplate='Risk Level: %{label}<br>Patients: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="Patient Risk Stratification",
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def create_model_comparison_plot(self, model_metrics):
        """
        Compare multiple ML models performance
        """
        models = list(model_metrics.keys())
        metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        
        fig = go.Figure()
        
        for metric in metrics:
            values = [model_metrics[model].get(metric, 0) for model in models]
            fig.add_trace(go.Bar(
                x=models,
                y=values,
                name=metric.replace('_', ' ').title(),
                hovertemplate='Model: %{x}<br>%{fullData.name}: %{y:.3f}<extra></extra>'
            ))
        
        fig.update_layout(
            title="Model Performance Comparison",
            xaxis_title="Model Type",
            yaxis_title="Score",
            template='plotly_white',
            barmode='group',
            yaxis=dict(range=[0, 1])
        )
        
        return fig.to_json()
    
    def create_roc_curve(self, y_true, y_pred_proba, title="ROC Curve"):
        """
        Create ROC curve visualization
        """
        from sklearn.metrics import roc_curve, auc
        
        fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
        roc_auc = auc(fpr, tpr)
        
        fig = go.Figure()
        
        # ROC curve
        fig.add_trace(go.Scatter(
            x=fpr,
            y=tpr,
            mode='lines',
            name=f'ROC Curve (AUC = {roc_auc:.3f})',
            line=dict(color='blue', width=3)
        ))
        
        # Diagonal line
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode='lines',
            name='Random Classifier',
            line=dict(color='red', dash='dash')
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="False Positive Rate",
            yaxis_title="True Positive Rate",
            template='plotly_white',
            xaxis=dict(range=[0, 1]),
            yaxis=dict(range=[0, 1])
        )
        
        return fig.to_json()
    
    def create_data_quality_dashboard(self, df, quality_metrics):
        """
        Create comprehensive data quality dashboard
        """
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Missing Data by Column",
                "Data Quality Score",
                "Data Type Distribution",
                "Dataset Overview"
            ],
            specs=[[{"type": "bar"}, {"type": "indicator"}],
                   [{"type": "pie"}, {"type": "table"}]]
        )
        
        # Missing data plot
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0].sort_values(ascending=True)
        
        fig.add_trace(
            go.Bar(
                x=missing_data.values,
                y=missing_data.index,
                orientation='h',
                marker_color='red',
                showlegend=False
            ),
            row=1, col=1
        )
        
        # Data quality indicator
        quality_score = quality_metrics.get('data_quality_score', 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=quality_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Quality Score"},
                gauge={
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 0.5], 'color': "lightgray"},
                        {'range': [0.5, 0.8], 'color': "yellow"},
                        {'range': [0.8, 1], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.9
                    }
                },
                showlegend=False
            ),
            row=1, col=2
        )
        
        # Data type distribution
        dtypes = df.dtypes.value_counts()
        fig.add_trace(
            go.Pie(
                labels=dtypes.index.astype(str),
                values=dtypes.values,
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Dataset overview table
        overview_data = [
            ["Rows", df.shape[0]],
            ["Columns", df.shape[1]],
            ["Missing Values", df.isnull().sum().sum()],
            ["Duplicate Rows", df.duplicated().sum()],
            ["Memory Usage (MB)", round(df.memory_usage(deep=True).sum() / 1024**2, 2)]
        ]
        
        fig.add_trace(
            go.Table(
                header=dict(values=["Metric", "Value"]),
                cells=dict(values=list(zip(*overview_data))),
                showlegend=False
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title="Data Quality Dashboard",
            template='plotly_white',
            height=600
        )
        
        return fig.to_json()
    
    def save_plot_as_image(self, fig_json, filename, format='png'):
        """
        Save plotly figure as image file
        """
        if not self.save_folder:
            return None
        
        try:
            import plotly.graph_objects as go
            fig = go.Figure(json.loads(fig_json))
            
            filepath = self.save_folder / f"{filename}.{format}"
            fig.write_image(str(filepath), format=format)
            
            return str(filepath)
        except Exception as e:
            print(f"Error saving plot: {e}")
            return None