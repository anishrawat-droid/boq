"""Quick sanity checks for the calculation core — no Streamlit required.

Run with:  python test_calculations.py
"""

from boq_calculator import (
    FrameProcessor,
    StreamingSetup,
    compute_totals,
    default_offline_events,
    default_online_events,
)


def test_defaults_produce_nonzero_gpu():
    setup = StreamingSetup()
    totals = compute_totals(
        setup, default_online_events(), default_offline_events(), FrameProcessor()
    )
    assert totals.gpu_gb > 0, "Default catalog should produce nonzero GPU requirement"
    print("GPU GB:", totals.gpu_gb, "| RAM GB:", totals.ram_gb, "| vCPU:", totals.vcpu)


def test_storage_matches_reference_sheet():
    # Reference workbook: 40 cameras, 1 Mbps/cam, 180 DVR days, 6h NDVR -> 75TB / 1TB
    setup = StreamingSetup(total_cameras=40, bandwidth_mbps_per_camera=1, dvr_days=180, ndvr_hours=6)
    totals = compute_totals(setup, [], [], FrameProcessor(enabled=False))
    assert totals.dvr_tb == 75, totals.dvr_tb
    assert totals.ndvr_tb == 1, totals.ndvr_tb
    print("Storage check passed: DVR=75TB, NDVR=1TB")


def test_disabling_events_zeroes_them_out():
    online = default_online_events()
    for ev in online:
        ev.enabled = False
    totals = compute_totals(StreamingSetup(), online, [], FrameProcessor(enabled=False))
    assert totals.gpu_gb == 0
    assert totals.vcpu == 0
    print("Disable-all check passed")


def test_anpr_event_present_in_default_catalog():
    online = default_online_events()
    event = next((ev for ev in online if ev.id == "anpr"), None)
    assert event is not None, "ANPR event should be included by default"
    assert event.cameras > 0
    assert len(event.stages) > 0
    print("ANPR check passed:", event.name, "|", event.cameras, "cameras")




if __name__ == "__main__":
    test_defaults_produce_nonzero_gpu()
    test_storage_matches_reference_sheet()
    test_disabling_events_zeroes_them_out()
    test_anpr_event_present_in_default_catalog()
    print("\nAll checks passed.")
