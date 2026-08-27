"""BOQ Capacity Estimator — Streamlit app.

Run with:  streamlit run app.py
"""

import copy

import streamlit as st

from boq_calculator import (
    FrameProcessor,
    OfflineEvent,
    OnlineEvent,
    Stage,
    StreamingSetup,
    build_workbook,
    client_spec_text,
    compute_totals,
    default_offline_events,
    default_online_events,
    workbook_to_bytes,
)

st.set_page_config(page_title="BOQ Capacity Estimator", layout="wide")


# --------------------------------------------------------------------------
# Session state init
# --------------------------------------------------------------------------
def init_state():
    st.session_state.setup = StreamingSetup()
    st.session_state.online_events = default_online_events()
    st.session_state.offline_events = default_offline_events()
    st.session_state.frame_processor = FrameProcessor()


if "setup" not in st.session_state:
    init_state()

setup: StreamingSetup = st.session_state.setup
online_events: list[OnlineEvent] = st.session_state.online_events
offline_events: list[OfflineEvent] = st.session_state.offline_events
frame_processor: FrameProcessor = st.session_state.frame_processor


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
top_l, top_r = st.columns([5, 1])
with top_l:
    st.title("📹 Camera Analytics Capacity Estimator")
    st.caption(
        "Enter camera counts per analytics event, tune per-model resource "
        "assumptions if needed, and get the GPU / vCPU / RAM / storage / "
        "bandwidth spec to quote the client."
    )
with top_r:
    st.write("")
    if st.button("Reset to defaults", use_container_width=True):
        init_state()
        st.rerun()

left, right = st.columns([2.1, 1])

