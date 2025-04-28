from flask import Flask, render_template_string, request
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# Paths to the Excel files
dir_path = os.path.dirname(os.path.abspath(__file__))
sector_file = os.path.join(dir_path, 'summary_per_sector-up-to-30-mar-2025.xlsx')
project_file = os.path.join(dir_path, 'summary_per_project-up-to-30-mar-2025.xlsx')

# Load data
sector_df = pd.read_excel(sector_file)
project_df = pd.read_excel(project_file)

# Get dropdown options
dropdown_sectors = sorted(sector_df['SECTOR'].dropna().unique())
dropdown_metrics = ['COST', 'CASH_OUT', 'CASH_IN']

TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sector Financial Summary</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8f9fa; }
        .container { max-width: 800px; margin: 40px auto; }
        .card { box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
        .form-select, .form-control, .btn { min-width: 150px; }
        .total { font-weight: bold; color: #198754; font-size: 1.3em; }
        .footer { text-align: center; color: #888; margin-top: 40px; font-size: 0.95em; }
        .table-responsive { margin-top: 20px; }
    </style>
</head>
<body>
<div class="container">
    <div class="text-center mb-4">
        <img src="https://img.icons8.com/ios-filled/50/198754/money-bag.png" alt="icon" style="height:40px;vertical-align:middle;">
        <span class="fs-3 fw-bold ms-2">Sector Financial Summary <span class="fs-6 text-secondary">(up to 30-Mar-2025)</span></span>
    </div>
    <div class="card p-4">
        <form method="post" class="row g-3 align-items-end">
            <div class="col-md-6">
                <label for="sector" class="form-label">Select Sector</label>
                <select name="sector" id="sector" class="form-select">
                    {% for sector in sectors %}
                        <option value="{{ sector }}" {% if sector == selected_sector %}selected{% endif %}>{{ sector }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-4">
                <label for="metric" class="form-label">Select Metric</label>
                <select name="metric" id="metric" class="form-select">
                    {% for metric in metrics %}
                        <option value="{{ metric }}" {% if metric == selected_metric %}selected{% endif %}>{{ metric.replace('_', ' ').title() }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-2 d-grid">
                <button type="submit" class="btn btn-success">Show</button>
            </div>
        </form>
        {% if total is not none %}
            <div class="mt-4">
                <h4>Total <span class="text-capitalize">{{ selected_metric.replace('_', ' ').title() }}</span> for <span class="text-primary">{{ selected_sector }}</span>:</h4>
                <div class="total mb-3">{{ '{:,.2f}'.format(total) }}</div>
                <h5 class="mb-2">Breakdown by Project</h5>
                <div class="table-responsive">
                    <table class="table table-striped table-bordered">
                        <thead class="table-light">
                            <tr>
                                <th>Project Number</th>
                                <th>Project Name</th>
                                <th>{{ selected_metric.replace('_', ' ').title() }}</th>
                            </tr>
                        </thead>
                        <tbody>
                        {% for row in breakdown %}
                            <tr>
                                <td>{{ row['PROJECT_NUM'] }}</td>
                                <td>{{ row['PROJECT_NAME'] }}</td>
                                <td>{{ '{:,.2f}'.format(row[selected_metric]) }}</td>
                            </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        {% endif %}
    </div>
    <div class="footer">
        &copy; {{ year }} RME Data Science | Powered by Flask & Bootstrap
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_sector = dropdown_sectors[0]
    selected_metric = dropdown_metrics[0]
    total = None
    breakdown = []
    if request.method == 'POST':
        selected_sector = request.form.get('sector', selected_sector)
        selected_metric = request.form.get('metric', selected_metric)
        # Get total for sector
        sector_row = sector_df[sector_df['SECTOR'] == selected_sector]
        if not sector_row.empty:
            total = sector_row.iloc[0][selected_metric]
        # Get breakdown by project
        proj_rows = project_df[project_df['SECTOR'] == selected_sector][['PROJECT_NUM', 'PROJECT_NAME', selected_metric]]
        breakdown = proj_rows.to_dict('records')
    return render_template_string(TEMPLATE,
                                  sectors=dropdown_sectors,
                                  metrics=dropdown_metrics,
                                  selected_sector=selected_sector,
                                  selected_metric=selected_metric,
                                  total=total,
                                  breakdown=breakdown,
                                  year=datetime.now().year)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 