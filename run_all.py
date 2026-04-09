import time
from src.generator.generate_dim_towers import build_dim_towers
from src.generator.generate_dim_customers import build_dim_customers
from src.generator.generate_dim_time import build_dim_time
from src.generator.generate_dim_weather import build_dim_weather
from src.generator.generate_dim_incidents import build_dim_incidents
from src.generator.generate_fact_network_events import build_fact_network_events


def run_step(name, fn, **kwargs):
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}")
    start = time.time()
    result = fn(**kwargs)
    elapsed = time.time() - start
    print(f"  Done in {elapsed:.1f}s")
    return result


if __name__ == "__main__":
    total_start = time.time()

    run_step("DIM_TOWERS", build_dim_towers)
    run_step("DIM_CUSTOMERS", build_dim_customers)
    run_step("DIM_TIME", build_dim_time)
    run_step("DIM_WEATHER", build_dim_weather)
    run_step("DIM_INCIDENTS", build_dim_incidents)
    run_step("FACT_NETWORK_EVENTS", build_fact_network_events)

    total = time.time() - total_start
    print(f"\nAll generators completed in {total:.1f}s")
    print("Output files are in data/generated/")
