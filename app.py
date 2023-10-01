from flask import Flask, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import time
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


UPLOAD_FOLDER = os.path.join('staticFiles', 'uploads')
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'This is your secret key to utilize session in Flask'

# Define the scope and credentials file path
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
credentials_path = 'E:\StackIt Project\CSV_Importer\credentials.json' 

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

            sheet = gc.open('Project CSV')  
           
            worksheet = sheet.get_worksheet(0)  

            worksheet.clear()

            # Read the CSV file
            uploaded_df = pd.read_csv(file_path, encoding='unicode_escape', low_memory=False, keep_default_na=False)

            # Clean and preprocess the data (adjust as needed)
            uploaded_df = uploaded_df.dropna(axis=1, how='all') # Replace NaN values with zeros
            print(uploaded_df)

            # Extract column names
            column_names = uploaded_df.columns.tolist()

            # Convert the DataFrame to a list of lists, including column names as the first row
            data_to_insert = [column_names] + uploaded_df.values.tolist()

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
        
@app.route('/apply_filters', methods=['POST', 'GET'])
def apply_filters():
    data_file_path = session.get('uploaded_data_file_path', None)
    uploaded_df = pd.read_csv(r"staticFiles\Updated_Dataset\New_Data.csv")
    uploaded_df = uploaded_df.dropna()
    
    # Extract Column Names
    col_names = uploaded_df.columns.values.tolist()
    print(col_names)

    if request.method == 'POST':

        # Retrieve filter criteria from the form
        column = request.form.get('column')
        condition = request.form.get('condition')
        filter_value = request.form.get('value')
        print(f"Column: {column}, Condition: {condition}, Filter Value: {filter_value}")

        # Apply the selected filter
        if condition == 'equals':
            if uploaded_df[column].dtype == 'object':
                filtered_df = uploaded_df[uploaded_df[column].astype(str) == filter_value]
            elif uploaded_df[column].dtype in ['int64', 'float64']:
                filtered_df = uploaded_df[uploaded_df[column] == int(filter_value)]  # Assuming filter_value is an integer
            else:
                # Handle other non-string columns here
                filtered_df = uploaded_df
        elif condition == 'contains':
            if uploaded_df[column].dtype == 'object':
                filtered_df = uploaded_df[uploaded_df[column].str.contains(filter_value, case=False)]
            elif uploaded_df[column].dtype in ['int64', 'float64']:
                # Handle numeric columns separately if needed
                filtered_df = uploaded_df
            else:
                # Handle other non-string columns here
                filtered_df = uploaded_df
        else:
            # Handle other filter conditions as needed
            filtered_df = uploaded_df
 
        filtered_csv_filename = f"Filtered_Data.csv"

        # Define the path for the new CSV file
        filtered_csv_path = os.path.join(os.getcwd(), r"staticFiles\Updated_Dataset", filtered_csv_filename)

        # Save the filtered DataFrame to the new CSV file
        filtered_df.to_csv(filtered_csv_path, index=False)

        # Convert the filtered DataFrame to a list of dictionaries
        filtered_data = filtered_df.to_dict('records')


        print(filtered_df)

        return render_template('filtered_data1.html', col_names=col_names, filtered_data=filtered_data)

    return render_template('filtered_data2.html', col_names=col_names)

@app.route('/apply_column_selection', methods=['POST', 'GET'])
def apply_column_selection():
    data_file_path = session.get('uploaded_data_file_path', None)
    uploaded_df = pd.read_csv(data_file_path, encoding='unicode_escape')

    # Extract Column Names
    col_names = uploaded_df.columns.values.tolist()

    if request.method == 'POST':
        # Retrieve selected columns for display
        selected_columns = request.form.getlist('display_columns')

        # Check if the form was submitted with selected columns
        if selected_columns:
            # Filter the DataFrame to include only the selected columns
            filtered_df = uploaded_df[selected_columns]
            
            filtered_csv_filename = f"New_Data.csv"

            # # Define the path for the new CSV file
            filtered_csv_path = os.path.join(os.getcwd(), r"staticFiles\Updated_Dataset", filtered_csv_filename)

            # # Save the filtered DataFrame to the new CSV file
            filtered_df.to_csv(filtered_csv_path, index=False)

            # Convert the DataFrame to a list of dictionaries
            data = filtered_df.to_dict('records')

            return render_template('selection2.html', col_names=col_names, selected_columns=selected_columns, data=data)

    return render_template('selection1.html', col_names=col_names)


@app.route('/finalUpload', methods=['GET', 'POST'])
def finalUpload():
    if request.method == 'POST':
        # Replace the file path with the path to your CSV file
        file_path = r'staticFiles\Updated_Dataset\Filtered_Data.csv'
        
        # Check if the file has an allowed extension (not needed in this case)
        session['uploaded_data_file_path'] = file_path

        # Now, also write the data to Google Sheets
        sheet = gc.open('Project CSV')  
           
        worksheet = sheet.get_worksheet(0)  

        worksheet.clear()

        # Read the CSV file
        uploaded_df = pd.read_csv(file_path, encoding='unicode_escape', low_memory=False, keep_default_na=False)

        # Clean and preprocess the data 
        uploaded_df = uploaded_df.dropna(axis=1, how='all') 
        print(uploaded_df)

        # Extract column names
        column_names = uploaded_df.columns.tolist()

        # Convert the DataFrame to a list of lists, including column names as the first row
        data_to_insert = [column_names] + uploaded_df.values.tolist()

        worksheet.insert_rows(data_to_insert)

        return render_template('filtered_data2.html')

    return render_template("filtered_data1.html")



if __name__ == '__main__':
    app.run(debug=True)
