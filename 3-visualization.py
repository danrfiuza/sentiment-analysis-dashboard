import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from wordcloud import WordCloud
import plotly.express as px
import io
import base64
import os

# Sample data
df = pd.read_csv('https://raw.githubusercontent.com/danrfiuza/sentiment-analysis-dashboard/main/course_reviews_with_score.csv')

df['classification'] = df['roberta_classification'].apply(
    lambda x: 'Positive' if x == 1 else 'Negative' if x == -1 else 'Neutral')

# Calculate KPIs
total_reviews = len(df)
avg_rating = df['Label'].mean()
avg_sentiment = df['roberta_classification'].mean()
positive_count = (df['roberta_classification'] == 1).sum()
negative_count = (df['roberta_classification'] == -1).sum()
neutral_count = (df['roberta_classification'] == 0).sum()


def get_average_sentiment_percentage(df):
    total_reviews = len(df)
    positive_count = (df['roberta_classification'] == 1).sum()
    return (positive_count / total_reviews) * 100

# Generate word clouds


def generate_wordcloud(text):
    if text == '':
        return ''
    wordcloud = WordCloud(width=400, height=200,
                          background_color='white').generate(text)
    buffer = io.BytesIO()
    wordcloud.to_image().save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded_image}"


def get_text_for_sentiment(sentiment_value, df):
    if (len(df) == 0):
        return ''

    if sentiment_value == -1:
        return ' '.join(df[df['roberta_classification'] == -1]['translated_review_removed_stopwords'])
    elif sentiment_value == 0:
        return ' '.join(df[df['roberta_classification'] == 0]['translated_review_removed_stopwords'])
    else:
        return ' '.join(df[df['roberta_classification'] == 1]['translated_review_removed_stopwords'])


# Create a Dash app
external_script = ["https://tailwindcss.com/",
                   {"src": "https://cdn.tailwindcss.com"}]

app = dash.Dash(
    __name__,
    external_scripts=external_script,
)


@app.callback(
    [
        Output('rating_avg', 'children'),
        Output('total_reviews', 'children'),
        Output('gauge-chart', 'figure'),
        Output('negative_count', 'children'),
        Output('neutral_count', 'children'),
        Output('positive_count', 'children'),
        Output('wordcloud_negative', 'src'),
        Output('wordcloud_neutral', 'src'),
        Output('wordcloud_positive', 'src'),
        Output('data-table', 'data'),
    ],
    [Input('category-filter', 'value')]
)
def update_dashboard(selected_category):
    filtered_df = df[df['CourseId'] == selected_category]
    avg_sentiment = get_average_sentiment_percentage(filtered_df)
    average_value = filtered_df['Label'].mean()
    return [
        f"{average_value:.2f}",
        len(filtered_df),
        go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_sentiment,
            title={'text': "Average Sentiment"},
            number={'suffix': "%"},# Add percentage symbol
            gauge={
                'axis': {
                    'range': [0, 100],
                    'tickvals': [0, 50, 100],
                    'ticktext': ['Negative', 'Neutral', 'Positive']
                },
                'bar': {'color': "rgb(59, 130, 246)"},
                'steps': [
                    {'range': [0, 49.99], 'color': "red"},
                    {'range': [50, 50.01], 'color': "yellow"},
                    {'range': [50.01, 100], 'color': "green"}
                ]
            }
        )),
        (filtered_df['roberta_classification'] == -1).sum(),
        (filtered_df['roberta_classification'] == 0).sum(),
        (filtered_df['roberta_classification'] == 1).sum(),
        generate_wordcloud(get_text_for_sentiment(-1, filtered_df)),
        generate_wordcloud(get_text_for_sentiment(0, filtered_df)),
        generate_wordcloud(get_text_for_sentiment(1, filtered_df)),
        filtered_df.to_dict('records')
    ]


# Create Data Table
# Define columns
columns = [
    {'name': 'ID', 'id': 'ReviewID'},
    {'name': 'Review', 'id': 'Review'},
    {'name': 'Translated Review', 'id': 'translated_review'},
    {'name': 'Rating', 'id': 'Label'},
    {'name': 'Classification', 'id': 'classification'},
]
style_cell = {
    'textAlign': 'left',
    'overflow': 'visible',         # Allow content to overflow
    'textOverflow': 'clip',        # No ellipsis, show full text
    'whiteSpace': 'normal',        # Allow text to wrap
    'maxWidth': '200px',           # Set a maximum width if needed
    'padding': '10px',             # Add padding
    'overflowX': 'auto'
}
data_table = dash.dash_table.DataTable(
    id='data-table',
    data=df.to_dict('records'),
    columns=columns,
    page_size=5,
    style_cell=style_cell
)

