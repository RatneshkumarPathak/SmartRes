
import streamlit as st
import pandas as pd
from core.cpu_scheduler import (
    fcfs,
    preemptive_priority,
    priority_scheduling,
    round_robin,
    sjf,
    srtf,
)
from database.db import (
    init_db,
    get_resources,
    get_processes,
    get_allocations,
    get_events,
    add_resource,
    update_resource_total,
    add_process,
    request_resources,
    terminate_process,
    get_safety_status,
)

st.set_page_config(
    page_title="SmartRes | OS Resource Manager",
    page_icon="⚙️",
    layout="wide",
)

init_db()

st.title("⚙️ SmartRes")
st.caption("Smart Operating System Resource Management System")
st.write(
    "Simulate processes, manage system resources, and evaluate resource "
    "requests using Banker’s Algorithm."
)

resources = get_resources()
processes = get_processes()
allocations = get_allocations()
active_processes = [p for p in processes if p["status"] == "Active"]

try:
    safety = get_safety_status()
except Exception as exc:
    safety = {"safe": False, "sequence": [], "available": []}
    st.error(f"Unable to evaluate system safety: {exc}")

allocated_by_resource = {
    r["id"]: sum(
        row["allocated"]
        for row in allocations
        if row["resource_id"] == r["id"]
    )
    for r in resources
}

available_by_resource = {
    r["id"]: r["total"] - allocated_by_resource[r["id"]]
    for r in resources
}

c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Processes", len(active_processes))
c2.metric("Resource Types", len(resources))
c3.metric(
    "Total Units",
    sum(r["total"] for r in resources),
)
c4.metric(
    "System State",
    "SAFE" if safety["safe"] else "UNSAFE",
)

st.divider()

overview, process_tab, resource_tab, request_tab, history_tab , cpu_tab, sim_tab= st.tabs(
    [
        "Overview",
        "Process Management",
        "Resource Management",
        "Resource Requests",
        "Event History",
        "CPU Scheduling",
        "Execution Simulator",
    ]
)


