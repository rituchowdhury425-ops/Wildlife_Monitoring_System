
# Wildlife Monitoring System 🐾

A Python Flask-based web application designed to demonstrate wildlife image classification, user authentication, detection history, and a sample GPS-based wildlife map.

## Features

- User registration and login
- Image upload and preview
- Image classification using a pretrained ResNet-50 model
- Detection results with confidence scores
- Detection history with pagination
- Demonstration wildlife map using Leaflet
- SQLite database integration

## Technologies Used

- Python
- Flask
- HTML5
- CSS3
- SQLite
- Hugging Face Transformers
- ResNet-50
- Leaflet.js

## Project Structure

```text
Wildlife_Monitoring_System/
│
├── app.py
├── auth.py
├── check_database.py
├── upgrade_database.py
├── .gitignore
│
├── static/
│   └── style.css
│
└── templates/
    ├── index.html
    ├── history.html
    ├── login.html
    └── register.html
```

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/rituchowdhury425-ops/Wildlife_Monitoring_System.git
```

2. Open the project folder:

```bash
cd Wildlife_Monitoring_System
```

3. Create a virtual environment:

```bash
python -m venv venv
```

4. Activate it on Windows:

```bash
venv\Scripts\activate
```

5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Initialize the database using the project's setup scripts, if required.

7. Run the application:

```bash
python app.py
```

8. Open in your browser:

```text
http://127.0.0.1:5000
```

## Important Notes

- The image classification uses a pretrained general-purpose ResNet-50 model. It is not a custom-trained wildlife detection model.
- The GPS map displays demonstration coordinates, not live animal tracking.
- This project is an academic prototype.

## Author

**Ritu Chowdhury**

GitHub: https://github.com/rituchowdhury425-ops

LinkedIn: https://www.linkedin.com/in/ritu-chowdhury-792883413/
