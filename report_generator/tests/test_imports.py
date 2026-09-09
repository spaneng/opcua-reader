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


def test_report_filename_has_no_path_separator():
    from fuel_additive_report.application import report_filename

    name = report_filename("SJBP - 12/09/26")
    assert name == "SJBP - 12-09-26.pdf"
    assert "/" not in name
