import pandera as pa
from pandera import Column, DataFrameSchema

patient_feature_schema = DataFrameSchema(
    {
        "age": Column(int, pa.Check.in_range(0, 120)),
        "gender": Column(int, pa.Check.isin([0, 1])),
        "num_encounters": Column(int, pa.Check.ge(0)),
        "avg_los": Column(float, pa.Check.ge(0)),
        "creatinine": Column(float, pa.Check.ge(0)),
        "heart_rate": Column(float, pa.Check.in_range(30, 250)),
        "systolic_bp": Column(float, pa.Check.in_range(50, 250)),
    }
)
