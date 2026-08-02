import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
import pandas as pd

import native_simulator
import parameters
import simulator
import utility


def make_data() -> utility.ElectricData:
    values = {
        "Net Import": [2.0, 2.0, 2.0, 2.0],
        "Thermal": [3.0, 3.0, 3.0, 3.0],
        "Nuclear": [0.0, 0.0, 0.0, 0.0],
        "Storage": [0.0, 0.0, 0.0, 0.0],
        "Self-consumption": [0.0, 0.0, 0.0, 0.0],
        "Photovoltaic": [0.0, 4.0, 4.0, 0.0],
        "Hydro": [0.0, 0.0, 0.0, 0.0],
        "Wind": [0.0, 0.0, 0.0, 0.0],
        "Geothermal": [0.0, 0.0, 0.0, 0.0],
        "Import": [2.0, 2.0, 2.0, 2.0],
        "Export": [0.0, 0.0, 0.0, 0.0],
        "Consumption": [5.0, 5.0, 5.0, 5.0],
    }
    return utility.ElectricData(
        power_item={key: np.asarray(value, dtype=np.float64) for key, value in values.items()},
        start=pd.Timestamp("2025-01-01T00:00:00"),
        end=pd.Timestamp("2025-01-01T01:00:00"),
    )


@unittest.skipUnless(native_simulator.cpp_available(), "C++ extension has not been built")
class NativeEngineParityTests(unittest.TestCase):
    def test_scenario_matches_python_reference(self):
        data = make_data()
        original_engine = os.environ.get("TERNA_SIMULATION_ENGINE")
        try:
            os.environ["TERNA_SIMULATION_ENGINE"] = "python"
            expected = simulator.simulate_alternative_scenario(data, 10.0, 2.0, 1.0, False)
            os.environ["TERNA_SIMULATION_ENGINE"] = "cpp"
            actual = simulator.simulate_alternative_scenario(data, 10.0, 2.0, 1.0, False)
        finally:
            if original_engine is None:
                os.environ.pop("TERNA_SIMULATION_ENGINE", None)
            else:
                os.environ["TERNA_SIMULATION_ENGINE"] = original_engine

        for source in parameters.SOURCES + parameters.OTHER_POWER_ITEMS:
            np.testing.assert_allclose(actual.power_item[source], expected.power_item[source])
        self.assertAlmostEqual(actual.energy_item["Total Production"][1], expected.energy_item["Total Production"][1])

    def test_generation_csv_handles_repeated_dst_hour(self):
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "generation.csv"
            csv_path.write_text(
                "Date,Generation,Source\n"
                "26/10/2025 02:00:00,1.0,Thermal\n"
                "26/10/2025 02:00:00,2.0,Thermal\n"
                "26/10/2025 02:15:00,3.0,Thermal\n",
                encoding="utf-8",
            )
            original_engine = os.environ.get("TERNA_SIMULATION_ENGINE")
            try:
                os.environ["TERNA_SIMULATION_ENGINE"] = "python"
                expected = utility.load_generation_data_from_csv(csv_path)
                os.environ["TERNA_SIMULATION_ENGINE"] = "cpp"
                actual = utility.load_generation_data_from_csv(csv_path)
            finally:
                if original_engine is None:
                    os.environ.pop("TERNA_SIMULATION_ENGINE", None)
                else:
                    os.environ["TERNA_SIMULATION_ENGINE"] = original_engine

            self.assertEqual(actual.start, expected.start)
            self.assertEqual(actual.end, expected.end)
            np.testing.assert_allclose(
                actual.power_item["Thermal"], expected.power_item["Thermal"], equal_nan=True
            )

    def test_decarbonization_surface_matches_python_reference(self):
        data = make_data()
        original_engine = os.environ.get("TERNA_SIMULATION_ENGINE")
        original_workers = os.environ.get("TERNA_SURFACE_WORKERS")
        try:
            os.environ["TERNA_SIMULATION_ENGINE"] = "python"
            expected = simulator.compute_decarbonization_surface(data, 2.0, 1.0, 10.0)
            os.environ["TERNA_SIMULATION_ENGINE"] = "cpp"
            os.environ["TERNA_SURFACE_WORKERS"] = "2"
            actual = simulator.compute_decarbonization_surface(data, 2.0, 1.0, 10.0)
        finally:
            if original_engine is None:
                os.environ.pop("TERNA_SIMULATION_ENGINE", None)
            else:
                os.environ["TERNA_SIMULATION_ENGINE"] = original_engine
            if original_workers is None:
                os.environ.pop("TERNA_SURFACE_WORKERS", None)
            else:
                os.environ["TERNA_SURFACE_WORKERS"] = original_workers

        self.assertEqual(len(actual), len(expected))
        np.testing.assert_allclose(actual, expected)


if __name__ == "__main__":
    unittest.main()