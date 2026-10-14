
import streamlit as st
import pandas as pd

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

overview, process_tab, resource_tab, request_tab, history_tab = st.tabs(
    [
        "Overview",
        "Process Management",
        "Resource Management",
        "Resource Requests",
        "Event History",
    ]
)

with overview:
    st.subheader("System Overview")

    if resources:
        resource_summary = pd.DataFrame([
            {
                "Resource": r["name"],
                "Total": r["total"],
                "Allocated": allocated_by_resource[r["id"]],
                "Available": available_by_resource[r["id"]],
            }
            for r in resources
        ])
        st.dataframe(resource_summary, use_container_width=True, hide_index=True)
    else:
        st.info("Start by adding resources in Resource Management.")

    if active_processes:
        st.subheader("Active Processes")
        st.dataframe(
            pd.DataFrame(active_processes)[
                ["id", "name", "status", "created_at"]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No active processes yet.")

    if safety["safe"] and safety["sequence"]:
        sequence_text = " → ".join(
            f"P{process_id}" for process_id in safety["sequence"]
        )
        st.success(f"Safe sequence: {sequence_text}")
    elif not safety["safe"]:
        st.warning("No safe sequence exists for the current allocation state.")

    if allocations:
        st.subheader("Allocation and Need Matrix")
        st.dataframe(
            pd.DataFrame(allocations),
            use_container_width=True,
            hide_index=True,
        )

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

st.divider()
st.caption(
    "SmartRes development milestone • Process management, resource "
    "allocation, safety evaluation, and persistent event history"
)
