🌱 Crop Yield Data Storage and Management Solution
AWS Capstone Project

A full-stack agricultural data management web application developed using Flask, HTML, CSS, and JavaScript.  
This project is being built **from scratch** following clean architecture, cloud-ready practices, and industry standards.  
Cloud deployment and AWS services will be integrated in later phases.

---

📌 Project Overview

The Crop Yield Data Storage and Management Solution aims to modernize traditional agricultural record-keeping by providing farmers and administrators with a secure, structured, and easy-to-use web platform.

Farmers can log seasonal crop yield data, track farm performance, and manage records digitally, while administrators can monitor users and data centrally through an admin dashboard.

---

✨ Key Features

👨‍🌾 Farmer Module
- Farmer Registration
- Farmer Login / Logout
- Secure session-based authentication
- Farmer Dashboard
- Add crop yield records:
  - Crop Name
  - Season
  - Cultivated Area
  - Total Yield
- View previously logged yield data
- Clean and responsive UI

🛠️ Admin Module
- Admin Registration
- Admin Login / Logout
- Admin Dashboard
- View all registered users
- View all crop yield records
- Role-based access separation (Farmer / Admin)

---

🧑‍💻 Tech Stack

| Layer            | Technology                           |
|------------------|--------------------------------------|
| Backend          | Flask (Python)                       |
| Frontend         | HTML5, CSS3, JavaScript              |
| Styling          | Custom CSS (Agriculture Theme)       |
| Sessions         | Flask Sessions                       |
| Version Control  | Git & GitHub                         |
| Cloud (Planned)  | AWS EC2, DynamoDB, SNS, IAM          |

---

📂 Project Structure

CropYield-AWS-Capstone/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── templates/
│   ├── layout.html
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   └── admin_dashboard.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
│
└── venv/ (ignored in Git)

---

🔐 Authentication Flow

- Users can sign up and log in as Farmers
- Admins have a separate authentication portal
- Flask sessions are used to manage login state
- Role-based redirection ensures secure access

---

🎯 Objectives of the Project

- Build a real-world agricultural data management system
- Implement clean Flask routing and template inheritance
- Design a professional UI without frontend frameworks
- Follow scalable and maintainable project structure
- Prepare the application for cloud deployment on AWS

---

☁️ AWS Deployment Plan (Upcoming)

- Deploy Flask application on AWS EC2
- Configure IAM roles for secure service access
- Integrate Amazon DynamoDB for data storage
- Implement Amazon SNS for email notifications
- Production setup using Gunicorn and Nginx

---

🔮 Future Enhancements

- Advanced admin analytics dashboard
- Crop yield insights & trends
- Harvest reminder notifications
- Role-based access using IAM
- EC2 + Nginx + Gunicorn deployment
- Full cloud-native architecture

---

👤 Author

Prashant Rai  
🎓 B.Tech CSE (AI)  
📍 India  
🔗 GitHub: https://github.com/prashant-rai99
