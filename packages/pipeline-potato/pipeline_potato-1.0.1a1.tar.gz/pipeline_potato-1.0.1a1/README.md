# 🥔 Pipeline Potato

**Pipeline Potato** is a lightweight, decorator-based **Asynchronous Dataflow Framework** for Python. It is designed to simplify the creation of high-concurrency ETL pipelines, specifically optimized for I/O-bound workloads like API orchestration, cloud storage scraping, and large-scale data migration.


---

## ✨ Key Features

* **Declarative Concurrency:** Control the throughput of individual steps using simple decorators (`@step`, `@tree_traversal`).
* **Automatic Back-pressure:** Built-in `buffer_size` management ensures your memory stays lean, even when producers are faster than consumers.
* **Async-First:** Built from the ground up for `asyncio`, making it highly efficient for thousands of concurrent network connections.
* **Zero Boilerplate:** No complex worker management or manual queue handling. Just define your logic and let the "Potato" handle the distribution.

---

## 🛠 At a Glance

```python
@step(
    concurrency=50, 
    buffer_size=100, 
    page_size=10
)
async def process_data(p: APotato, payload: list):
    # This step runs 50 instances concurrently
    # It automatically handles batching based on your page_size
    result = await call_external_api(payload)
    
    # Pass the results to the next stage in the pipeline.
    # This call blocks until space is available in next_step's buffer queue.
    # Each step has its own buffer (controlled by buffer_size) to store payloads.
    # Execution resumes only after all results are pushed to the buffer.
    await p(next_step, [result])
```

---

## 📖 Example: Downloading AWS Permissions

This example demonstrates how to build a pipeline that fetches all AWS service permissions by crawling AWS's public service reference API, available here: https://servicereference.us-east-1.amazonaws.com/v1/service-list.json

```python
import asyncio
import json
import time
import aiohttp
from pipeline_potato import APotato, pipeline
from pipeline_potato.steps import entry_point, step


class AwsPermissionsCrawler:
    aiohttp_session = None
    total_services = 0
    total_actions = 0


@entry_point
async def start_aws_discovery(p: APotato) -> None:
    """The entry point fetches the master service list."""
    url = "https://servicereference.us-east-1.amazonaws.com/v1/service-list.json"

    async with AwsPermissionsCrawler.aiohttp_session.get(url) as response:
        services = json.loads(await response.text())

        for service_info in services:
            payload = (service_info["service"], service_info["url"])
            await p(fetch_service_details, [payload])


@step(
    concurrency=5,    # Run up to 5 HTTP requests in parallel
    buffer_size=100,  # Prevent memory bloat by capping the input queue
    page_size=1       # Process one service per task instance
)
async def fetch_service_details(_: APotato, payload: list) -> None:
    """Fetch actions for each AWS service."""
    service_name, url = payload[0]

    async with AwsPermissionsCrawler.aiohttp_session.get(url) as response:
        data = json.loads(await response.text())
        actions = data.get("Actions", [])

        print(f"✅ {service_name}: {len(actions)} actions")
        AwsPermissionsCrawler.total_services += 1
        AwsPermissionsCrawler.total_actions += len(actions)


async def main() -> None:
    start_time = time.time()
    connector = aiohttp.TCPConnector(limit=0, limit_per_host=0)

    async with aiohttp.ClientSession(connector=connector) as session:
        AwsPermissionsCrawler.aiohttp_session = session
        await pipeline(start_aws_discovery)

    duration = time.time() - start_time
    print(f"Done! {AwsPermissionsCrawler.total_actions} actions across {AwsPermissionsCrawler.total_services} services in {duration:.2f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
```

**What's happening here:**

1. **Entry Point (`@entry_point`)**: Fetches the master list of AWS services and dispatches each service to the next step.
2. **Worker Step (`@step`)**: Processes each service with controlled concurrency (5 parallel requests), fetching the detailed actions list.
3. **Back-pressure**: The `buffer_size=100` ensures that if `fetch_service_details` falls behind, the entry point will automatically slow down.