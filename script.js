// Global variables
let patientData = [];
let charts = {};

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadStatus = document.getElementById('uploadStatus');
const summarySection = document.getElementById('summarySection');
const chartsSection = document.getElementById('chartsSection');
const tableSection = document.getElementById('tableSection');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    // File upload events
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// File processing
function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showUploadStatus('Please upload a CSV file.', 'error');
        return;
    }

    showUploadStatus('Processing file...', 'processing');
    
    Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: function(results) {
            if (results.errors.length > 0) {
                showUploadStatus('Error parsing CSV file. Please check the format.', 'error');
                return;
            }
            
            processPatientData(results.data);
        },
        error: function(error) {
            showUploadStatus('Error reading file: ' + error.message, 'error');
        }
    });
}

function processPatientData(data) {
    // Validate and clean data
    const requiredColumns = ['patient_id', 'age', 'hemoglobin_level', 'treatment_type', 'diagnosis_date', 'cancer_type'];
    
    if (data.length === 0) {
        showUploadStatus('No data found in the file.', 'error');
        return;
    }

    // Check if required columns exist
    const firstRow = data[0];
    const missingColumns = requiredColumns.filter(col => !(col in firstRow));
    
    if (missingColumns.length > 0) {
        showUploadStatus(`Missing required columns: ${missingColumns.join(', ')}`, 'error');
        return;
    }

    // Clean and validate data
    patientData = data.filter(row => {
        return row.patient_id && 
               row.age && 
               row.hemoglobin_level && 
               row.treatment_type && 
               row.cancer_type &&
               !isNaN(parseFloat(row.age)) && 
               !isNaN(parseFloat(row.hemoglobin_level));
    }).map(row => ({
        patient_id: row.patient_id.trim(),
        age: parseInt(row.age),
        hemoglobin_level: parseFloat(row.hemoglobin_level),
        treatment_type: row.treatment_type.trim(),
        diagnosis_date: row.diagnosis_date.trim(),
        cancer_type: row.cancer_type.trim()
    }));

    if (patientData.length === 0) {
        showUploadStatus('No valid patient records found. Please check your data format.', 'error');
        return;
    }

    showUploadStatus(`Successfully loaded ${patientData.length} patient records!`, 'success');
    
    // Show data sections and generate visualizations
    displayDataSummary();
    generateCharts();
    displayDataTable();
    
    // Show sections with animation
    setTimeout(() => {
        summarySection.style.display = 'block';
        summarySection.classList.add('fade-in');
        
        setTimeout(() => {
            chartsSection.style.display = 'block';
            chartsSection.classList.add('fade-in');
            
            setTimeout(() => {
                tableSection.style.display = 'block';
                tableSection.classList.add('fade-in');
            }, 300);
        }, 300);
    }, 500);
}

function showUploadStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `upload-status ${type}`;
}

// Data summary functions
function displayDataSummary() {
    const totalPatients = patientData.length;
    const avgHemoglobin = (patientData.reduce((sum, p) => sum + p.hemoglobin_level, 0) / totalPatients).toFixed(1);
    const treatmentCounts = getFrequencyCount(patientData, 'treatment_type');
    const commonTreatment = Object.keys(treatmentCounts)[0] || 'N/A';
    const uniqueCancerTypes = new Set(patientData.map(p => p.cancer_type)).size;

    document.getElementById('totalPatients').textContent = totalPatients;
    document.getElementById('avgHemoglobin').textContent = avgHemoglobin;
    document.getElementById('commonTreatment').textContent = commonTreatment;
    document.getElementById('cancerTypes').textContent = uniqueCancerTypes;
}

// Chart generation functions
function generateCharts() {
    generateHemoglobinDistributionChart();
    generateTreatmentChart();
    generateAgeHemoglobinChart();
    generateCancerTypesChart();
    generateTreatmentHemoglobinChart();
    generateAgeDistributionChart();
}

function generateHemoglobinDistributionChart() {
    const ctx = document.getElementById('hemoglobinChart').getContext('2d');
    
    // Create hemoglobin level ranges
    const ranges = ['< 8', '8-10', '10-12', '12-14', '14-16', '> 16'];
    const counts = [0, 0, 0, 0, 0, 0];
    
    patientData.forEach(patient => {
        const hb = patient.hemoglobin_level;
        if (hb < 8) counts[0]++;
        else if (hb < 10) counts[1]++;
        else if (hb < 12) counts[2]++;
        else if (hb < 14) counts[3]++;
        else if (hb < 16) counts[4]++;
        else counts[5]++;
    });

    charts.hemoglobin = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ranges,
            datasets: [{
                label: 'Number of Patients',
                data: counts,
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Hemoglobin Level (g/dL)'
                    }
                }
            }
        }
    });
}

