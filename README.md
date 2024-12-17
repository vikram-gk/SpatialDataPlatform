
1)Clone the repository to your local machine using the following command: git clone repo_name

2)Create and Activate a Virtual Environment It's recommended to use a virtual environment to manage dependencies. Run the following commands to create and activate the virtual environment: 
For Windows:
 python -m venv venv
 venv\Scripts\activate
For macOS/Linux:
 python3 -m venv venv
 source venv/bin/activate

3)Install the Required Dependencies Once the virtual environment is activated, install the necessary dependencies using pip:

 pip install -r requirements.txt
Run the Application With the environment set up and dependencies installed, you can run the application:

4) Start the mongodb server

5)Run python main.py
This command will start the FastAPI application, which will be hosted locally.

Access the API Documentation FastAPI automatically generates interactive API documentation using Swagger. You can access it by navigating to:

 http://127.0.0.1:8000/docs
By appending /docs to the base URL, you will be redirected to the Swagger UI, where you can explore and interact with the API endpoints.
