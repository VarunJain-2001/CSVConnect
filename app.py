from flask import Flask, request, render_template, session
from werkzeug.utils import secure_filename
import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

UPLOAD_FOLDER = os.path.join('staticFiles', 'uploads')
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'This is your secret key to utilize session in Flask'

# Define the scope and credentials file path
# scope = ['https://www.googleapis.com/auth/spreadsheets']
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
# scope = ['https://www.googleapis.com/auth/spreadsheets']
credentials_path = 'E:\StackIt Project\CSV_Importer\credentials.json'  # Update with your credentials file path

# Authenticate with Google Sheets API
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
gc = gspread.authorize(credentials)

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def uploadFile():
    if request.method == 'POST':
        # Check if a file is uploaded
        if 'file' not in request.files:
            return render_template("index.html", error="No file part")
        
        f = request.files['file']

        # Check if the file has an allowed extension
        if f and allowed_file(f.filename):
            # Create the upload folder if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            # Extracting uploaded file name
            data_filename = secure_filename(f.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], data_filename)

            f.save(file_path)

            session['uploaded_data_file_path'] = file_path

            # Now, also write the data to Google Sheets
            sheet = gc.open('Project CSV')  # Replace with your Google Sheet name
           
            worksheet = sheet.get_worksheet(0)  # Use the first worksheet (index 0) or specify the desired worksheet

            worksheet.clear()

            # Read the CSV file
            uploaded_df = pd.read_csv(file_path,low_memory=False)

            # Clean and preprocess the data (adjust as needed)
            uploaded_df = uploaded_df.dropna(axis=1,how='all') # Replace NaN values with zeros
            print(uploaded_df)

            # Convert the DataFrame to a list of lists
            data_to_insert = uploaded_df.values.tolist()


            worksheet.insert_rows(data_to_insert)

            return render_template('index2.html')
        else:
            return render_template("index.html", error="Invalid file format. Allowed formats: .csv")

    return render_template("index.html")

@app.route('/show_data')
def showData():
    # Uploaded File Path
    data_file_path = session.get('uploaded_data_file_path', None)
    if data_file_path:
        # Read the CSV file
        uploaded_df = pd.read_csv(data_file_path, encoding='unicode_escape')

        # Convert the DataFrame to HTML Table
        uploaded_df_html = uploaded_df.to_html()

        return render_template('show_csv_data.html', data_var=uploaded_df_html)
    else:
        return render_template('show_csv_data.html', data_var="No data available")

if __name__ == '__main__':
    app.run(debug=True)
