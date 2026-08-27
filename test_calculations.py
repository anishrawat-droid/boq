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
    setup = StreamingSetup()
    online = default_online_events()
    for ev in online:
        ev.enabled = False
    totals = compute_totals(setup, online, [], FrameProcessor(enabled=False))
    assert totals.gpu_gb == 0
    assert totals.ram_gb >= setup.ram_gb
    assert totals.vcpu >= setup.vcpu
    print("Disable-all check passed:", totals.ram_gb, "GB RAM |", totals.vcpu, "vCPU")


def test_anpr_event_present_in_default_catalog():
    online = default_online_events()
    event = next((ev for ev in online if ev.id == "anpr"), None)
    assert event is not None, "ANPR event should be included by default"
    assert event.cameras > 0
    assert len(event.stages) > 0
    print("ANPR check passed:", event.name, "|", event.cameras, "cameras")


def test_streaming_only_mode_ignores_models():
    setup = StreamingSetup(include_models=False)
    totals = compute_totals(
        setup,
        default_online_events(),
        default_offline_events(),
        FrameProcessor(enabled=False),
    )
    assert totals.gpu_gb == 0, "Stream-only mode should exclude model GPU load"
    assert totals.ram_gb >= setup.ram_gb, "Streaming setup should include base RAM"
    assert totals.vcpu >= setup.vcpu, "Streaming setup should include base vCPU"
    assert totals.dvr_tb > 0, "Streaming storage should still be calculated"
    print("Streaming-only check passed:", totals.ram_gb, "GB RAM |", totals.vcpu, "vCPU |", totals.dvr_tb, "TB DVR")


if __name__ == "__main__":
    test_defaults_produce_nonzero_gpu()
    test_storage_matches_reference_sheet()
    test_disabling_events_zeroes_them_out()
    test_anpr_event_present_in_default_catalog()
    test_streaming_only_mode_ignores_models()
    print("\nAll checks passed.")