# --------------------------------------------------------------------------
# LEFT COLUMN — inputs
# --------------------------------------------------------------------------
with left:
    with st.expander("Streaming Setup", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        setup.total_cameras = c1.number_input("Total Cameras", min_value=0, value=setup.total_cameras)
        setup.operational_hours = c2.number_input("Operational Hours/Day", min_value=0.0, max_value=24.0, value=float(setup.operational_hours))
        setup.dvr_days = c3.number_input("DVR Storage (days)", min_value=0.0, value=float(setup.dvr_days))
        setup.ndvr_hours = c4.number_input("NDVR Buffer (hours)", min_value=0.0, value=float(setup.ndvr_hours))
        setup.bandwidth_mbps_per_camera = c5.number_input("Bandwidth/Camera (Mbps)", min_value=0.0, value=float(setup.bandwidth_mbps_per_camera), step=0.1)

        setup.include_models = st.checkbox(
            "Include analytics models in BOQ",
            value=setup.include_models,
            help="Turn this off to size only the streaming setup and keep model load out of the estimate.",
        )

    st.subheader("Real-Time Analytics (Online Events)")
    st.caption("FPS-driven, always-on inference")

    for ev in online_events:
        r = ev.resource_usage()
        with st.container(border=True):
            h1, h2 = st.columns([3, 2])
            with h1:
                ev.enabled = st.checkbox(
                    ev.name + (" (custom)" if ev.custom else ""),
                    value=ev.enabled,
                    key=f"toggle_{ev.id}",
                )
            with h2:
                st.markdown(
                    f"<div style='text-align:right; padding-top:6px; color:#888;'>"
                    f"GPU {r['gpu_mb']/1024:.2f} GB &nbsp;|&nbsp; "
                    f"RAM {r['ram_mb']/1024:.2f} GB &nbsp;|&nbsp; "
                    f"vCPU {r['vcpu']:.1f}</div>",
                    unsafe_allow_html=True,
                )

            b1, b2 = st.columns([1, 3])
            ev.cameras = b1.number_input(
                "Cameras", min_value=0, value=ev.cameras, key=f"cams_{ev.id}"
            )
            if ev.custom and b2.button("Remove", key=f"rm_{ev.id}"):
                online_events.remove(ev)
                st.rerun()

            with st.expander("Edit model params", expanded=ev.custom):
                for i, s in enumerate(ev.stages):
                    cols = st.columns([2, 1, 1, 1, 1, 1])
                    cols[0].markdown(f"**{s.name}**")
                    s.mult = cols[1].number_input("FPS load/cam", value=float(s.mult), step=0.01, key=f"mult_{ev.id}_{i}")
                    s.cap = cols[2].number_input("Capacity FPS/inst", value=float(s.cap), step=0.5, key=f"cap_{ev.id}_{i}")
                    s.gpu_mb = cols[3].number_input("GPU MB/inst", value=float(s.gpu_mb), key=f"gpu_{ev.id}_{i}")
                    s.ram_mb = cols[4].number_input("RAM MB/inst", value=float(s.ram_mb), key=f"ram_{ev.id}_{i}")
                    s.vcpu = cols[5].number_input("vCPU/inst", value=float(s.vcpu), step=0.5, key=f"vcpu_{ev.id}_{i}")

    if st.button("+ Add custom analytics model"):
        new_id = f"custom_online_{len(online_events)}_{id(object())}"
        online_events.append(
            OnlineEvent(
                id=new_id,
                name="New Analytics Model",
                cameras=10,
                stages=[Stage("Custom Model", mult=1, cap=30, gpu_mb=1200, ram_mb=2400, vcpu=2)],
                custom=True,
            )
        )
        st.rerun()

    st.subheader("Batch Analytics (Offline / Forensic Events)")
    st.caption("recordings/day driven")

    for ev in offline_events:
        r = ev.resource_usage()
        with st.container(border=True):
            h1, h2 = st.columns([3, 2])
            with h1:
                ev.enabled = st.checkbox(
                    ev.name + (" (custom)" if ev.custom else ""),
                    value=ev.enabled,
                    key=f"otoggle_{ev.id}",
                )
            with h2:
                st.markdown(
                    f"<div style='text-align:right; padding-top:6px; color:#888;'>"
                    f"Inst {r['instances']} &nbsp;|&nbsp; "
                    f"GPU {r['gpu_mb']/1024:.2f} GB &nbsp;|&nbsp; "
                    f"RAM {r['ram_mb']/1024:.2f} GB &nbsp;|&nbsp; "
                    f"vCPU {r['vcpu']:.1f}</div>",
                    unsafe_allow_html=True,
                )
            cols = st.columns(6)
            ev.recordings_per_day = cols[0].number_input("Recordings/Day", min_value=0.0, value=float(ev.recordings_per_day), key=f"rpd_{ev.id}")
            ev.minutes_per_recording = cols[1].number_input("Min/Recording", min_value=0.0, value=float(ev.minutes_per_recording), key=f"mpr_{ev.id}")
            ev.gpu_mb = cols[2].number_input("GPU MB/Instance", min_value=0.0, value=float(ev.gpu_mb), key=f"ogpu_{ev.id}")
            ev.ram_mb = cols[3].number_input("RAM MB/Instance", min_value=0.0, value=float(ev.ram_mb), key=f"oram_{ev.id}")
            ev.vcpu = cols[4].number_input("vCPU/Instance", min_value=0.0, value=float(ev.vcpu), step=0.5, key=f"ovcpu_{ev.id}")
            if ev.custom and cols[5].button("Remove", key=f"orm_{ev.id}"):
                offline_events.remove(ev)
                st.rerun()

    if st.button("+ Add custom batch job"):
        new_id = f"custom_offline_{len(offline_events)}_{id(object())}"
        offline_events.append(
            OfflineEvent(
                id=new_id,
                name="New Batch Job",
                minutes_per_recording=10,
                recordings_per_day=0,
                gpu_mb=1200,
                ram_mb=2400,
                vcpu=2,
                custom=True,
            )
        )
        st.rerun()

    st.subheader("Auxiliary Services")
    with st.container(border=True):
        frame_processor.enabled = st.checkbox(
            "Frame Processor (ingestion, auto-scales with cameras)",
            value=frame_processor.enabled,
        )
        c1, c2 = st.columns(2)
        frame_processor.ram_per_feed_mb = c1.number_input("RAM/Feed (MB)", min_value=0.0, value=float(frame_processor.ram_per_feed_mb))
        frame_processor.vcpu_per_feed = c2.number_input("vCPU/Feed", min_value=0.0, value=float(frame_processor.vcpu_per_feed), step=0.01)
    st.caption(
        "LLM/VLM chat services are typically hosted via API and aren't "
        "included in local GPU/CPU sizing here. Size those separately if "
        "self-hosting."
    )

    st.subheader("Resource Breakdown")
    breakdown_rows = []
    for ev in online_events:
        if not ev.enabled:
            continue
        r = ev.resource_usage()
        breakdown_rows.append({
            "Event / Model": f"{ev.name} ({ev.cameras} cams)",
            "Instances": "—", "GPU (MB)": r["gpu_mb"], "RAM (MB)": r["ram_mb"], "vCPU": r["vcpu"],
        })
        for s in r["stages"]:
            breakdown_rows.append({
                "Event / Model": f"    → {s['name']}",
                "Instances": s["instances"], "GPU (MB)": s["gpu_mb"], "RAM (MB)": s["ram_mb"], "vCPU": s["vcpu"],
            })
    for ev in offline_events:
        if not ev.enabled:
            continue
        r = ev.resource_usage()
        breakdown_rows.append({
            "Event / Model": f"{ev.name} (batch)",
            "Instances": r["instances"], "GPU (MB)": r["gpu_mb"], "RAM (MB)": r["ram_mb"], "vCPU": r["vcpu"],
        })
    if frame_processor.enabled:
        fp = frame_processor.resource_usage(setup.total_cameras)
        breakdown_rows.append({
            "Event / Model": "Frame Processor (ingestion)",
            "Instances": "—", "GPU (MB)": 0, "RAM (MB)": fp["ram_mb"], "vCPU": fp["vcpu"],
        })
    st.dataframe(breakdown_rows, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------
# RIGHT COLUMN — live readout
# --------------------------------------------------------------------------
with right:
    st.subheader("🖥️ Server Spec Readout")

    totals = compute_totals(setup, online_events, offline_events, frame_processor)

    with st.container(border=True):
        st.metric("GPU Memory", f"{totals.gpu_gb} GB", f"{totals.gpu_cards} × 16GB GPU equivalent")
        st.metric("System RAM", f"{totals.ram_gb} GB")
        st.metric("Compute", f"{totals.vcpu} vCPU", f"{totals.physical_cores} cores · {totals.servers} server(s)")
        st.divider()
        st.markdown(f"**DVR Storage:** {totals.dvr_tb} TB")
        st.markdown(f"**NDVR Storage:** {totals.ndvr_tb} TB")
        st.markdown(f"**Incoming Bandwidth:** {totals.bandwidth_mbps:,.0f} Mbps")

    spec_text = client_spec_text(setup, online_events, offline_events, totals)
    st.download_button(
        "📋 Download client spec (.txt)",
        data=spec_text,
        file_name="client_spec.txt",
        use_container_width=True,
    )

    wb = build_workbook(setup, online_events, offline_events, totals)
    st.download_button(
        "📊 Export Excel BOQ",
        data=workbook_to_bytes(wb),
        file_name="BOQ_Estimate.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary",
    )

    with st.expander("Show client spec text"):
        st.code(spec_text, language=None)

    st.caption(
        "Physical cores assume 2 vCPU/core. Servers assume 128 cores/server "
        "(dual 64-core). Storage assumes constant-bitrate streaming at the "
        "configured Mbps/camera. Adjust assumptions above before quoting."
    )