function generateTreatmentChart() {
    const ctx = document.getElementById('treatmentChart').getContext('2d');
    const treatmentCounts = getFrequencyCount(patientData, 'treatment_type');
    
    const colors = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c', 
        '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
    ];

    charts.treatment = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(treatmentCounts),
            datasets: [{
                data: Object.values(treatmentCounts),
                backgroundColor: colors.slice(0, Object.keys(treatmentCounts).length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function generateAgeHemoglobinChart() {
    const ctx = document.getElementById('ageHemoglobinChart').getContext('2d');
    
    charts.ageHemoglobin = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Patients',
                data: patientData.map(p => ({ x: p.age, y: p.hemoglobin_level })),
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Age (years)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Hemoglobin Level (g/dL)'
                    }
                }
            }
        }
    });
}

function generateCancerTypesChart() {
    const ctx = document.getElementById('cancerChart').getContext('2d');
    const cancerCounts = getFrequencyCount(patientData, 'cancer_type');
    
    const colors = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c', 
        '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
    ];

    charts.cancer = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(cancerCounts),
            datasets: [{
                data: Object.values(cancerCounts),
                backgroundColor: colors.slice(0, Object.keys(cancerCounts).length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function generateTreatmentHemoglobinChart() {
    const ctx = document.getElementById('treatmentHemoglobinChart').getContext('2d');
    
    // Calculate average hemoglobin by treatment type
    const treatmentGroups = {};
    patientData.forEach(patient => {
        if (!treatmentGroups[patient.treatment_type]) {
            treatmentGroups[patient.treatment_type] = [];
        }
        treatmentGroups[patient.treatment_type].push(patient.hemoglobin_level);
    });
    
    const treatments = Object.keys(treatmentGroups);
    const avgHemoglobin = treatments.map(treatment => {
        const levels = treatmentGroups[treatment];
        return levels.reduce((sum, level) => sum + level, 0) / levels.length;
    });

    charts.treatmentHemoglobin = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: treatments,
            datasets: [{
                label: 'Average Hemoglobin Level (g/dL)',
                data: avgHemoglobin,
                backgroundColor: 'rgba(118, 75, 162, 0.8)',
                borderColor: 'rgba(118, 75, 162, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Average Hemoglobin Level (g/dL)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Treatment Type'
                    }
                }
            }
        }
    });
}

function generateAgeDistributionChart() {
    const ctx = document.getElementById('ageChart').getContext('2d');
    
    // Create age ranges
    const ranges = ['< 30', '30-40', '40-50', '50-60', '60-70', '> 70'];
    const counts = [0, 0, 0, 0, 0, 0];
    
    patientData.forEach(patient => {
        const age = patient.age;
        if (age < 30) counts[0]++;
        else if (age < 40) counts[1]++;
        else if (age < 50) counts[2]++;
        else if (age < 60) counts[3]++;
        else if (age < 70) counts[4]++;
        else counts[5]++;
    });

    charts.age = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ranges,
            datasets: [{
                label: 'Number of Patients',
                data: counts,
                backgroundColor: 'rgba(240, 147, 251, 0.2)',
                borderColor: 'rgba(240, 147, 251, 1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'rgba(240, 147, 251, 1)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: 'Number of Patients'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Age Range (years)'
                    }
                }
            }
        }
    });
}

// Data table functions
function displayDataTable() {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';
    
    patientData.forEach(patient => {
        const row = tableBody.insertRow();
        row.insertCell(0).textContent = patient.patient_id;
        row.insertCell(1).textContent = patient.age;
        row.insertCell(2).textContent = patient.hemoglobin_level.toFixed(1);
        row.insertCell(3).textContent = patient.treatment_type;
        row.insertCell(4).textContent = patient.cancer_type;
        row.insertCell(5).textContent = patient.diagnosis_date;
    });
}

// Utility functions
function getFrequencyCount(data, field) {
    const counts = {};
    data.forEach(item => {
        const value = item[field];
        counts[value] = (counts[value] || 0) + 1;
    });
    
    // Sort by frequency (descending)
    return Object.fromEntries(
        Object.entries(counts).sort(([,a], [,b]) => b - a)
    );
}

// Cleanup function for charts
function destroyCharts() {
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    charts = {};
}