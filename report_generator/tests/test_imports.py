"""
Basic tests for the report generator.

This ensures all modules are importable and that the config is valid.
"""


def test_import_app():
    from fuel_additive_report.application import FuelAdditiveReportGenerator

    assert FuelAdditiveReportGenerator
    assert FuelAdditiveReportGenerator.config_cls is not None


def test_config():
    from fuel_additive_report.app_config import FuelAdditiveReportConfig

    schema = FuelAdditiveReportConfig.to_schema()
    assert isinstance(schema, dict)
    assert len(schema["properties"]) > 0


def test_build_pdf():
    from fuel_additive_report.build_pdf import build_pdf

    context = {
        "skid_name": "Test Skid",
        "report_label": "Test Skid - 20/08/26",
        "report_time": "01:00:am",
        "report_date": "20-08-2026",
        "injectors": [
            {
                "index": 1,
                "injector_name": "Injector 1",
                "flowmeter_total": 1234.5,
                "actual_injection_detergent": 12.3,
                "calculated_detergent": 12.1,
                "difference": 1.6,
            }
        ],
        "total_gasoline": 1234.5,
        "total_calculated_detergent": 12.1,
        "total_actual_detergent_injected": 12.3,
        "difference": 1.6,
    }
    pdf = build_pdf(context)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")


def test_report_label_carries_the_reported_day():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from fuel_additive_report.application import report_label

    riyadh = ZoneInfo("Asia/Riyadh")
    label = report_label("SJBP", datetime(2026, 9, 12, tzinfo=riyadh))
    assert label == "SJBP - 12/09/26"
    # whatever the skid is called, the label follows
    assert (
        report_label("NRBP", datetime(2026, 1, 5, tzinfo=riyadh)) == "NRBP - 05/01/26"
    )


def test_report_filename_survives_the_wire():
    """No "/" (path separator) and no spaces (aiohttp percent-encodes them
    into the multipart filename, and the "%20" reaches the emailed
    attachment's name)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from fuel_additive_report.application import report_filename

    riyadh = ZoneInfo("Asia/Riyadh")
    day = datetime(2026, 9, 12, tzinfo=riyadh)

    assert report_filename("SJBP", day) == "SJBP_12-09-26.pdf"
    # skid names carry spaces of their own
    assert report_filename("Saad BP", day) == "Saad_BP_12-09-26.pdf"
    for skid in ("SJBP", "Saad BP", "DCA Injection Skids"):
        name = report_filename(skid, day)
        assert "/" not in name and " " not in name


def test_each_skid_gets_its_own_file_name():
    """Four of the five skids report the same skid_name, so the file name has
    to come from the device - attachments are keyed on filename and identical
    names overwrite each other."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from fuel_additive_report.application import report_filename

    day = datetime(2026, 9, 12, tzinfo=ZoneInfo("Asia/Riyadh"))
    names = {report_filename(s, day) for s in ("NRBP", "QSBP", "SRBP", "Saad BP", "SJBP")}
    assert len(names) == 5
