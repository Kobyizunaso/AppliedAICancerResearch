"""
API routes for data upload, processing, and management
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import db
from models.dataset import Dataset
from models.user import User
from utils.data_processor import MedicalDataProcessor
from pathlib import Path

data_bp = Blueprint('data', __name__)

def init_data_processor():
    """Initialize data processor with app config"""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
    processed_folder = current_app.config.get('PROCESSED_FOLDER', 'data/processed')
    return MedicalDataProcessor(upload_folder, processed_folder)

def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'csv', 'json', 'xlsx', 'xls'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@data_bp.route('/upload', methods=['POST'])
def upload_dataset():
    """
    Upload and process a new dataset
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get additional form data
        dataset_name = request.form.get('name', 'Unnamed Dataset')
        description = request.form.get('description', '')
        user_id = request.form.get('user_id')  # In production, get from JWT token
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        # Validate user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_folder / filename
        file.save(str(file_path))
        
        # Get file size
        file_size = file_path.stat().st_size
        file_format = filename.rsplit('.', 1)[1].lower()
        
        # Process dataset
        processor = init_data_processor()
        processing_result = processor.process_dataset(
            str(file_path), user_id, dataset_name, description
        )
        
        if not processing_result['success']:
            # Clean up uploaded file if processing failed
            file_path.unlink(missing_ok=True)
            return jsonify({'error': processing_result['error']}), 400
        
        # Create dataset record in database
        dataset = Dataset(
            name=dataset_name,
            cancer_type=processing_result['cancer_type'],
            data_type=processing_result['data_type'],
            file_path=str(file_path),
            file_size=file_size,
            file_format=file_format,
            user_id=user_id,
            description=description
        )
        
        # Update dataset with processing results
        dataset.mark_as_processed(processing_result['processed_file_path'])
        dataset.update_data_stats(
            processing_result['num_rows'],
            processing_result['num_columns'],
            processing_result['missing_data_percentage'],
            processing_result['data_quality_score']
        )
        dataset.set_column_info(processing_result['column_metadata'])
        dataset.validate_dataset()
        
        db.session.add(dataset)
        db.session.commit()
        
        return jsonify({
            'message': 'Dataset uploaded and processed successfully',
            'dataset': dataset.to_dict(),
            'processing_details': processing_result
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@data_bp.route('/datasets', methods=['GET'])
def get_datasets():
    """
    Get list of datasets for a user
    """
    try:
        user_id = request.args.get('user_id')
        cancer_type = request.args.get('cancer_type')
        data_type = request.args.get('data_type')
        
        # Build query
        query = Dataset.query
        
        if user_id:
            query = query.filter(Dataset.user_id == user_id)
        
        if cancer_type:
            query = query.filter(Dataset.cancer_type == cancer_type)
        
        if data_type:
            query = query.filter(Dataset.data_type == data_type)
        
        # Add public datasets if user is not filtering by user_id
        if not user_id:
            query = query.filter(Dataset.is_public == True)
        
        datasets = query.order_by(Dataset.upload_date.desc()).all()
        
        return jsonify({
            'datasets': [dataset.to_dict() for dataset in datasets],
            'count': len(datasets)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch datasets: {str(e)}'}), 500

@data_bp.route('/datasets/<int:dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """
    Get specific dataset details
    """
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Get dataset summary
        processor = init_data_processor()
        summary = processor.get_dataset_summary(dataset.processed_file_path)
        
        return jsonify({
            'dataset': dataset.to_dict(),
            'summary': summary
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch dataset: {str(e)}'}), 500

@data_bp.route('/datasets/<int:dataset_id>/data', methods=['GET'])
def get_dataset_data():
    """
    Get actual data from processed dataset
    """
    try:
        dataset_id = request.view_args['dataset_id']
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Load data
        processor = init_data_processor()
        df = processor.load_processed_dataset(dataset.processed_file_path)
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        data_subset = df.iloc[start_idx:end_idx]
        
        return jsonify({
            'data': data_subset.to_dict('records'),
            'total_rows': len(df),
            'page': page,
            'per_page': per_page,
            'has_next': end_idx < len(df),
            'has_prev': page > 1,
            'columns': df.columns.tolist()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch dataset data: {str(e)}'}), 500

@data_bp.route('/datasets/<int:dataset_id>', methods=['PUT'])
def update_dataset(dataset_id):
    """
    Update dataset metadata
    """
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            dataset.name = data['name']
        if 'description' in data:
            dataset.description = data['description']
        if 'is_public' in data:
            dataset.is_public = data['is_public']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Dataset updated successfully',
            'dataset': dataset.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to update dataset: {str(e)}'}), 500

@data_bp.route('/datasets/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    """
    Delete a dataset and its files
    """
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Delete files
        try:
            if os.path.exists(dataset.file_path):
                os.unlink(dataset.file_path)
            if dataset.processed_file_path and os.path.exists(dataset.processed_file_path):
                os.unlink(dataset.processed_file_path)
        except Exception as e:
            print(f"Warning: Could not delete files: {e}")
        
        # Delete database record
        db.session.delete(dataset)
        db.session.commit()
        
        return jsonify({'message': 'Dataset deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete dataset: {str(e)}'}), 500

@data_bp.route('/datasets/<int:dataset_id>/validate', methods=['POST'])
def validate_dataset(dataset_id):
    """
    Validate dataset quality and structure
    """
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        processor = init_data_processor()
        df = processor.load_processed_dataset(dataset.processed_file_path)
        
        # Run validation
        is_valid, validation_message = processor.validate_file_format(dataset.processed_file_path)
        data_quality_score = processor.calculate_data_quality_score(df)
        column_metadata = processor.extract_column_metadata(df)
        
        # Update dataset
        dataset.data_quality_score = data_quality_score
        dataset.set_column_info(column_metadata)
        
        if is_valid and data_quality_score > 0.7:
            dataset.validate_dataset()
        
        db.session.commit()
        
        return jsonify({
            'is_valid': is_valid,
            'validation_message': validation_message,
            'data_quality_score': data_quality_score,
            'column_metadata': column_metadata,
            'dataset': dataset.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@data_bp.route('/cancer-types', methods=['GET'])
def get_cancer_types():
    """
    Get available cancer types
    """
    try:
        cancer_types = db.session.query(Dataset.cancer_type).distinct().all()
        cancer_types = [ct[0] for ct in cancer_types]
        
        return jsonify({
            'cancer_types': cancer_types,
            'count': len(cancer_types)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch cancer types: {str(e)}'}), 500

@data_bp.route('/data-types', methods=['GET'])
def get_data_types():
    """
    Get available data types
    """
    try:
        data_types = db.session.query(Dataset.data_type).distinct().all()
        data_types = [dt[0] for dt in data_types]
        
        return jsonify({
            'data_types': data_types,
            'count': len(data_types)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch data types: {str(e)}'}), 500