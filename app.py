
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

overview, process_tab, resource_tab, request_tab, history_tab, cpu_tab = st.tabs(
    [
        "Overview",
        "Process Management",
        "Resource Management",
        "Resource Requests",
        "Event History",
        "CPU Scheduling Lab",
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
    st.subheader("CPU Scheduling Lab")
    st.write(
        "Configure one workload, compare all six scheduling algorithms, "
        "and then step through any algorithm using the same processes."
    )
    st.info(
        "All six algorithms use the same arrival times, CPU burst times, and priorities. "
        "A smaller priority number means a higher priority. SJF/SRTF use the supplied "
        "burst lengths; context-switch overhead is not modelled."
    )

    st.markdown("### 1. Configure the shared workload")
    process_count = st.number_input(
        "Number of processes",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        key="shared_process_count",
    )
    st.caption(
        "Arrival = when a process enters the ready queue · Burst = total CPU time needed · "
        "Priority = smaller number means higher priority."
    )

    scheduling_processes = []
    for i in range(int(process_count)):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            pid = st.text_input(
                f"Process ID {i + 1}", value=f"P{i + 1}", key=f"shared_pid_{i}"
            )
        with c2:
            arrival = st.number_input(
                f"Arrival {i + 1}", min_value=0, value=0, step=1,
                key=f"shared_arrival_{i}"
            )
        with c3:
            burst = st.number_input(
                f"Burst {i + 1}", min_value=1, value=3, step=1,
                key=f"shared_burst_{i}"
            )
        with c4:
            priority = st.number_input(
                f"Priority {i + 1}", min_value=0, value=1, step=1,
                key=f"shared_priority_{i}",
                help="Lower number means higher priority."
            )

        scheduling_processes.append({
            "pid": pid.strip(),
            "arrival": int(arrival),
            "burst": int(burst),
            "priority": int(priority),
        })

    quantum = st.number_input(
        "Round Robin time quantum",
        min_value=1,
        value=2,
        step=1,
        key="shared_quantum",
        help="Maximum CPU time a process can use in one turn before returning to the ready queue."
    )

    workload_signature = tuple(
        (p["pid"], p["arrival"], p["burst"], p["priority"])
        for p in scheduling_processes
    )

    def validate_workload(workload):
        ids = [p["pid"] for p in workload]
        if any(not pid for pid in ids):
            return "Process IDs cannot be empty."
        if len(ids) != len(set(ids)):
            return "Every process must have a unique ID."
        return None

    algorithm_functions = {
        "FCFS": fcfs,
        "SJF": sjf,
        "SRTF": srtf,
        "Priority": priority_scheduling,
        "Preemptive Priority": preemptive_priority,
        "Round Robin": round_robin,
    }

    comparison_section, playback_section = st.tabs(
        ["Compare all six algorithms", "Execution playback"]
    )

    with comparison_section:
        st.markdown("### 2. Compare scheduling performance")
        st.write(
            "Run every algorithm against the exact same workload. Compare average "
            "waiting time, turnaround time, CPU utilisation, throughput, and completion time."
        )

        if st.button(
            "Run comparison of all six algorithms",
            type="primary",
            use_container_width=True,
            key="run_scheduling_comparison",
        ):
            validation_error = validate_workload(scheduling_processes)
            if validation_error:
                st.error(validation_error)
            else:
                try:
                    outputs = {}
                    for name, function in algorithm_functions.items():
                        if name == "Round Robin":
                            outputs[name] = function(scheduling_processes, int(quantum))
                        else:
                            outputs[name] = function(scheduling_processes)

                    total_burst = sum(p["burst"] for p in scheduling_processes)

                    def calculate_metrics(results):
                        makespan = max(p["completion"] for p in results)
                        return {
                            "Average Waiting Time": sum(p["waiting"] for p in results) / len(results),
                            "Average Turnaround Time": sum(p["turnaround"] for p in results) / len(results),
                            "CPU Utilisation (%)": total_burst / makespan * 100 if makespan else 0,
                            "Throughput (processes/unit time)": len(results) / makespan if makespan else 0,
                            "Final Completion Time": makespan,
                        }

                    metrics = {
                        name: calculate_metrics(output[0])
                        for name, output in outputs.items()
                    }
                    st.session_state["scheduling_comparison"] = {
                        "signature": workload_signature,
                        "quantum": int(quantum),
                        "outputs": outputs,
                        "metrics": metrics,
                    }
                except ValueError as exc:
                    st.error(f"Could not run the comparison: {exc}")

        comparison_data = st.session_state.get("scheduling_comparison")
        if comparison_data and comparison_data["signature"] != workload_signature:
            st.info("The workload has changed. Run the comparison again to refresh these results.")
        elif comparison_data:
            outputs = comparison_data["outputs"]
            metrics = comparison_data["metrics"]

            st.divider()
            st.markdown("#### Performance summary")
            metric_rows = []
            for metric_name in next(iter(metrics.values())):
                row = {"Metric": metric_name}
                for algorithm_name, values in metrics.items():
                    row[algorithm_name] = round(values[metric_name], 2)
                metric_rows.append(row)
            st.dataframe(
                pd.DataFrame(metric_rows),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "Lower is generally better for waiting, turnaround, and completion time; "
                "higher is generally better for throughput and utilisation. Utilisation = "
                "total CPU burst ÷ elapsed time from time 0 to final completion. "
                "Throughput = process count ÷ the same elapsed time. Idle gaps are included; "
                "context-switch overhead is not modelled."
            )

            st.markdown("#### Gantt chart comparison")
            import plotly.graph_objects as go

            process_ids = [p["pid"] for p in scheduling_processes]
            palette = [
                "#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2",
                "#B279A2", "#FF9DA6", "#9D755D", "#BAB0AC", "#79706E"
            ]
            process_colors = {
                pid: palette[index % len(palette)]
                for index, pid in enumerate(process_ids)
            }

            def create_gantt(timeline, title):
                fig = go.Figure()
                for event in timeline:
                    pid = event["pid"]
                    start = event["start"]
                    finish = event["finish"]
                    fig.add_trace(go.Bar(
                        x=[finish - start],
                        y=[pid],
                        base=[start],
                        orientation="h",
                        marker_color=process_colors.get(pid, "#777777"),
                        name=pid,
                        hovertemplate=(
                            f"Process: {pid}<br>Start: {start}<br>Finish: {finish}"
                            f"<br>Duration: {finish - start}<extra></extra>"
                        ),
                    ))
                final_time = max(event["finish"] for event in timeline)
                fig.update_layout(
                    title=title,
                    xaxis_title="CPU time",
                    yaxis_title="Process",
                    barmode="overlay",
                    showlegend=False,
                    xaxis=dict(range=[0, final_time], dtick=1, zeroline=True),
                    height=270,
                    margin=dict(l=20, r=15, t=45, b=35),
                )
                return fig

            st.caption(
                "Each colour represents the same process across all charts. Blank spaces "
                "on the time axis indicate periods when the CPU is idle."
            )
            algorithm_names = list(outputs)
            for row_start in range(0, len(algorithm_names), 2):
                left, right = st.columns(2)
                for column, algorithm_name in zip(
                    (left, right), algorithm_names[row_start:row_start + 2]
                ):
                    with column:
                        st.plotly_chart(
                            create_gantt(outputs[algorithm_name][1], algorithm_name),
                            use_container_width=True,
                        )

            st.markdown("#### Process-wise completion metrics")
            for algorithm_name, (results, _) in outputs.items():
                with st.expander(f"{algorithm_name} — detailed results"):
                    st.dataframe(
                        pd.DataFrame(results),
                        use_container_width=True,
                        hide_index=True,
                    )

            st.markdown("#### How to interpret the six algorithms")
            explanations = {
                "FCFS": "Runs ready processes in arrival order, without interruption. Simple, but a long job can delay short jobs (convoy effect).",
                "SJF": "Selects the ready process with the shortest full CPU burst. It is non-preemptive and can reduce average waiting under suitable assumptions when burst lengths are known.",
                "SRTF": "Selects the ready process with the least remaining CPU time. A newly arrived shorter job can preempt the current process.",
                "Priority": "Selects the ready process with the smallest priority number. It is non-preemptive; low-priority processes may starve.",
                "Preemptive Priority": "Runs the highest-priority ready process and preempts the current one when a higher-priority process becomes ready. Starvation is possible.",
                "Round Robin": f"Gives each ready process up to {comparison_data['quantum']} time units per turn. Unfinished processes return to the back of the ready queue; the quantum controls responsiveness and switching frequency.",
            }
            for name, explanation in explanations.items():
                st.markdown(f"**{name}:** {explanation}")

    with playback_section:
        st.markdown("### 3. Step through any scheduling algorithm")
        st.write(
            "The simulator uses the workload configured above. Select an algorithm, "
            "generate its timeline, and move through the execution segments."
        )
        selected_algorithm = st.selectbox(
            "Algorithm to simulate",
            list(algorithm_functions),
            key="shared_sim_algorithm",
        )
        sim_quantum = int(quantum)
        if selected_algorithm == "Round Robin":
            sim_quantum = st.number_input(
                "Simulation time quantum",
                min_value=1,
                value=int(quantum),
                step=1,
                key="shared_sim_quantum",
            )

        if st.button(
            "Generate playback for this workload",
            type="primary",
            use_container_width=True,
            key="generate_shared_playback",
        ):
            validation_error = validate_workload(scheduling_processes)
            if validation_error:
                st.error(validation_error)
            else:
                try:
                    if selected_algorithm == "Round Robin":
                        sim_results, sim_timeline = round_robin(
                            scheduling_processes, int(sim_quantum)
                        )
                    else:
                        sim_results, sim_timeline = algorithm_functions[selected_algorithm](
                            scheduling_processes
                        )
                    st.session_state["sim_data"] = {
                        "signature": workload_signature,
                        "algorithm": selected_algorithm,
                        "processes": [dict(p) for p in scheduling_processes],
                        "results": sim_results,
                        "timeline": sim_timeline,
                        "quantum": int(sim_quantum),
                    }
                    st.session_state["sim_step"] = 0
                except ValueError as exc:
                    st.error(f"Could not generate playback: {exc}")

        data = st.session_state.get("sim_data")
        if data and data["signature"] != workload_signature:
            st.info("The workload has changed. Generate playback again to simulate the updated processes.")
        elif data:
            timeline = data["timeline"]
            configured_processes = data["processes"]
            if not timeline:
                st.warning("No execution timeline was generated.")
            else:
                st.divider()
                st.markdown(f"#### Execution playback — {data['algorithm']}")
                if data["algorithm"] == "Round Robin":
                    st.caption(f"Time quantum: {data['quantum']} time units")

                total_steps = len(timeline)
                step = st.slider(
                    "Execution segment",
                    min_value=0,
                    max_value=total_steps,
                    value=min(st.session_state.get("sim_step", 0), total_steps),
                    key="sim_step",
                    help="Step 0 is before execution. Each step completes one continuous CPU segment.",
                )
                previous_finish = timeline[step - 1]["finish"] if step else 0
                next_event = timeline[step] if step < total_steps else None
                current_time = next_event["start"] if next_event else previous_finish

                st.progress(
                    step / total_steps,
                    text=f"{step} of {total_steps} execution segments completed",
                )
                c1, c2, c3 = st.columns(3)
                c1.metric("Simulation time", current_time)
                c2.metric("Segments completed", step)
                c3.metric("Segments remaining", total_steps - step)

                process_states = []
                for process in configured_processes:
                    pid = process["pid"]
                    executed = sum(
                        event["finish"] - event["start"]
                        for event in timeline[:step]
                        if event["pid"] == pid
                    )
                    remaining = process["burst"] - executed
                    if remaining == 0:
                        status = "Completed"
                    elif next_event is not None and next_event["pid"] == pid:
                        status = "Next to run"
                    elif process["arrival"] > current_time:
                        status = "Not arrived"
                    else:
                        status = "Ready / waiting"
                    process_states.append({
                        "Process": pid,
                        "Arrival": process["arrival"],
                        "Burst": process["burst"],
                        "Priority": process.get("priority", 0),
                        "Executed": executed,
                        "Remaining": remaining,
                        "Status": status,
                    })

                st.markdown("#### Process states at this step")
                st.dataframe(
                    pd.DataFrame(process_states),
                    use_container_width=True,
                    hide_index=True,
                )

                st.markdown("#### Scheduling decision")
                if next_event is None:
                    st.success("All processes have completed. The simulation is finished.")
                else:
                    idle_time = next_event["start"] - previous_finish
                    if idle_time > 0:
                        st.warning(
                            f"The CPU is idle for {idle_time} time unit(s) because no process is ready."
                        )
                    decision_text = {
                        "FCFS": "The earliest-arrived process in the ready queue is selected and runs until completion.",
                        "SJF": "The ready process with the shortest full CPU burst is selected; it is not interrupted once running.",
                        "SRTF": "The ready process with the shortest remaining CPU time is selected; a shorter newly arrived job can preempt it.",
                        "Priority": "The ready process with the smallest priority value is selected; it runs without preemption.",
                        "Preemptive Priority": "The ready process with the smallest priority value is selected; a higher-priority arrival can preempt it.",
                        "Round Robin": f"The next process in the ready queue receives up to {data['quantum']} time unit(s). If unfinished, it returns to the queue's end.",
                    }[data["algorithm"]]
                    st.success(
                        f"{next_event['pid']} is scheduled from time {next_event['start']} "
                        f"to {next_event['finish']}."
                    )
                    st.caption(decision_text)

                import plotly.graph_objects as go
                palette = [
                    "#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2",
                    "#B279A2", "#FF9DA6", "#9D755D", "#BAB0AC", "#79706E"
                ]
                process_colors = {
                    p["pid"]: palette[index % len(palette)]
                    for index, p in enumerate(configured_processes)
                }
                fig = go.Figure()
                for index, event in enumerate(timeline):
                    pid = event["pid"]
                    fig.add_trace(go.Bar(
                        x=[event["finish"] - event["start"]],
                        y=[pid],
                        base=[event["start"]],
                        orientation="h",
                        marker_color=process_colors.get(pid, "#777777"),
                        opacity=1.0 if index < step else 0.35,
                        name=pid,
                        hovertemplate=(
                            f"Process: {pid}<br>Start: {event['start']}"
                            f"<br>Finish: {event['finish']}<extra></extra>"
                        ),
                    ))
                final_time = max(event["finish"] for event in timeline)
                fig.add_vline(
                    x=current_time,
                    line_dash="dash",
                    line_width=2,
                    annotation_text="Current time",
                )
                fig.update_layout(
                    title="CPU execution timeline",
                    xaxis_title="Simulation time",
                    yaxis_title="Process",
                    barmode="overlay",
                    showlegend=False,
                    xaxis=dict(range=[0, final_time], dtick=1),
                    height=330,
                    margin=dict(l=20, r=15, t=45, b=35),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Completed segments are shown at full opacity; upcoming segments are faded. Blank gaps indicate CPU idle time.")

                previous_col, next_col = st.columns(2)
                with previous_col:
                    if st.button("← Previous segment", disabled=(step == 0), use_container_width=True):
                        st.session_state["sim_step"] = step - 1
                        st.rerun()
                with next_col:
                    if st.button("Next segment →", disabled=(step == total_steps), type="primary", use_container_width=True):
                        st.session_state["sim_step"] = step + 1
                        st.rerun()

                with st.expander("View final process metrics"):
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
