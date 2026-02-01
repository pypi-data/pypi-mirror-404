"""Tests for empathy_healthcare_plugin.

Comprehensive test coverage for clinical protocol monitoring system.

Created: 2026-01-20
Coverage target: 80%+
"""

import json
from datetime import datetime, timedelta

import pytest

from empathy_healthcare_plugin import ClinicalProtocolMonitor
from empathy_healthcare_plugin.monitors.monitoring.protocol_checker import (
    ComplianceStatus,
    ProtocolChecker,
    ProtocolCheckResult,
    ProtocolDeviation,
)
from empathy_healthcare_plugin.monitors.monitoring.protocol_loader import (
    ClinicalProtocol,
    ProtocolCriterion,
    ProtocolIntervention,
    ProtocolLoader,
)
from empathy_healthcare_plugin.monitors.monitoring.sensor_parsers import (
    FHIRObservationParser,
    SensorParserFactory,
    SimpleJSONParser,
    VitalSignReading,
    VitalSignType,
    normalize_vitals,
    parse_sensor_data,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_protocol():
    """Create a sample clinical protocol for testing."""
    return ClinicalProtocol(
        name="Test Sepsis Protocol",
        version="1.0.0",
        applies_to=["adult_icu"],
        screening_criteria=[
            ProtocolCriterion(
                parameter="systolic_bp",
                condition="<=",
                value=100,
                points=2,
                description="Hypotension",
            ),
            ProtocolCriterion(
                parameter="hr",
                condition=">=",
                value=90,
                points=1,
                description="Tachycardia",
            ),
            ProtocolCriterion(
                parameter="respiratory_rate",
                condition=">=",
                value=22,
                points=1,
                description="Tachypnea",
            ),
            ProtocolCriterion(
                parameter="mental_status",
                condition="altered",
                value=None,
                points=2,
                description="Altered mental status",
            ),
        ],
        screening_threshold=2,
        interventions=[
            ProtocolIntervention(
                order=1,
                action="Draw blood cultures",
                timing="within 1 hour",
                required=True,
            ),
            ProtocolIntervention(
                order=2,
                action="Start IV fluids",
                timing="within 30 minutes",
                required=True,
            ),
            ProtocolIntervention(
                order=3,
                action="Administer antibiotics",
                timing="within 1 hour",
                required=True,
            ),
        ],
        monitoring_frequency="every 15 minutes",
        reassessment_timing="hourly",
        escalation_criteria=["MAP < 65", "Lactate > 4"],
        documentation_requirements=["Sepsis screening documented"],
    )


@pytest.fixture
def sample_patient_data():
    """Sample patient vital signs data."""
    return {
        "hr": 110,
        "systolic_bp": 95,
        "diastolic_bp": 60,
        "respiratory_rate": 24,
        "o2_sat": 94,
        "temp_f": 101.5,
        "mental_status": "normal",
    }


@pytest.fixture
def simple_json_data():
    """Sample simple JSON sensor data."""
    return json.dumps(
        {
            "patient_id": "12345",
            "timestamp": "2026-01-20T14:30:00Z",
            "vitals": {
                "hr": 110,
                "systolic_bp": 95,
                "diastolic_bp": 60,
                "respiratory_rate": 24,
                "o2_sat": 94,
                "temp_f": 101.5,
            },
        }
    )


@pytest.fixture
def fhir_observation_data():
    """Sample FHIR Observation resource."""
    return json.dumps(
        {
            "resourceType": "Observation",
            "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
            "valueQuantity": {"value": 110, "unit": "bpm"},
            "effectiveDateTime": "2026-01-20T14:30:00Z",
            "subject": {"reference": "Patient/12345"},
        }
    )


# =============================================================================
# Sensor Parser Tests
# =============================================================================


class TestVitalSignReading:
    """Tests for VitalSignReading dataclass."""

    def test_to_dict(self):
        """Test converting VitalSignReading to dictionary."""
        reading = VitalSignReading(
            vital_type=VitalSignType.HEART_RATE,
            value=110,
            unit="bpm",
            timestamp=datetime(2026, 1, 20, 14, 30),
            source="bedside_monitor",
            patient_id="12345",
            quality="good",
            metadata={"device": "Philips"},
        )

        result = reading.to_dict()

        assert result["vital_type"] == "heart_rate"
        assert result["value"] == 110
        assert result["unit"] == "bpm"
        assert result["patient_id"] == "12345"
        assert result["quality"] == "good"
        assert result["metadata"]["device"] == "Philips"

    def test_to_dict_with_none_metadata(self):
        """Test to_dict with None metadata."""
        reading = VitalSignReading(
            vital_type=VitalSignType.HEART_RATE,
            value=110,
            unit="bpm",
            timestamp=datetime.now(),
            source="test",
            patient_id="12345",
        )

        result = reading.to_dict()
        assert result["metadata"] == {}


class TestSimpleJSONParser:
    """Tests for SimpleJSONParser."""

    def test_parse_valid_data(self, simple_json_data):
        """Test parsing valid simple JSON data."""
        parser = SimpleJSONParser()
        readings = parser.parse(simple_json_data)

        assert len(readings) >= 5
        hr_readings = [r for r in readings if r.vital_type == VitalSignType.HEART_RATE]
        assert len(hr_readings) == 1
        assert hr_readings[0].value == 110

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns empty list."""
        parser = SimpleJSONParser()
        readings = parser.parse("not valid json")
        assert readings == []

    def test_parse_empty_vitals(self):
        """Test parsing data with no vitals."""
        parser = SimpleJSONParser()
        data = json.dumps({"patient_id": "12345", "vitals": {}})
        readings = parser.parse(data)
        assert readings == []

    def test_parse_unknown_vitals(self):
        """Test parsing data with unknown vital types."""
        parser = SimpleJSONParser()
        data = json.dumps({"patient_id": "12345", "vitals": {"unknown_vital": 100}})
        readings = parser.parse(data)
        assert readings == []

    def test_parse_all_vital_types(self):
        """Test parsing all supported vital types."""
        parser = SimpleJSONParser()
        data = json.dumps(
            {
                "patient_id": "test",
                "vitals": {
                    "hr": 80,
                    "heart_rate": 80,
                    "systolic_bp": 120,
                    "diastolic_bp": 80,
                    "respiratory_rate": 16,
                    "rr": 16,
                    "temp_f": 98.6,
                    "temp_c": 37.0,
                    "o2_sat": 98,
                    "spo2": 98,
                    "mental_status": "normal",
                    "pain": 2,
                },
            }
        )
        readings = parser.parse(data)
        assert len(readings) >= 10


class TestFHIRObservationParser:
    """Tests for FHIRObservationParser."""

    def test_parse_valid_observation(self, fhir_observation_data):
        """Test parsing valid FHIR Observation."""
        parser = FHIRObservationParser()
        readings = parser.parse(fhir_observation_data)

        assert len(readings) == 1
        assert readings[0].vital_type == VitalSignType.HEART_RATE
        assert readings[0].value == 110
        assert readings[0].patient_id == "12345"

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        parser = FHIRObservationParser()
        readings = parser.parse("not valid json")
        assert readings == []

    def test_parse_non_observation_resource(self):
        """Test parsing non-Observation resource type."""
        parser = FHIRObservationParser()
        data = json.dumps({"resourceType": "Patient", "id": "12345"})
        readings = parser.parse(data)
        assert readings == []

    def test_parse_unknown_loinc_code(self):
        """Test parsing observation with unknown LOINC code."""
        parser = FHIRObservationParser()
        data = json.dumps(
            {
                "resourceType": "Observation",
                "code": {"coding": [{"system": "http://loinc.org", "code": "99999-9"}]},
                "valueQuantity": {"value": 100},
            }
        )
        readings = parser.parse(data)
        assert readings == []

    def test_parse_all_loinc_codes(self):
        """Test parsing observations with all supported LOINC codes."""
        parser = FHIRObservationParser()

        loinc_codes = ["8867-4", "8480-6", "9279-1", "8310-5", "2708-6", "38208-5"]

        for code in loinc_codes:
            data = json.dumps(
                {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": code}]},
                    "valueQuantity": {"value": 100, "unit": "units"},
                    "subject": {"reference": "Patient/test"},
                }
            )
            readings = parser.parse(data)
            assert len(readings) == 1, f"Failed for LOINC code {code}"


class TestSensorParserFactory:
    """Tests for SensorParserFactory."""

    def test_create_simple_json_parser(self):
        """Test creating SimpleJSONParser."""
        parser = SensorParserFactory.create("simple_json")
        assert isinstance(parser, SimpleJSONParser)

    def test_create_fhir_parser(self):
        """Test creating FHIRObservationParser."""
        parser = SensorParserFactory.create("fhir")
        assert isinstance(parser, FHIRObservationParser)

    def test_create_unsupported_format(self):
        """Test creating parser for unsupported format."""
        with pytest.raises(ValueError, match="Unsupported sensor format"):
            SensorParserFactory.create("hl7v2")


class TestParseSensorData:
    """Tests for parse_sensor_data convenience function."""

    def test_parse_simple_json(self, simple_json_data):
        """Test parsing simple JSON."""
        readings = parse_sensor_data(simple_json_data, "simple_json")
        assert len(readings) >= 5

    def test_parse_fhir(self, fhir_observation_data):
        """Test parsing FHIR data."""
        readings = parse_sensor_data(fhir_observation_data, "fhir")
        assert len(readings) == 1


class TestNormalizeVitals:
    """Tests for normalize_vitals function."""

    def test_normalize_all_types(self):
        """Test normalizing all vital sign types."""
        readings = [
            VitalSignReading(
                vital_type=VitalSignType.HEART_RATE,
                value=110,
                unit="bpm",
                timestamp=datetime.now(),
                source="test",
                patient_id="test",
            ),
            VitalSignReading(
                vital_type=VitalSignType.BLOOD_PRESSURE,
                value=120,
                unit="mmHg",
                timestamp=datetime.now(),
                source="test",
                patient_id="test",
            ),
            VitalSignReading(
                vital_type=VitalSignType.BLOOD_PRESSURE,
                value=60,
                unit="mmHg",
                timestamp=datetime.now(),
                source="test",
                patient_id="test",
            ),
            VitalSignReading(
                vital_type=VitalSignType.RESPIRATORY_RATE,
                value=18,
                unit="/min",
                timestamp=datetime.now(),
                source="test",
                patient_id="test",
            ),
            VitalSignReading(
                vital_type=VitalSignType.TEMPERATURE,
                value=98.6,
                unit="°F",
                timestamp=datetime.now(),
                source="test",
                patient_id="test",
            ),
            VitalSignReading(
                vital_type=VitalSignType.OXYGEN_SATURATION,
                value=98,
                unit="%",
                timestamp=datetime.now(),
                source="test",
                patient_id="test",
            ),
            VitalSignReading(
                vital_type=VitalSignType.MENTAL_STATUS,
                value="normal",
                unit="text",
                timestamp=datetime.now(),
                source="test",
                patient_id="test",
            ),
            VitalSignReading(
                vital_type=VitalSignType.PAIN_SCORE,
                value=2,
                unit="0-10",
                timestamp=datetime.now(),
                source="test",
                patient_id="test",
            ),
        ]

        normalized = normalize_vitals(readings)

        assert normalized["hr"] == 110
        assert normalized["systolic_bp"] == 120
        assert normalized["diastolic_bp"] == 60
        assert normalized["respiratory_rate"] == 18
        assert normalized["temp_f"] == 98.6
        assert normalized["o2_sat"] == 98
        assert normalized["mental_status"] == "normal"
        assert normalized["pain_score"] == 2

    def test_normalize_celsius_temperature(self):
        """Test normalizing temperature in Celsius."""
        readings = [
            VitalSignReading(
                vital_type=VitalSignType.TEMPERATURE,
                value=37.0,
                unit="°C",
                timestamp=datetime.now(),
                source="test",
                patient_id="test",
            ),
        ]

        normalized = normalize_vitals(readings)
        assert normalized["temp_c"] == 37.0


# =============================================================================
# Protocol Loader Tests
# =============================================================================


class TestProtocolLoader:
    """Tests for ProtocolLoader."""

    def test_load_protocol_file_not_found(self, tmp_path):
        """Test loading non-existent protocol."""
        loader = ProtocolLoader(str(tmp_path))

        with pytest.raises(FileNotFoundError, match="Protocol not found"):
            loader.load_protocol("nonexistent")

    def test_load_protocol_success(self, tmp_path):
        """Test loading valid protocol file."""
        protocol_data = {
            "protocol_name": "Test Protocol",
            "protocol_version": "1.0.0",
            "applies_to": ["test"],
            "screening_criteria": {
                "criteria": [
                    {
                        "parameter": "hr",
                        "condition": ">=",
                        "value": 100,
                        "points": 1,
                        "description": "Tachycardia",
                    }
                ],
                "threshold": 1,
            },
            "interventions": [
                {
                    "order": 1,
                    "action": "Test action",
                    "timing": "immediately",
                    "required": True,
                }
            ],
            "monitoring_requirements": {
                "vitals_frequency": "hourly",
                "reassessment": "every 4 hours",
            },
        }

        protocol_file = tmp_path / "test_protocol.json"
        protocol_file.write_text(json.dumps(protocol_data))

        loader = ProtocolLoader(str(tmp_path))
        protocol = loader.load_protocol("test_protocol")

        assert protocol.name == "Test Protocol"
        assert protocol.version == "1.0.0"
        assert len(protocol.screening_criteria) == 1
        assert len(protocol.interventions) == 1

    def test_list_available_protocols(self, tmp_path):
        """Test listing available protocols."""
        # Create some protocol files
        (tmp_path / "sepsis.json").write_text("{}")
        (tmp_path / "stroke.json").write_text("{}")
        (tmp_path / "not_a_protocol.txt").write_text("")

        loader = ProtocolLoader(str(tmp_path))
        protocols = loader.list_available_protocols()

        assert "sepsis" in protocols
        assert "stroke" in protocols
        assert "not_a_protocol" not in protocols

    def test_list_protocols_empty_directory(self, tmp_path):
        """Test listing protocols in empty directory."""
        loader = ProtocolLoader(str(tmp_path))
        protocols = loader.list_available_protocols()
        assert protocols == []

    def test_list_protocols_nonexistent_directory(self, tmp_path):
        """Test listing protocols when directory doesn't exist."""
        loader = ProtocolLoader(str(tmp_path / "nonexistent"))
        protocols = loader.list_available_protocols()
        assert protocols == []

    def test_validate_protocol_valid(self, sample_protocol):
        """Test validating a valid protocol."""
        loader = ProtocolLoader()
        errors = loader.validate_protocol(sample_protocol)
        assert errors == []

    def test_validate_protocol_missing_name(self, sample_protocol):
        """Test validating protocol with missing name."""
        sample_protocol.name = ""
        loader = ProtocolLoader()
        errors = loader.validate_protocol(sample_protocol)
        assert "Protocol must have a name" in errors

    def test_validate_protocol_duplicate_orders(self, sample_protocol):
        """Test validating protocol with duplicate intervention orders."""
        sample_protocol.interventions[1].order = 1  # Same as first
        loader = ProtocolLoader()
        errors = loader.validate_protocol(sample_protocol)
        assert "Intervention orders must be unique" in errors


# =============================================================================
# Protocol Checker Tests
# =============================================================================


class TestProtocolChecker:
    """Tests for ProtocolChecker."""

    def test_check_compliance_protocol_not_activated(self, sample_protocol):
        """Test compliance check when criteria not met."""
        checker = ProtocolChecker()
        patient_data = {
            "hr": 70,  # Normal
            "systolic_bp": 120,  # Normal
            "respiratory_rate": 14,  # Normal
            "mental_status": "normal",
        }

        result = checker.check_compliance(sample_protocol, patient_data)

        assert not result.protocol_activated
        assert result.activation_score < sample_protocol.screening_threshold
        assert result.alert_level == "NONE"

    def test_check_compliance_protocol_activated(self, sample_protocol, sample_patient_data):
        """Test compliance check when criteria met."""
        checker = ProtocolChecker()

        result = checker.check_compliance(sample_protocol, sample_patient_data)

        assert result.protocol_activated
        assert result.activation_score >= sample_protocol.screening_threshold
        assert result.threshold == sample_protocol.screening_threshold

    def test_check_compliance_with_intervention_status(self, sample_protocol, sample_patient_data):
        """Test compliance check with intervention status."""
        checker = ProtocolChecker()
        intervention_status = {
            "Draw blood cultures": {"completed": True},
            "Start IV fluids": {"completed": False, "time_due": None},
            "Administer antibiotics": {"completed": False, "time_due": None},
        }

        result = checker.check_compliance(sample_protocol, sample_patient_data, intervention_status)

        assert result.protocol_activated
        assert len(result.deviations) == 2  # Two pending
        assert "Draw blood cultures" in result.compliant_items

    def test_check_compliance_overdue_intervention(self, sample_protocol, sample_patient_data):
        """Test compliance check with overdue intervention."""
        checker = ProtocolChecker()
        past_time = datetime.now() - timedelta(hours=2)
        intervention_status = {
            "Draw blood cultures": {
                "completed": False,
                "time_due": past_time,
            },
        }

        result = checker.check_compliance(sample_protocol, sample_patient_data, intervention_status)

        assert result.alert_level == "CRITICAL"
        overdue = [d for d in result.deviations if d.status == ComplianceStatus.OVERDUE]
        assert len(overdue) == 1

    def test_evaluate_all_conditions(self, sample_protocol):
        """Test evaluation of all condition types."""
        checker = ProtocolChecker()

        # Test all comparison operators
        test_cases = [
            ({"test": 5}, "<=", 10, True),
            ({"test": 5}, ">=", 3, True),
            ({"test": 5}, "==", 5, True),
            ({"test": 5}, "!=", 10, True),
            ({"test": 5}, "<", 10, True),
            ({"test": 5}, ">", 3, True),
            ({"test": "confused"}, "altered", None, True),
            ({"test": "normal"}, "altered", None, False),
            ({"test": 10}, "altered", None, True),  # GCS < 15
            ({"test": 15}, "altered", None, False),  # GCS = 15
        ]

        for patient_data, condition, value, expected in test_cases:
            result = checker._evaluate_condition(patient_data.get("test"), condition, value)
            assert result == expected, f"Failed for condition {condition}"

    def test_evaluate_criterion_missing_parameter(self, sample_protocol):
        """Test evaluating criterion with missing parameter."""
        checker = ProtocolChecker()
        criterion = ProtocolCriterion(
            parameter="missing_param",
            condition=">=",
            value=100,
            points=1,
        )

        result = checker._evaluate_criterion(criterion, {})

        assert not result.met
        assert "not available" in result.reasoning

    def test_generate_recommendation_stable_patient(self, sample_protocol):
        """Test recommendation for stable patient."""
        checker = ProtocolChecker()
        patient_data = {"hr": 70, "systolic_bp": 120}

        result = checker.check_compliance(sample_protocol, patient_data)

        assert (
            "stable" in result.recommendation.lower()
            or "monitoring" in result.recommendation.lower()
        )


# =============================================================================
# Clinical Protocol Monitor Tests
# =============================================================================


class TestClinicalProtocolMonitor:
    """Tests for ClinicalProtocolMonitor."""

    def test_init_default(self):
        """Test default initialization."""
        monitor = ClinicalProtocolMonitor()
        assert monitor.active_protocols == {}
        assert monitor.patient_history == {}

    def test_init_custom_directory(self, tmp_path):
        """Test initialization with custom directory."""
        monitor = ClinicalProtocolMonitor(str(tmp_path))
        assert monitor.protocol_loader.protocol_dir == tmp_path

    @pytest.mark.asyncio
    async def test_analyze_missing_patient_id(self):
        """Test analyze with missing patient_id."""
        monitor = ClinicalProtocolMonitor()
        result = await monitor.analyze({"sensor_data": "{}"})
        assert "error" in result
        assert "patient_id" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_missing_sensor_data(self):
        """Test analyze with missing sensor_data."""
        monitor = ClinicalProtocolMonitor()
        result = await monitor.analyze({"patient_id": "12345"})
        assert "error" in result
        assert "sensor_data" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_no_active_protocol(self):
        """Test analyze without active protocol."""
        monitor = ClinicalProtocolMonitor()
        result = await monitor.analyze({"patient_id": "12345", "sensor_data": "{}"})
        assert "error" in result
        assert "No active protocol" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_with_loaded_protocol(self, sample_protocol, simple_json_data):
        """Test analyze with pre-loaded protocol."""
        monitor = ClinicalProtocolMonitor()
        monitor.active_protocols["12345"] = sample_protocol

        result = await monitor.analyze(
            {
                "patient_id": "12345",
                "sensor_data": simple_json_data,
                "sensor_format": "simple_json",
            }
        )

        assert "error" not in result
        assert result["patient_id"] == "12345"
        assert "protocol_compliance" in result
        assert "trajectory" in result
        assert "alerts" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_analyze_with_dict_sensor_data(self, sample_protocol):
        """Test analyze with dict sensor data (not JSON string)."""
        monitor = ClinicalProtocolMonitor()
        monitor.active_protocols["12345"] = sample_protocol

        result = await monitor.analyze(
            {
                "patient_id": "12345",
                "sensor_data": {
                    "hr": 110,
                    "systolic_bp": 95,
                    "respiratory_rate": 24,
                },
            }
        )

        assert "error" not in result
        assert result["current_vitals"]["hr"] == 110

    @pytest.mark.asyncio
    async def test_analyze_history_management(self, sample_protocol):
        """Test that patient history is managed correctly."""
        monitor = ClinicalProtocolMonitor()
        monitor.active_protocols["12345"] = sample_protocol

        # Run multiple analyses
        for i in range(5):
            await monitor.analyze(
                {
                    "patient_id": "12345",
                    "sensor_data": {"hr": 80 + i},
                }
            )

        assert len(monitor.patient_history["12345"]) == 5

    @pytest.mark.asyncio
    async def test_analyze_history_limit(self, sample_protocol):
        """Test that history is limited to 144 entries."""
        monitor = ClinicalProtocolMonitor()
        monitor.active_protocols["12345"] = sample_protocol
        # Pre-populate with 150 entries
        monitor.patient_history["12345"] = [{"hr": i} for i in range(150)]

        await monitor.analyze({"patient_id": "12345", "sensor_data": {"hr": 100}})

        # Should be trimmed to 144
        assert len(monitor.patient_history["12345"]) <= 144

    def test_generate_alerts_protocol_activated(self, sample_protocol):
        """Test alert generation when protocol is activated."""
        monitor = ClinicalProtocolMonitor()

        compliance = ProtocolCheckResult(
            protocol_activated=True,
            activation_score=3,
            threshold=2,
            criteria_results=[],
            deviations=[],
            compliant_items=[],
            alert_level="WARNING",
            recommendation="Protocol activated",
        )

        # Create mock trajectory
        from empathy_healthcare_plugin.monitors.monitoring.trajectory_analyzer import (
            TrajectoryPrediction,
        )

        trajectory = TrajectoryPrediction(
            trajectory_state="stable",
            estimated_time_to_critical=None,
            vital_trends=[],
            overall_assessment="Stable",
            confidence=0.9,
            recommendations=[],
        )

        alerts = monitor._generate_alerts(compliance, trajectory)

        assert len(alerts) >= 1
        assert any(a["type"] == "protocol_activated" for a in alerts)

    def test_generate_alerts_overdue_intervention(self, sample_protocol):
        """Test alert generation for overdue interventions."""
        monitor = ClinicalProtocolMonitor()

        deviation = ProtocolDeviation(
            intervention=ProtocolIntervention(
                order=1,
                action="Test action",
                timing="immediately",
            ),
            status=ComplianceStatus.OVERDUE,
            reasoning="Overdue",
        )

        compliance = ProtocolCheckResult(
            protocol_activated=True,
            activation_score=3,
            threshold=2,
            criteria_results=[],
            deviations=[deviation],
            compliant_items=[],
            alert_level="CRITICAL",
            recommendation="Intervention overdue",
        )

        from empathy_healthcare_plugin.monitors.monitoring.trajectory_analyzer import (
            TrajectoryPrediction,
        )

        trajectory = TrajectoryPrediction(
            trajectory_state="stable",
            estimated_time_to_critical=None,
            vital_trends=[],
            overall_assessment="Stable",
            confidence=0.9,
            recommendations=[],
        )

        alerts = monitor._generate_alerts(compliance, trajectory)

        assert any(a["type"] == "intervention_overdue" for a in alerts)
        assert any(a["severity"] == "critical" for a in alerts)

    def test_generate_alerts_trajectory_critical(self, sample_protocol):
        """Test alert generation for critical trajectory."""
        monitor = ClinicalProtocolMonitor()

        compliance = ProtocolCheckResult(
            protocol_activated=False,
            activation_score=0,
            threshold=2,
            criteria_results=[],
            deviations=[],
            compliant_items=[],
            alert_level="NONE",
            recommendation="",
        )

        from empathy_healthcare_plugin.monitors.monitoring.trajectory_analyzer import (
            TrajectoryPrediction,
        )

        trajectory = TrajectoryPrediction(
            trajectory_state="critical",
            estimated_time_to_critical="30 minutes",
            vital_trends=[],
            overall_assessment="Critical deterioration detected",
            confidence=0.85,
            recommendations=["Immediate intervention required"],
        )

        alerts = monitor._generate_alerts(compliance, trajectory)

        assert any(a["type"] == "trajectory_critical" for a in alerts)

    def test_generate_recommendations_deduplication(self, sample_protocol):
        """Test that recommendations are deduplicated."""
        monitor = ClinicalProtocolMonitor()

        compliance = ProtocolCheckResult(
            protocol_activated=True,
            activation_score=3,
            threshold=2,
            criteria_results=[],
            deviations=[],
            compliant_items=[],
            alert_level="WARNING",
            recommendation="Start monitoring",
        )

        from empathy_healthcare_plugin.monitors.monitoring.trajectory_analyzer import (
            TrajectoryPrediction,
        )

        trajectory = TrajectoryPrediction(
            trajectory_state="stable",
            estimated_time_to_critical=None,
            vital_trends=[],
            overall_assessment="Stable",
            confidence=0.9,
            recommendations=["Start monitoring", "Check vitals"],  # Duplicate
        )

        recommendations = monitor._generate_recommendations(compliance, trajectory, sample_protocol)

        # Should be deduplicated
        assert recommendations.count("Start monitoring") == 1


# =============================================================================
# Integration Tests
# =============================================================================


class TestHealthcarePluginIntegration:
    """Integration tests for the healthcare plugin."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """Test complete workflow from data to alerts."""
        # Create a test protocol
        protocol_data = {
            "protocol_name": "Test Sepsis",
            "protocol_version": "1.0.0",
            "applies_to": ["test"],
            "screening_criteria": {
                "criteria": [
                    {
                        "parameter": "hr",
                        "condition": ">=",
                        "value": 100,
                        "points": 2,
                    },
                    {
                        "parameter": "systolic_bp",
                        "condition": "<=",
                        "value": 100,
                        "points": 2,
                    },
                ],
                "threshold": 2,
            },
            "interventions": [
                {
                    "order": 1,
                    "action": "Start fluids",
                    "timing": "within 30 min",
                }
            ],
            "monitoring_requirements": {
                "vitals_frequency": "every 15 min",
                "reassessment": "hourly",
            },
        }

        (tmp_path / "test_sepsis.json").write_text(json.dumps(protocol_data))

        # Create monitor and load protocol
        monitor = ClinicalProtocolMonitor(str(tmp_path))
        monitor.load_protocol("12345", "test_sepsis")

        # Analyze patient data
        result = await monitor.analyze(
            {
                "patient_id": "12345",
                "sensor_data": json.dumps(
                    {
                        "patient_id": "12345",
                        "vitals": {"hr": 110, "systolic_bp": 85},
                    }
                ),
                "sensor_format": "simple_json",
            }
        )

        # Verify results
        assert result["patient_id"] == "12345"
        assert result["protocol"]["name"] == "Test Sepsis"
        assert result["protocol_compliance"]["activated"] is True
        assert len(result["alerts"]) >= 1