with overview:

    # 2. Resource utilisation
    st.subheader("Resource Utilisation")
    st.caption(
        "The bars show how much of each resource's total capacity "
        "is currently allocated to active processes."
    )

    if resources:
        for resource in resources:
            resource_id = resource["id"]
            total = resource["total"]
            allocated = allocated_by_resource[resource_id]
            available = available_by_resource[resource_id]

            utilisation = (
                allocated / total if total > 0 else 0
            )

            st.write(f"**{resource['name']}**")

            col1, col2 = st.columns([4, 1])

            with col1:
                st.progress(
                    min(max(utilisation, 0.0), 1.0),
                    text=f"{utilisation * 100:.1f}% utilised"
                )

            with col2:
                st.metric(
                    "Available",
                    f"{available}/{total}"
                )

            st.caption(
                f"{allocated} allocated · "
                f"{available} available · "
                f"{total} total units"
            )
    else:
        st.info("Add resources to start monitoring utilisation.")

    st.divider()

    # 3. Process monitoring
    st.subheader("Process Monitoring")

    if processes:
        process_summary = []

        for process in processes:
            process_allocations = [
                row for row in allocations
                if row["process_id"] == process["id"]
            ]

            total_allocated = sum(
                row["allocated"] for row in process_allocations
            )

            total_need = sum(
                row["need"] for row in process_allocations
            )

            process_summary.append({
                "Process ID": f"P{process['id']}",
                "Name": process["name"],
                "Status": process["status"],
                "Allocated Units": total_allocated,
                "Remaining Need": total_need,
                "Created At": process["created_at"],
            })

        st.dataframe(
            pd.DataFrame(process_summary),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Allocated Units = resources currently held by a process. "
            "Remaining Need = additional units it may still require."
        )
    else:
        st.info("No processes have been created yet.")

    st.divider()

    # 4. Banker’s Algorithm safety status
    st.subheader("System Safety Analysis")

    if safety["safe"]:
        st.success(
            "SAFE STATE: The system currently has at least one "
            "safe execution sequence."
        )

        if safety["sequence"]:
            sequence_text = " → ".join(
                f"P{process_id}" for process_id in safety["sequence"]
            )

            st.markdown(f"**Safe execution sequence:** {sequence_text}")

            st.info(
                "A safe sequence means processes can finish one by one "
                "using currently available resources and resources "
                "released by previously completed processes."
            )
        else:
            st.info(
                "There are no active processes to execute. "
                "The empty system is considered safe."
            )
    else:
        st.error(
            "UNSAFE STATE: No safe execution sequence exists "
            "for the current resource allocation."
        )

        st.warning(
            "An unsafe state does not necessarily mean deadlock "
            "has already occurred. It means the system cannot "
            "guarantee that all active processes can finish."
        )

    st.divider()

    # 5. Detailed allocation matrix
    st.subheader("Allocation and Remaining Need Matrix")

    if allocations:
        matrix = pd.DataFrame(allocations)

        st.dataframe(
            matrix,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Max Claim = maximum declared requirement. "
            "Allocation = units currently held. "
            "Need = Max Claim − Allocation."
        )
    else:
        st.info(
            "Create processes to populate the allocation matrix."
        )

    st.divider()

    # 6. Recent activity
    st.subheader("Recent System Activity")

    recent_events = get_events(limit=5)

    if recent_events:
        st.dataframe(
            pd.DataFrame(recent_events),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No system events have been recorded yet.")


with resource_tab:
    st.subheader("Add a Resource Type")

    with st.form("add_resource_form", clear_on_submit=True):
        resource_name = st.text_input(
            "Resource name", placeholder="e.g. Printer"
        )
        resource_total = st.number_input(
            "Total available units", min_value=0, value=3, step=1
        )
        add_resource_button = st.form_submit_button("Add Resource")

    if add_resource_button:
        try:
            add_resource(resource_name, int(resource_total))
            st.success(f"Resource '{resource_name}' added.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not add resource: {exc}")

    if resources:
        st.subheader("Existing Resources")
        st.dataframe(
            pd.DataFrame([
                {
                    "ID": r["id"],
                    "Resource": r["name"],
                    "Total": r["total"],
                    "Allocated": allocated_by_resource[r["id"]],
                    "Available": available_by_resource[r["id"]],
                }
                for r in resources
            ]),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Update Resource Capacity")
        with st.form("update_resource_form"):
            selected_resource = st.selectbox(
                "Resource",
                resources,
                format_func=lambda r: f"{r['name']} (ID {r['id']})",
            )
            new_total = st.number_input(
                "New total capacity",
                min_value=0,
                value=int(selected_resource["total"]),
                step=1,
                key="new_capacity",
            )
            update_button = st.form_submit_button("Update Capacity")

        if update_button:
            try:
                update_resource_total(
                    selected_resource["id"], int(new_total)
                )
                st.success("Resource capacity updated.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not update resource: {exc}")

with process_tab:
    st.subheader("Create a Process")

    if not resources:
        st.info("Create at least one resource type first.")
    else:
        with st.form("add_process_form", clear_on_submit=True):
            process_name = st.text_input(
                "Process name", placeholder="e.g. Compiler"
            )
            st.write("Declare the maximum resource requirement for this process.")
            maximum_claims = {}

            for resource in resources:
                maximum_claims[resource["id"]] = st.number_input(
                    f"Maximum {resource['name']} units",
                    min_value=0,
                    max_value=int(resource["total"]),
                    value=0,
                    step=1,
                    key=f"claim_{resource['id']}",
                )

            create_process_button = st.form_submit_button("Create Process")

        if create_process_button:
            try:
                add_process(
                    process_name,
                    {
                        key: int(value)
                        for key, value in maximum_claims.items()
                    },
                )
                st.success(f"Process '{process_name}' created.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not create process: {exc}")

    if processes:
        st.subheader("Process Register")
        st.dataframe(
            pd.DataFrame(processes),
            use_container_width=True,
            hide_index=True,
        )

    if active_processes:
        st.subheader("Terminate a Process")
        with st.form("terminate_process_form"):
            process_to_terminate = st.selectbox(
                "Select process",
                active_processes,
                format_func=lambda p: f"P{p['id']} — {p['name']}",
            )
            terminate_button = st.form_submit_button("Terminate and Release Resources")

        if terminate_button:
            try:
                terminate_process(process_to_terminate["id"])
                st.success("Process terminated and its resources released.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not terminate process: {exc}")

with request_tab:
    st.subheader("Request Resources")

    if not active_processes or not resources:
        st.info("Create at least one resource and one active process first.")
    else:
        with st.form("request_form"):
            selected_process = st.selectbox(
                "Requesting process",
                active_processes,
                format_func=lambda p: f"P{p['id']} — {p['name']}",
            )
            selected_resource = st.selectbox(
                "Requested resource",
                resources,
                format_func=lambda r: r["name"],
            )
            request_amount = st.number_input(
                "Units requested", min_value=1, value=1, step=1
            )
            request_button = st.form_submit_button("Evaluate and Request")

        if request_button:
            try:
                approved, reason, sequence = request_resources(
                    selected_process["id"],
                    selected_resource["id"],
                    int(request_amount),
                )

                if approved:
                    st.success(reason)
                    st.write(
                        "Safe sequence: "
                        + " → ".join(f"P{i}" for i in sequence)
                    )
                else:
                    st.error(reason)

                st.rerun()
            except Exception as exc:
                st.error(f"Request could not be processed: {exc}")

with history_tab:
    st.subheader("Persistent Event History")
    events = get_events()

    if events:
        st.dataframe(
            pd.DataFrame(events),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No events recorded yet.")



with cpu_tab:
    st.subheader("CPU Scheduling Comparison Lab")

    st.write(
        "Run six CPU scheduling algorithms on the same workload and compare "
        "their execution order, waiting time, turnaround time, and CPU utilisation."
    )
    st.info(
        "All algorithms receive identical arrival times, burst times, and priorities. "
        "A smaller priority number means a higher priority. Algorithms that do not "
        "use priority simply ignore that input."
    )

    count = st.number_input(
        "Number of processes",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        key="comparison_process_count",
    )

    scheduling_processes = []
    st.markdown("### Workload Configuration")
    st.caption(
        "Arrival Time: when a process enters the ready queue. "
        "Burst Time: total CPU time required. Priority: smaller number = higher priority."
    )

    for i in range(int(count)):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            pid = st.text_input(
                f"Process ID {i + 1}",
                value=f"P{i + 1}",
                key=f"comparison_pid_{i}",
            )
        with c2:
            arrival = st.number_input(
                f"Arrival Time {i + 1}",
                min_value=0,
                value=0,
                step=1,
                key=f"comparison_arrival_{i}",
            )
        with c3:
            burst = st.number_input(
                f"Burst Time {i + 1}",
                min_value=1,
                value=3,
                step=1,
                key=f"comparison_burst_{i}",
            )
        with c4:
            priority = st.number_input(
                f"Priority {i + 1}",
                min_value=0,
                value=1,
                step=1,
                key=f"comparison_priority_{i}",
                help="Lower number means higher priority.",
            )

        scheduling_processes.append({
            "pid": pid.strip(),
            "arrival": int(arrival),
            "burst": int(burst),
            "priority": int(priority),
        })

    quantum = st.number_input(
        "Round Robin Time Quantum",
        min_value=1,
        value=2,
        step=1,
        key="comparison_quantum",
        help="Maximum CPU time a process can use in one turn before returning to the ready queue.",
    )

    if st.button(
        "Compare All Six Algorithms",
        type="primary",
        use_container_width=True,
    ):
        ids = [p["pid"] for p in scheduling_processes]

        if any(not pid for pid in ids):
            st.error("Process IDs cannot be empty.")
        elif len(ids) != len(set(ids)):
            st.error("Every process must have a unique ID.")
        else:
            algorithms = {
                "FCFS": lambda: fcfs(scheduling_processes),
                "SJF": lambda: sjf(scheduling_processes),
                "SRTF": lambda: srtf(scheduling_processes),
                "Priority": lambda: priority_scheduling(scheduling_processes),
                "Preemptive Priority": lambda: preemptive_priority(scheduling_processes),
                "Round Robin": lambda: round_robin(scheduling_processes, int(quantum)),
            }

            try:
                algorithm_outputs = {
                    name: run() for name, run in algorithms.items()
                }
            except ValueError as exc:
                st.error(f"Invalid scheduling input: {exc}")
                algorithm_outputs = {}

            if algorithm_outputs:
                total_burst = sum(p["burst"] for p in scheduling_processes)

                def calculate_metrics(results):
                    makespan = max(p["completion"] for p in results)
                    average_waiting = sum(p["waiting"] for p in results) / len(results)
                    average_turnaround = sum(
                        p["turnaround"] for p in results
                    ) / len(results)
                    return {
                        "Average Waiting Time": average_waiting,
                        "Average Turnaround Time": average_turnaround,
                        "CPU Utilisation (%)": (
                            total_burst / makespan * 100 if makespan else 0
                        ),
                        "Throughput (processes/unit time)": (
                            len(results) / makespan if makespan else 0
                        ),
                        "Total Completion Time": makespan,
                    }

                metrics = {
                    name: calculate_metrics(output[0])
                    for name, output in algorithm_outputs.items()
                }

                st.session_state["scheduling_comparison"] = {
                    "processes": scheduling_processes,
                    "quantum": int(quantum),
                    "outputs": algorithm_outputs,
                    "metrics": metrics,
                }

    # Keep the last comparison visible when another widget causes a rerun.
    if "scheduling_comparison" in st.session_state:
        comparison_data = st.session_state["scheduling_comparison"]
        outputs = comparison_data["outputs"]
        metrics = comparison_data["metrics"]

        st.divider()
        st.markdown("## Performance Comparison")

        metric_rows = []
        for metric_name in next(iter(metrics.values())):
            row = {"Metric": metric_name}
            for algorithm_name in metrics:
                row[algorithm_name] = round(
                    metrics[algorithm_name][metric_name], 2
                )
            metric_rows.append(row)

        st.dataframe(
            pd.DataFrame(metric_rows),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "CPU utilisation = total useful CPU burst time ÷ elapsed time "
            "from time 0 to the final completion. Throughput = completed "
            "processes ÷ that elapsed time. Context-switch overhead is not modelled."
        )

        st.divider()
        st.markdown("## Gantt Chart Comparison")

        import plotly.graph_objects as go

        def create_gantt(timeline, title):
            fig = go.Figure()
            for event in timeline:
                start = event["start"]
                finish = event["finish"]
                pid = str(event["pid"])
                fig.add_trace(
                    go.Bar(
                        x=[finish - start],
                        y=[pid],
                        base=[start],
                        orientation="h",
                        name=pid,
                        hovertemplate=(
                            "Process: " + pid
                            + "<br>Start: %{base}"
                            + "<br>Duration: %{x}"
                            + "<extra></extra>"
                        ),
                    )
                )

            makespan = max(event["finish"] for event in timeline)
            fig.update_layout(
                title=title,
                xaxis_title="CPU Time",
                yaxis_title="Process",
                barmode="overlay",
                showlegend=False,
                xaxis=dict(range=[0, makespan], dtick=1, zeroline=True),
                height=300,
                margin=dict(l=20, r=20, t=45, b=35),
            )
            return fig

        algorithm_names = list(outputs.keys())
        for row_start in range(0, len(algorithm_names), 2):
            left, right = st.columns(2)
            for column, algorithm_name in zip(
                (left, right), algorithm_names[row_start:row_start + 2]
            ):
                with column:
                    st.plotly_chart(
                        create_gantt(
                            outputs[algorithm_name][1],
                            f"{algorithm_name} Timeline",
                        ),
                        use_container_width=True,
                    )

        st.divider()
        st.markdown("## Process-wise Results")
        for algorithm_name, (results, _) in outputs.items():
            with st.expander(f"{algorithm_name} — process metrics"):
                st.dataframe(
                    pd.DataFrame(results),
                    use_container_width=True,
                    hide_index=True,
                )

        st.divider()
        st.markdown("## What Each Algorithm Does")

        explanations = {
            "FCFS": (
                "Runs processes in arrival order. It is simple and non-preemptive, "
                "but a long process at the front can make short processes wait."
            ),
            "SJF": (
                "Among processes that have already arrived, chooses the one with "
                "the shortest full CPU burst. It is non-preemptive; a running job "
                "is not interrupted."
            ),
            "SRTF": (
                "Chooses the ready process with the smallest remaining CPU time. "
                "A newly arrived shorter job can preempt the current process."
            ),
            "Priority": (
                "Chooses the ready process with the highest priority (smallest "
                "priority number). It is non-preemptive."
            ),
            "Preemptive Priority": (
                "Runs the highest-priority ready process and interrupts the current "
                "process when a higher-priority process arrives."
            ),
            "Round Robin": (
                f"Gives each ready process up to {comparison_data['quantum']} CPU "
                "time units per turn. An unfinished process goes to the back of "
                "the ready queue, improving sharing and responsiveness."
            ),
        }

        for algorithm_name, explanation in explanations.items():
            st.markdown(f"**{algorithm_name}:** {explanation}")

        st.warning(
            "Priority scheduling can cause starvation for low-priority processes. "
            "SJF/SRTF depend on knowing or estimating CPU burst lengths. "
            "Round Robin's behaviour depends strongly on its time quantum."
        )


with sim_tab:
    st.subheader("OS Process Execution Simulator")

    st.write(
        "Follow CPU execution one segment at a time. Observe how processes "
        "arrive, wait, execute, get preempted, and complete."
    )
    st.info(
        "This is a scheduling simulation, not execution of real operating-system "
        "processes. Smaller priority numbers represent higher priority."
    )

    sim_count = st.number_input(
        "Number of processes",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        key="sim_process_count",
    )

    sim_processes = []
    st.markdown("### Process Configuration")

    for i in range(int(sim_count)):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            sim_pid = st.text_input(
                f"Process ID {i + 1}",
                value=f"P{i + 1}",
                key=f"sim_pid_{i}",
            )
        with c2:
            sim_arrival = st.number_input(
                f"Arrival Time {i + 1}",
                min_value=0,
                value=0,
                step=1,
                key=f"sim_arrival_{i}",
            )
        with c3:
            sim_burst = st.number_input(
                f"Burst Time {i + 1}",
                min_value=1,
                value=3,
                step=1,
                key=f"sim_burst_{i}",
            )
        with c4:
            sim_priority = st.number_input(
                f"Priority {i + 1}",
                min_value=0,
                value=1,
                step=1,
                key=f"sim_priority_{i}",
                help="Lower number means higher priority.",
            )

        sim_processes.append({
            "pid": sim_pid.strip(),
            "arrival": int(sim_arrival),
            "burst": int(sim_burst),
            "priority": int(sim_priority),
        })

    algorithm_functions = {
        "FCFS": fcfs,
        "SJF": sjf,
        "SRTF": srtf,
        "Priority": priority_scheduling,
        "Preemptive Priority": preemptive_priority,
        "Round Robin": round_robin,
    }

    sim_algorithm = st.selectbox(
        "Scheduling Algorithm",
        list(algorithm_functions.keys()),
        key="sim_algorithm",
    )

    sim_quantum = 2
    if sim_algorithm == "Round Robin":
        sim_quantum = st.number_input(
            "Time Quantum",
            min_value=1,
            value=2,
            step=1,
            key="sim_time_quantum",
        )

    if st.button(
        "Generate Execution Simulation",
        type="primary",
        use_container_width=True,
    ):
        ids = [p["pid"] for p in sim_processes]

        if any(not pid for pid in ids):
            st.error("Process IDs cannot be empty.")
        elif len(ids) != len(set(ids)):
            st.error("Process IDs must be unique.")
        else:
            try:
                if sim_algorithm == "Round Robin":
                    sim_results, sim_timeline = round_robin(
                        sim_processes, int(sim_quantum)
                    )
                else:
                    sim_results, sim_timeline = algorithm_functions[
                        sim_algorithm
                    ](sim_processes)

                st.session_state["sim_data"] = {
                    "algorithm": sim_algorithm,
                    "processes": sim_processes,
                    "results": sim_results,
                    "timeline": sim_timeline,
                    "quantum": int(sim_quantum),
                }
                st.session_state["sim_step"] = 0
            except ValueError as exc:
                st.error(f"Invalid scheduling input: {exc}")

    if "sim_data" in st.session_state:
        data = st.session_state["sim_data"]
        timeline = data["timeline"]
        configured_processes = data["processes"]

        if not timeline:
            st.warning("No execution timeline was generated.")
        else:
            st.divider()
            st.markdown("## Execution Playback")
            st.write(f"Algorithm: **{data['algorithm']}**")

            if data["algorithm"] == "Round Robin":
                st.write(f"Time Quantum: **{data['quantum']} units**")

            total_steps = len(timeline)
            step = st.slider(
                "Move through execution",
                min_value=0,
                max_value=total_steps,
                value=min(st.session_state.get("sim_step", 0), total_steps),
                key="sim_step",
                help=(
                    "Step 0 is before execution. Each next step completes "
                    "one CPU execution segment."
                ),
            )

            if step == 0:
                previous_finish = 0
            else:
                previous_finish = timeline[step - 1]["finish"]

            next_event = timeline[step] if step < total_steps else None
            current_time = (
                next_event["start"] if next_event is not None else previous_finish
            )

            st.progress(
                step / total_steps,
                text=f"Execution progress: {step}/{total_steps} segments completed",
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Current Simulation Time", current_time)
            c2.metric("Completed Segments", step)
            c3.metric("Remaining Segments", total_steps - step)

            process_states = []
            for process in configured_processes:
                pid = process["pid"]
                burst = process["burst"]
                arrival = process["arrival"]

                executed = sum(
                    event["finish"] - event["start"]
                    for event in timeline[:step]
                    if event["pid"] == pid
                )
                remaining = burst - executed

                if remaining == 0:
                    status = "Completed"
                elif next_event is not None and next_event["pid"] == pid:
                    status = "Running next"
                elif arrival > current_time:
                    status = "Not Arrived"
                else:
                    status = "Ready / Waiting"

                process_states.append({
                    "Process": pid,
                    "Arrival": arrival,
                    "Burst": burst,
                    "Priority": process.get("priority", 0),
                    "Executed": executed,
                    "Remaining": remaining,
                    "Status": status,
                })

            st.markdown("### Current Process States")
            st.dataframe(
                pd.DataFrame(process_states),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("### What is happening now?")
            if next_event is None:
                st.success(
                    "All processes have completed execution. "
                    "The CPU scheduling simulation is finished."
                )
            else:
                idle_time = next_event["start"] - previous_finish
                if idle_time > 0:
                    st.warning(
                        f"The CPU was idle for {idle_time} time units because "
                        "no process was ready."
                    )

                explanation = {
                    "FCFS": "The earliest-arrived waiting process gets the CPU and runs to completion.",
                    "SJF": "The ready process with the shortest full burst is selected; it is not preempted.",
                    "SRTF": "The ready process with the shortest remaining time is selected; arrivals can cause preemption.",
                    "Priority": "The ready process with the smallest priority number is selected; it is not preempted.",
                    "Preemptive Priority": "The ready process with the smallest priority number runs; a higher-priority arrival can preempt it.",
                    "Round Robin": "The process receives up to one time quantum. If unfinished, it returns to the back of the ready queue.",
                }[data["algorithm"]]

                st.success(
                    f"{next_event['pid']} is scheduled from time "
                    f"{next_event['start']} to {next_event['finish']}."
                )
                st.caption(explanation)
                st.caption(
                    "Move the slider one step forward to complete this execution segment."
                )

            import plotly.graph_objects as go

            fig = go.Figure()
            for index, event in enumerate(timeline):
                fig.add_trace(
                    go.Bar(
                        x=[event["finish"] - event["start"]],
                        y=[event["pid"]],
                        base=[event["start"]],
                        orientation="h",
                        name=event["pid"],
                        opacity=1.0 if index < step else 0.35,
                        hovertemplate=(
                            f"Process: {event['pid']}"
                            "<br>Start: %{base}"
                            "<br>Duration: %{x}"
                            "<extra></extra>"
                        ),
                    )
                )

            final_time = max(event["finish"] for event in timeline)
            fig.add_vline(
                x=current_time,
                line_dash="dash",
                line_width=2,
                annotation_text="Current time",
            )
            fig.update_layout(
                title="CPU Execution Timeline",
                xaxis_title="Simulation Time",
                yaxis_title="Process",
                barmode="overlay",
                showlegend=False,
                xaxis=dict(range=[0, final_time], dtick=1),
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)

            previous_col, next_col = st.columns(2)
            with previous_col:
                if st.button(
                    "← Previous Step",
                    disabled=(step == 0),
                    use_container_width=True,
                ):
                    st.session_state["sim_step"] = step - 1
                    st.rerun()

            with next_col:
                if st.button(
                    "Next Step →",
                    disabled=(step == total_steps),
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state["sim_step"] = step + 1
                    st.rerun()

            with st.expander("View final scheduling results"):
                st.dataframe(
                    pd.DataFrame(data["results"]),
                    use_container_width=True,
                    hide_index=True,
                )


st.divider()
st.caption(
    "SmartRes development milestone • Process management, resource "
    "allocation, safety evaluation, and persistent event history"
)
