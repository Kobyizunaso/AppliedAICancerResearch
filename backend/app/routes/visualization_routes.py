"""
API routes for data visualization and chart generation
"""

from flask import Blueprint, request, jsonify, current_app
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import db
from models.dataset import Dataset
from models.analysis import Analysis, AnalysisResult
from utils.data_processor import MedicalDataProcessor
from utils.visualization import CancerDataVisualizer
import json

viz_bp = Blueprint('viz', __name__)

def init_components():
    """Initialize visualization components"""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
    processed_folder = current_app.config.get('PROCESSED_FOLDER', 'data/processed')
    
    processor = MedicalDataProcessor(upload_folder, processed_folder)
    visualizer = CancerDataVisualizer()
    
    return processor, visualizer

@viz_bp.route('/dataset/<int:dataset_id>/overview', methods=['GET'])
def get_dataset_overview_charts(dataset_id):
    """
    Generate overview visualizations for a dataset
    """
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        processor, visualizer = init_components()
        
        # Load dataset
        df = processor.load_processed_dataset(dataset.processed_file_path)
        
        # Generate visualizations
        charts = {}
        
        # Data quality dashboard
        quality_metrics = {
            'data_quality_score': dataset.data_quality_score or 0.8,
            'missing_data_percentage': dataset.missing_data_percentage or 0
        }
        
        charts['quality_dashboard'] = visualizer.create_data_quality_dashboard(df, quality_metrics)
        
        # Distribution plots
        charts['distributions'] = visualizer.create_distribution_plots(df, cancer_type=dataset.cancer_type)
        
        # Correlation heatmap
        charts['correlation'] = visualizer.create_correlation_heatmap(df)
        
        return jsonify({
            'dataset_id': dataset_id,
            'charts': charts,
            'dataset_info': {
                'name': dataset.name,
                'cancer_type': dataset.cancer_type,
                'data_type': dataset.data_type,
                'rows': dataset.num_rows,
                'columns': dataset.num_columns
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate overview charts: {str(e)}'}), 500

@viz_bp.route('/analysis/<int:analysis_id>/results', methods=['GET'])
def get_analysis_visualizations(analysis_id):
    """
    Generate visualizations for analysis results
    """
    try:
        analysis = Analysis.query.get(analysis_id)
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        processor, visualizer = init_components()
        
        charts = {}
        
        # Get analysis results
        for result in analysis.results:
            result_data = result.get_result_data()
            
            if result.result_type == 'prediction':
                # Feature importance plot
                if 'feature_importance' in result_data:
                    charts['feature_importance'] = visualizer.create_feature_importance_plot(
                        result_data['feature_importance'],
                        f"Feature Importance - {analysis.name}"
                    )
                
                # Model performance metrics
                if 'metrics' in result_data:
                    charts['model_metrics'] = {
                        'accuracy': result_data['metrics'].get('accuracy', 0),
                        'precision': result_data['metrics'].get('precision', 0),
                        'recall': result_data['metrics'].get('recall', 0),
                        'f1_score': result_data['metrics'].get('f1_score', 0)
                    }
            
            elif result.result_type == 'survival':
                # Survival curve
                if 'survival_analysis' in result_data:
                    charts['survival_curve'] = visualizer.create_survival_curve(
                        result_data['survival_analysis'],
                        f"Survival Analysis - {analysis.name}"
                    )
            
            elif result.result_type == 'cancer_specific':
                # Cancer-specific visualizations
                if 'treatment_response' in result_data:
                    charts['treatment_response'] = visualizer.create_treatment_response_plot(
                        result_data['treatment_response']
                    )
        
        return jsonify({
            'analysis_id': analysis_id,
            'analysis_name': analysis.name,
            'analysis_type': analysis.analysis_type,
            'charts': charts
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate analysis visualizations: {str(e)}'}), 500

@viz_bp.route('/models/comparison', methods=['POST'])
def compare_models():
    """
    Generate model comparison visualizations
    """
    try:
        data = request.get_json()
        model_ids = data.get('model_ids', [])
        
        if not model_ids:
            return jsonify({'error': 'No model IDs provided'}), 400
        
        # Get models
        from models.ml_model import MLModel
        models = MLModel.query.filter(MLModel.id.in_(model_ids)).all()
        
        if not models:
            return jsonify({'error': 'No models found'}), 404
        
        # Prepare model metrics for comparison
        model_metrics = {}
        for model in models:
            model_metrics[f"{model.name} ({model.model_type})"] = {
                'accuracy': model.accuracy or 0,
                'precision': model.precision or 0,
                'recall': model.recall or 0,
                'f1_score': model.f1_score or 0,
                'auc_score': model.auc_score or 0
            }
        
        processor, visualizer = init_components()
        
        # Generate comparison chart
        comparison_chart = visualizer.create_model_comparison_plot(model_metrics)
        
        return jsonify({
            'comparison_chart': comparison_chart,
            'models_compared': len(models),
            'model_details': [model.to_dict() for model in models]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate model comparison: {str(e)}'}), 500

@viz_bp.route('/survival-curve', methods=['POST'])
def generate_survival_curve():
    """
    Generate survival curve from analysis results
    """
    try:
        data = request.get_json()
        analysis_id = data.get('analysis_id')
        
        if not analysis_id:
            return jsonify({'error': 'Analysis ID required'}), 400
        
        analysis = Analysis.query.get(analysis_id)
        if not analysis or analysis.analysis_type != 'survival':
            return jsonify({'error': 'Survival analysis not found'}), 404
        
        # Get survival results
        survival_result = None
        for result in analysis.results:
            if result.result_type == 'survival':
                survival_result = result.get_result_data()
                break
        
        if not survival_result or 'survival_analysis' not in survival_result:
            return jsonify({'error': 'Survival data not found'}), 404
        
        processor, visualizer = init_components()
        
        # Generate survival curve
        survival_chart = visualizer.create_survival_curve(
            survival_result['survival_analysis'],
            f"Kaplan-Meier Survival Curve - {analysis.name}"
        )
        
        return jsonify({
            'survival_chart': survival_chart,
            'analysis_name': analysis.name,
            'median_survival': survival_result['survival_analysis'].get('median_survival')
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate survival curve: {str(e)}'}), 500

@viz_bp.route('/risk-stratification', methods=['POST'])
def generate_risk_stratification():
    """
    Generate patient risk stratification visualization
    """
    try:
        data = request.get_json()
        dataset_id = data.get('dataset_id')
        risk_column = data.get('risk_column')
        
        if not dataset_id or not risk_column:
            return jsonify({'error': 'Dataset ID and risk column required'}), 400
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        processor, visualizer = init_components()
        
        # Load dataset
        df = processor.load_processed_dataset(dataset.processed_file_path)
        
        if risk_column not in df.columns:
            return jsonify({'error': f'Risk column "{risk_column}" not found'}), 400
        
        # Extract risk scores
        risk_scores = df[risk_column].dropna()
        
        if len(risk_scores) == 0:
            return jsonify({'error': 'No valid risk scores found'}), 400
        
        # Generate risk stratification chart
        risk_chart = visualizer.create_patient_risk_stratification(
            df, risk_scores, dataset.cancer_type
        )
        
        return jsonify({
            'risk_chart': risk_chart,
            'dataset_name': dataset.name,
            'total_patients': len(risk_scores),
            'risk_column': risk_column
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate risk stratification: {str(e)}'}), 500

@viz_bp.route('/custom-plot', methods=['POST'])
def generate_custom_plot():
    """
    Generate custom visualization based on user parameters
    """
    try:
        data = request.get_json()
        dataset_id = data.get('dataset_id')
        plot_type = data.get('plot_type')  # histogram, scatter, box, etc.
        x_column = data.get('x_column')
        y_column = data.get('y_column')
        color_column = data.get('color_column')
        
        if not dataset_id or not plot_type or not x_column:
            return jsonify({'error': 'Dataset ID, plot type, and X column required'}), 400
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        processor, visualizer = init_components()
        
        # Load dataset
        df = processor.load_processed_dataset(dataset.processed_file_path)
        
        # Validate columns exist
        required_columns = [x_column]
        if y_column:
            required_columns.append(y_column)
        if color_column:
            required_columns.append(color_column)
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Columns not found: {missing_columns}'}), 400
        
        # Generate plot based on type
        import plotly.express as px
        
        if plot_type == 'histogram':
            fig = px.histogram(df, x=x_column, color=color_column, title=f"Distribution of {x_column}")
        elif plot_type == 'scatter' and y_column:
            fig = px.scatter(df, x=x_column, y=y_column, color=color_column, 
                           title=f"{y_column} vs {x_column}")
        elif plot_type == 'box':
            fig = px.box(df, x=color_column, y=x_column, title=f"Box Plot of {x_column}")
        else:
            return jsonify({'error': 'Unsupported plot type or missing required columns'}), 400
        
        # Convert to JSON
        custom_chart = fig.to_json()
        
        return jsonify({
            'custom_chart': custom_chart,
            'plot_type': plot_type,
            'dataset_name': dataset.name,
            'columns_used': {
                'x': x_column,
                'y': y_column,
                'color': color_column
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate custom plot: {str(e)}'}), 500

@viz_bp.route('/export-chart', methods=['POST'])
def export_chart():
    """
    Export chart as image file
    """
    try:
        data = request.get_json()
        chart_data = data.get('chart_data')  # JSON chart data
        filename = data.get('filename', 'chart')
        format = data.get('format', 'png')
        
        if not chart_data:
            return jsonify({'error': 'Chart data required'}), 400
        
        processor, visualizer = init_components()
        
        # Save chart as image
        saved_path = visualizer.save_plot_as_image(chart_data, filename, format)
        
        if saved_path:
            return jsonify({
                'message': 'Chart exported successfully',
                'file_path': saved_path,
                'filename': f"{filename}.{format}"
            }), 200
        else:
            return jsonify({'error': 'Failed to export chart'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Chart export failed: {str(e)}'}), 500