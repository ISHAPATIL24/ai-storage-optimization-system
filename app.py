import pandas as pd
import os
import plotly.express as px
from flask import Flask, render_template, request
import joblib
app = Flask(__name__)
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)
rf = joblib.load(
    os.path.join(
        BASE_DIR,
        'storage_tier_model.joblib'
    )
)
df = pd.read_csv(
    os.path.join(
        BASE_DIR,
        'storage_dataset.csv'
    )
)
total_files = len(df)
cold_files = len(
    df[df['storage_tier'] == 'Cold']
)
total_storage_mb = df['file_size_mb'].sum()

storage_tb = round(
    total_storage_mb / (1024 * 1024),
    2
)

tier_counts = (
    df['storage_tier']
    .value_counts()
    .reset_index()
)

tier_counts.columns = [
    'Storage Tier',
    'Count'
]

fig = px.pie(
    tier_counts,
    names='Storage Tier',
    values='Count',
    title='Storage Tier Distribution'
)

storage_chart = fig.to_html(
    full_html=False
)




monthly_savings = (
    df['file_size_mb'] * 0.08
).sum()

monthly_savings = round(
    monthly_savings,
    2
)

cost_data = pd.DataFrame({

    'Category': [
        'Current Cost',
        'Optimized Cost'
    ],

    'Amount': [
        monthly_savings / 0.8,
        (monthly_savings / 0.8) - monthly_savings
    ]

})

cost_fig = px.bar(
    cost_data,
    x='Category',
    y='Amount',
    title='Cost Analysis'
)
cost_chart = cost_fig.to_html(
    full_html=False
)
df['priority_score'] = (
    df['file_size_mb']
    * df['days_since_last_access']
) / (
    df['access_frequency'] + 1
)
archive_candidates = (
    df[df['storage_tier'] == 'Cold']
    .sort_values(
        by='priority_score',
        ascending=False
    )
    .head(5)
)

@app.route('/')
def home():

    return render_template(
    'index.html',
    total_files=total_files,
    cold_files=cold_files,
    storage_tb=storage_tb,
    monthly_savings=monthly_savings,
    storage_chart=storage_chart,
    cost_chart=cost_chart,
    archive_candidates=archive_candidates
)
def predict_storage_tier(
    file_size,
    access_frequency,
    days_since_last_access
):

    prediction = rf.predict([[
        file_size,
        access_frequency,
        days_since_last_access
    ]])

    return prediction[0]
def get_recommendation(
    tier,
    file_size,
    access_frequency,
    days
):

    priority_score = (
        file_size * days
    ) / (access_frequency + 1)

    if tier == "Hot":
        recommendation = "Keep in Premium Storage"

    elif tier == "Warm":
        recommendation = "Keep in Standard Storage"

    else:

        if priority_score > 50000:
            recommendation = "Archive Immediately"

        else:
            recommendation = "Archive When Possible"

    return recommendation


def analyze_file(
    file_size,
    access_frequency,
    days_since_last_access
):

    tier = predict_storage_tier(
        file_size,
        access_frequency,
        days_since_last_access
    )

    recommendation = get_recommendation(
        tier,
        file_size,
        access_frequency,
        days_since_last_access
    )

    monthly_savings = file_size * (0.10 - 0.02)

    return {
        "Storage Tier": tier,
        "Recommendation": recommendation,
        "Estimated Monthly Savings": monthly_savings
    }

@app.route('/predict', methods=['POST'])
def predict():

    file_size = int(
        request.form['file_size']
    )

    access_frequency = int(
        request.form['access_frequency']
    )

    days_since_last_access = int(
        request.form['days_since_last_access']
    )

    result = analyze_file(
        file_size,
        access_frequency,
        days_since_last_access
    )

    return render_template(
    'result.html',
    result=result
)

if __name__ == '__main__':
    app.run(debug=True)