app.layout = html.Div([
    html.H1("Sentiment Analysis Dashboard",
            className="text-4xl font-bold mb-8 text-center"),
    html.Div([
        dcc.Dropdown(
            id='category-filter',
            options=[{'label': i, 'value': i}
                     for i in df['CourseId'].unique()],
            value=df['CourseId'].unique()[0],
            # set callback to update the dashboard
            clearable=False,
            searchable=True,
            placeholder="Select a course",
        ),
    ], className='p-4 bg-gray-50 rounded-lg shadow-md w-full mb-5'),

    # KPIs
    html.Div([
        html.Div([
            html.Div([
                html.H3(
                    "Number of Reviews",
                    className="text-lg font-medium text-center"
                ),
                html.H1(
                    id='total_reviews',
                    className="text-6xl font-bold text-blue-500 text-center"
                )
            ], className='p-4 bg-gray-50 rounded-lg shadow-md text-center flex-1 flex  flex-col justify-center items-center w-full mb-4'),
            html.Div([
                html.H3("Rating Average", className="text-lg font-medium"),
                html.H1(
                    id='rating_avg',
                    className="text-6xl font-bold text-blue-500"
                )
            ], className='p-4 bg-gray-50 rounded-lg shadow-md text-center flex-1 flex  flex-col justify-center items-center w-full'),
        ], className='flex flex-col w-full mr-4'),
        html.Div([
            dcc.Graph(
                id='gauge-chart',
                figure=go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=avg_sentiment,
                    title={'text': "Average Sentiment"},
                    gauge={
                        'axis': {'range': [-1, 1]},
                        'steps': [
                            {'range': [-1, -0.33], 'color': "red",
                                'name': "Negative"},
                            {'range': [-0.33, 0.33],
                             'color': "yellow", 'name': "Neutral"},
                            {'range': [0.33, 1], 'color': "green",
                                'name': "Positive"}
                        ],
                        'bar': {'color': "darkblue"},
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': avg_sentiment
                        }
                    }
                )),
                className=""
            ),

        ], className='p-4 bg-gray-50 rounded-lg shadow-md text-center')
    ], className='flex justify-around mb-8'),

    # Classification Count
    html.Div([
        html.Div([
            html.H3(
                "Number of Negative Reviews",
                className="text-lg font-medium text-center"
            ),
            html.H1(
                id='negative_count',
                className="text-6xl font-bold text-blue-500 text-center"
            )
        ], className='bg-gray-50 p-4 shadow-md rounded-lg shadow-md w-full'),

        html.Div([
            html.H3(
                "Number of Neutral Reviews",
                className="text-lg font-medium text-center"
            ),
            html.H1(
                id='neutral_count',
                className="text-6xl font-bold text-blue-500 text-center"
            )
        ], className='bg-gray-50 p-4 shadow-md rounded-lg shadow-md w-full mx-4'),

        html.Div([
            html.H3(
                "Number of Positive Reviews",
                className="text-lg font-medium text-center"
            ),
            html.H1(
                id='positive_count',
                className="text-6xl font-bold text-blue-500 text-center"
            )
        ], className='bg-gray-50 p-4 shadow-md rounded-lg shadow-md w-full'),
    ], className='flex justify-around mb-8'),

    # Word Cloud Charts
    html.Div([
        html.Div([
            html.H3("Negative Reviews Word Cloud",
                    className="text-lg text-center font-medium mb-5"),
            html.Img(id='wordcloud_negative', className='w-full text-center')
        ], className='bg-gray-50 p-4 shadow-md rounded-lg shadow-md w-full'),

        html.Div([
            html.H3("Neutral Reviews Word Cloud",
                    className="text-lg text-center font-medium mb-5"),
            html.Img(id='wordcloud_neutral', className='w-full text-center')
        ], className='bg-gray-50 p-4 shadow-md rounded-lg shadow-md mx-4 w-full'),

        html.Div([
            html.H3("Positive Reviews Word Cloud",
                    className="text-lg text-centerfont-medium mb-5"),
            html.Img(id='wordcloud_positive', className='w-full text-center')
        ], className='bg-gray-50 p-4 shadow-md rounded-lg shadow-md w-full')
    ], className='flex justify-around mb-8'),

    # Table with comments
    html.Div([
        html.H3("Comments Table", className="text-lg font-medium mb-4"),
        data_table
    ], className='bg-gray-50 p-4 bg-gray-100 rounded-lg shadow-md w-full')
], className="container mx-auto p-8")

if __name__ == '__main__':
    app.run_server(port=8060, debug=True)
