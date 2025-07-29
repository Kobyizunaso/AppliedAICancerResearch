"""
API routes for machine learning analysis, model training, and predictions
"""

from flask import Blueprint, request, jsonify, current_app
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import db
from models.dataset import Dataset
from models.analysis import Analysis, AnalysisResult
from models.ml_model import MLModel
from models.user import User
from ml_models.cancer_models import CancerMLPipeline, CancerDataAnalyzer
from utils.data_processor import MedicalDataProcessor
from pathlib import Path
import traceback
from datetime import datetime

ml_bp = Blueprint('ml', __name__)

def init_components():
    """Initialize ML components"""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
    processed_folder = current_app.config.get('PROCESSED_FOLDER', 'data/processed')
    models_folder = current_app.config.get('MODELS_FOLDER', 'data/models')
    
    processor = MedicalDataProcessor(upload_folder, processed_folder)
    pipeline = CancerMLPipeline()
    analyzer = CancerDataAnalyzer()
    
    return processor, pipeline, analyzer, models_folder

@ml_bp.route('/analyze', methods=['POST'])
def run_analysis():
    """
    Run comprehensive ML analysis on a dataset
    """
    try:
        data = request.get_json()
        
        # Required parameters
        dataset_id = data.get('dataset_id')
        analysis_name = data.get('name', 'Unnamed Analysis')
        analysis_type = data.get('analysis_type', 'prediction')  # prediction, survival, classification
        target_variable = data.get('target_variable')
        user_id = data.get('user_id')  # In production, get from JWT token
        
        # Optional parameters
        features = data.get('features', [])
        model_type = data.get('model_type', 'random_forest')
        description = data.get('description', '')
        
        # Validate inputs
        if not all([dataset_id, target_variable, user_id]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Validate dataset exists
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Validate user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Create analysis record
        analysis = Analysis(
            name=analysis_name,
            analysis_type=analysis_type,
            target_variable=target_variable,
            user_id=user_id,
            dataset_id=dataset_id,
            description=description
        )
        analysis.model_type = model_type
        analysis.set_features(features)
        
        db.session.add(analysis)
        db.session.flush()  # Get the ID without committing
        
        # Start analysis
        analysis.start_analysis()
        
        try:
            # Initialize components
            processor, pipeline, analyzer, models_folder = init_components()
            
            # Load dataset
            df = processor.load_processed_dataset(dataset.processed_file_path)
            
            # Validate target variable exists
            if target_variable not in df.columns:
                raise ValueError(f"Target variable '{target_variable}' not found in dataset")
            
            # Prepare data for ML
            if not features:
                # Auto-select features (exclude target and non-numeric columns)
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                features = [col for col in numeric_cols if col != target_variable]
            
            # Validate features exist
            missing_features = [f for f in features if f not in df.columns]
            if missing_features:
                raise ValueError(f"Features not found: {missing_features}")
            
            analysis.set_features(features)
            
            # Preprocess data
            X_train, X_test, y_train, y_test, feature_names = pipeline.preprocess_data(
                df[[target_variable] + features].copy(), target_variable
            )
            
            # Train model
            model = pipeline.train_classification_model(X_train, y_train, model_type)
            
            # Evaluate model
            metrics = pipeline.evaluate_model(model, X_test, y_test)
            
            # Get feature importance
            feature_importance = pipeline.get_feature_importance(model, feature_names)
            
            # Cross-validation
            cv_results = pipeline.cross_validate_model(
                X_train, y_train, model_type
            )
            
            # Save model
            model_filename = f"model_{analysis.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            model_path = Path(models_folder) / model_filename
            saved_model_path = pipeline.save_model(model, str(model_path))
            
            # Create ML model record
            ml_model = MLModel(
                name=f"{analysis_name} Model",
                model_type=model_type,
                cancer_type=dataset.cancer_type,
                target_variable=target_variable,
                model_file_path=saved_model_path,
                user_id=user_id,
                dataset_id=dataset_id,
                description=f"Model trained for {analysis_name}"
            )
            
            ml_model.set_features_used(feature_names)
            ml_model.update_performance_metrics(metrics)
            ml_model.set_cv_scores(cv_results['cv_scores'])
            ml_model.training_samples = len(X_train)
            
            db.session.add(ml_model)
            db.session.flush()
            
            # Update analysis with model reference
            analysis.model_id = ml_model.id
            
            # Store results
            results = {
                'metrics': metrics,
                'feature_importance': feature_importance,
                'cross_validation': cv_results,
                'model_id': ml_model.id
            }
            
            # Create analysis results
            analysis_result = AnalysisResult(
                result_type='prediction',
                result_data=results,
                analysis_id=analysis.id
            )
            db.session.add(analysis_result)
            
            # Cancer-specific analysis
            if dataset.cancer_type in ['breast', 'lung']:
                try:
                    if dataset.cancer_type == 'breast':
                        cancer_results = analyzer.analyze_breast_cancer(df)
                    elif dataset.cancer_type == 'lung':
                        cancer_results = analyzer.analyze_lung_cancer(df)
                    
                    if cancer_results:
                        cancer_analysis_result = AnalysisResult(
                            result_type='cancer_specific',
                            result_data=cancer_results,
                            analysis_id=analysis.id
                        )
                        db.session.add(cancer_analysis_result)
                        
                        # Generate insights
                        insights = analyzer.generate_insights(cancer_results)
                        if insights:
                            insights_result = AnalysisResult(
                                result_type='insights',
                                result_data={'insights': insights},
                                analysis_id=analysis.id
                            )
                            db.session.add(insights_result)
                
                except Exception as e:
                    print(f"Cancer-specific analysis failed: {e}")
            
            # Complete analysis
            analysis.complete_analysis(metrics)
            db.session.commit()
            
            return jsonify({
                'message': 'Analysis completed successfully',
                'analysis': analysis.to_dict(),
                'model': ml_model.to_dict(),
                'results': results
            }), 200
            
        except Exception as e:
            # Analysis failed
            error_message = str(e)
            analysis.fail_analysis(error_message)
            db.session.commit()
            
            return jsonify({
                'error': f'Analysis failed: {error_message}',
                'analysis': analysis.to_dict()
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to start analysis: {str(e)}'}), 500

@ml_bp.route('/predict', methods=['POST'])
def make_prediction():
    """
    Make predictions using a trained model
    """
    try:
        data = request.get_json()
        
        model_id = data.get('model_id')
        input_data = data.get('input_data')  # Dictionary of feature values
        
        if not model_id or not input_data:
            return jsonify({'error': 'Model ID and input data required'}), 400
        
        # Load model
        ml_model = MLModel.query.get(model_id)
        if not ml_model:
            return jsonify({'error': 'Model not found'}), 404
        
        # Initialize pipeline and load model
        _, pipeline, _, _ = init_components()
        model = pipeline.load_model(ml_model.model_file_path)
        
        # Prepare input data
        features_used = ml_model.get_features_used()
        
        # Validate input features
        missing_features = [f for f in features_used if f not in input_data]
        if missing_features:
            return jsonify({'error': f'Missing features: {missing_features}'}), 400
        
        # Create input array
        import numpy as np
        input_array = np.array([[input_data[f] for f in features_used]])
        
        # Scale input if needed (assuming pipeline was used for training)
        input_scaled = pipeline.scaler.transform(input_array)
        
        # Make prediction
        prediction = model.predict(input_scaled)[0]
        prediction_proba = None
        
        if hasattr(model, 'predict_proba'):
            prediction_proba = model.predict_proba(input_scaled)[0].tolist()
        
        # Update model usage
        ml_model.update_last_used()
        
        return jsonify({
            'prediction': prediction.tolist() if hasattr(prediction, 'tolist') else prediction,
            'prediction_probability': prediction_proba,
            'model': ml_model.to_dict(),
            'input_features': features_used,
            'input_data': input_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@ml_bp.route('/analyses', methods=['GET'])
def get_analyses():
    """
    Get list of analyses for a user
    """
    try:
        user_id = request.args.get('user_id')
        dataset_id = request.args.get('dataset_id')
        analysis_type = request.args.get('analysis_type')
        status = request.args.get('status')
        
        # Build query
        query = Analysis.query
        
        if user_id:
            query = query.filter(Analysis.user_id == user_id)
        
        if dataset_id:
            query = query.filter(Analysis.dataset_id == dataset_id)
        
        if analysis_type:
            query = query.filter(Analysis.analysis_type == analysis_type)
        
        if status:
            query = query.filter(Analysis.status == status)
        
        analyses = query.order_by(Analysis.start_time.desc()).all()
        
        return jsonify({
            'analyses': [analysis.to_dict() for analysis in analyses],
            'count': len(analyses)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch analyses: {str(e)}'}), 500

@ml_bp.route('/analyses/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """
    Get specific analysis with results
    """
    try:
        analysis = Analysis.query.get(analysis_id)
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Get analysis results
        results = [result.to_dict() for result in analysis.results]
        
        return jsonify({
            'analysis': analysis.to_dict(),
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch analysis: {str(e)}'}), 500

@ml_bp.route('/models', methods=['GET'])
def get_models():
    """
    Get list of trained models
    """
    try:
        user_id = request.args.get('user_id')
        cancer_type = request.args.get('cancer_type')
        model_type = request.args.get('model_type')
        is_active = request.args.get('is_active', type=bool)
        
        # Build query
        query = MLModel.query
        
        if user_id:
            query = query.filter(MLModel.user_id == user_id)
        
        if cancer_type:
            query = query.filter(MLModel.cancer_type == cancer_type)
        
        if model_type:
            query = query.filter(MLModel.model_type == model_type)
        
        if is_active is not None:
            query = query.filter(MLModel.is_active == is_active)
        
        models = query.order_by(MLModel.created_at.desc()).all()
        
        return jsonify({
            'models': [model.to_dict() for model in models],
            'count': len(models)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch models: {str(e)}'}), 500

@ml_bp.route('/models/<int:model_id>', methods=['GET'])
def get_model(model_id):
    """
    Get specific model details
    """
    try:
        model = MLModel.query.get(model_id)
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        
        return jsonify({
            'model': model.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch model: {str(e)}'}), 500

@ml_bp.route('/models/<int:model_id>/validate', methods=['POST'])
def validate_model(model_id):
    """
    Validate a trained model
    """
    try:
        model = MLModel.query.get(model_id)
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        
        # Mark as validated
        model.validate_model()
        
        return jsonify({
            'message': 'Model validated successfully',
            'model': model.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Model validation failed: {str(e)}'}), 500

@ml_bp.route('/survival-analysis', methods=['POST'])
def run_survival_analysis():
    """
    Run survival analysis on dataset
    """
    try:
        data = request.get_json()
        
        dataset_id = data.get('dataset_id')
        duration_col = data.get('duration_column')
        event_col = data.get('event_column')
        user_id = data.get('user_id')
        analysis_name = data.get('name', 'Survival Analysis')
        
        if not all([dataset_id, duration_col, event_col, user_id]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Validate dataset
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Initialize components
        processor, pipeline, analyzer, _ = init_components()
        
        # Load dataset
        df = processor.load_processed_dataset(dataset.processed_file_path)
        
        # Validate columns exist
        if duration_col not in df.columns or event_col not in df.columns:
            return jsonify({'error': 'Duration or event column not found'}), 400
        
        # Create analysis record
        analysis = Analysis(
            name=analysis_name,
            analysis_type='survival',
            target_variable=f"{duration_col},{event_col}",
            user_id=user_id,
            dataset_id=dataset_id
        )
        
        db.session.add(analysis)
        db.session.flush()
        
        analysis.start_analysis()
        
        try:
            # Run survival analysis
            survival_data, kmf = pipeline.survival_analysis(df, duration_col, event_col)
            
            # Cox regression if covariates available
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            covariates = [col for col in numeric_cols if col not in [duration_col, event_col]][:5]  # Limit to 5
            
            cox_results = None
            if covariates:
                try:
                    cox_results = pipeline.cox_regression(df, duration_col, event_col, covariates)
                except Exception as e:
                    print(f"Cox regression failed: {e}")
            
            # Store results
            results = {
                'survival_analysis': survival_data,
                'cox_regression': cox_results,
                'covariates_used': covariates
            }
            
            # Create analysis result
            analysis_result = AnalysisResult(
                result_type='survival',
                result_data=results,
                analysis_id=analysis.id
            )
            db.session.add(analysis_result)
            
            # Complete analysis
            analysis.complete_analysis({'median_survival': survival_data.get('median_survival', 0)})
            db.session.commit()
            
            return jsonify({
                'message': 'Survival analysis completed successfully',
                'analysis': analysis.to_dict(),
                'results': results
            }), 200
            
        except Exception as e:
            analysis.fail_analysis(str(e))
            db.session.commit()
            return jsonify({'error': f'Survival analysis failed: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to start survival analysis: {str(e)}'}), 500

@ml_bp.route('/model-types', methods=['GET'])
def get_model_types():
    """
    Get available ML model types
    """
    model_types = [
        'logistic_regression',
        'random_forest', 
        'svm',
        'neural_network',
        'random_forest_regressor'
    ]
    
    return jsonify({
        'model_types': model_types,
        'descriptions': {
            'logistic_regression': 'Linear model for binary classification',
            'random_forest': 'Ensemble method using decision trees',
            'svm': 'Support Vector Machine for classification',
            'neural_network': 'Multi-layer perceptron neural network',
            'random_forest_regressor': 'Random forest for regression tasks'
        }
    }), 200