# SmartRes – Operating System Resource Management Simulator

SmartRes is an interactive, Python-based simulation platform designed to demonstrate key Operating System concepts, including process management, resource allocation, deadlock avoidance, and CPU scheduling.

The project provides a visual environment where users can configure processes and system resources, observe resource-allocation decisions, and compare CPU scheduling algorithms through performance metrics, Gantt charts, and step-by-step execution playback.

## Features

### 1. Process Management
- Create and manage processes.
- Configure process details and resource requirements.
- Maintain process information using persistent database storage.

### 2. Resource Management
- Configure and monitor available system resources.
- Track resource allocation and availability.
- Manage resource-allocation information.

### 3. Deadlock Avoidance and Resource Requests
- Implements the Banker's Algorithm for deadlock avoidance.
- Evaluates system safety before granting resource requests.
- Provides safety-status information to help understand allocation decisions.

### 4. Event History
- Maintains a record of important system events.
- Allows users to inspect resource requests and management activities.

### 5. CPU Scheduling Lab

Implements six CPU scheduling algorithms:

- First Come First Serve (FCFS)
- Shortest Job First (SJF) – Non-preemptive
- Shortest Remaining Time First (SRTF) – Preemptive
- Priority Scheduling – Non-preemptive
- Preemptive Priority Scheduling
- Round Robin (RR)

The scheduling lab provides:
- Comparative performance metrics, including average waiting time and turnaround time.
- CPU utilisation and throughput calculations.
- Gantt chart visualisations.
- Step-by-step execution playback.
- Process-state information and scheduling-decision explanations.

All six algorithms can be evaluated using a common configured workload.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic and algorithms |
| Streamlit | Interactive web application |
| SQLite | Persistent application database |
| Plotly | Scheduling visualisations |
| Pandas | Data handling |
| Oracle 11g SQL | Separate DBMS schema and reporting deliverable |
| Pytest | Automated testing |

## Project Structure

```text
SmartRes/
│
├── app.py
├── core/
│   └── cpu_scheduler.py
│
├── database/
│   ├── schema_oracle11g.sql
│   └── oracle_reports.sql
│
├── tests/
│   └── test_cpu_scheduler.py
│
├── requirements.txt
└── README.md
```

*Note: The structure above highlights the principal project files and may omit additional modules.*

## Installation and Setup

### Prerequisites
- Python installed on your system.
- Git (optional, for cloning the repository).

### 1. Clone the repository

```bash
git clone https://github.com/RatneshkumarPathak/SmartRes.git
cd SmartRes
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

## Running Tests

Run the automated tests using:

```bash
python -m pytest -q
```

## Database Information

The running application uses SQLite for persistent application data.

The project also includes a separate Oracle 11g DBMS deliverable containing database schema definitions and SQL reports. The Oracle scripts are maintained separately and are not currently integrated with the live Streamlit application's SQLite database.

## Project Scope

SmartRes is an educational simulation platform. It demonstrates operating-system resource-management and CPU scheduling concepts through software models and interactive visualisations.

It does not directly manage physical CPU resources, operating-system processes, or hardware resources on the host computer.

## Future Improvements

Potential future improvements include:
- Better integration between process management and CPU scheduling.
- More comprehensive process-state transitions.
- Expanded validation and testing.
- Additional visual explanations of resource-allocation decisions.

## Author

**Ratnesh Kumar Pathak**

B.Tech – Computer Science and Engineering

GitHub: [RatneshkumarPathak](https://github.com/RatneshkumarPathak)