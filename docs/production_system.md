
## Production Architecture

I've made a lot of assumptions about how this type of tool would/could be used...
* Cloud-based: All pathfinding, layout processing, and model logic run in the cloud using AWS services (e.g., ECS, Lambda, and S3).
* Edge data collection: Robots are edge devices that perform scans and send layout updates (e.g., rack changes) and position updates (current location) to the cloud via secure HTTP POST requests.
* Real-time synchronization: The cloud system continuously updates the `WarehouseLayoutModel` and `ConnectivityMap` to reflect the latest warehouse conditions.
* Task input from WMS: The Warehouse Management System can create and send operational tasks—such as pick, move, or restock requests—to the Pathfinding API.
* Pathfinding in the cloud: The Pathfinding API calculates optimal routes and robot instructions using the latest connectivity graph and returns them to the WMS.
* Closed feedback loop: Robots execute assigned instructions, report progress, and send updated status data back to the cloud, enabling continuous layout accuracy and task tracking through the dashboard.

Proposed data/flow architecture:
```
┌────────────────────────────────────┐
│          Robots (Edge)             │
│ • Perform hourly scans             │
│ • Send layout updates via HTTP POST│
│                                    │
│ Payload types:                     │
│  • Add / Update / Remove location  │
│ Each payload includes:             │
│  • Location ID, rackface, column   │
│  • Centroid (x,y,z), status, time  │
└────────────┬───────────────────────┘
             │  HTTPS (POST)
             ▼
┌──────────────────────────┐
│     Amazon API Gateway   │
│ • Public HTTPS endpoint  │
│ • Authenticates requests │
│ • Invokes Lambda function│
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│        AWS Lambda        │
│ • Validates and parses   │
│   robot message payloads │
│ • Adds timestamps        │
│ • Publishes to Kinesis   │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│   Amazon Kinesis Stream  │
│ • Buffers incoming data  │
│ • Triggers ECS processor │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Layout & Graph Processor │
│ • Docker container on ECS│
│ • Updates WarehouseLayout│
│ • Rebuilds Connectivity  │
│ • Saves to S3 &/or       │
│   SageMaker Feature Store│
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────────────────────────┐
│           Pathfinding Model API              │
│ • Docker container on ECS                    │
│ • Uses latest ConnectivityMap from S3        │
│ • Runs PathFinder    to compute paths        │
│ • Exposes REST endpoints:                    │
│     /optimal_path    – compute route         │
│     /assign_task     – plan & assign task    │
│     /layout_state    – current layout info   │
└────────────┬─────────────────────────────────┘
             │               
             │               
             ▼              
┌──────────────────────┐   
│ Warehouse Management │   
│ System (WMS)         │  
│ • Sends task requests│  
│   (e.g. pick, move)  │ 
│ • Receives optimal   │  
│   routes + robot     │  
│   instructions       │   
└──────────────────────┘   
```

## CI/CD Pipeline Strategy

**Goal:** ensure every change to the layout/graph/pathfinding stack is validated, packaged, and deployed safely. A representative pipeline would include:

CI:
GitHub Actions triggers on every PR/push (partially implemented in this repo already)...   
1. **Static Analysis** – `uv run poe lint`.
2. **Unit Tests** – `uv run poe test`.
3. **Integration Tests** – load sample layouts/tasks, run pathfinding end-to-end, compare expected routes/costs, runtimes.

CD:

4. **Artifact Build** – Tagged (e.g. commit hash) Docker image (layout/graph service + pathfinding API) pushed to ECR.
5. **Update** ECS task definition to use latest image (manually or automatically...), which replaces old tasks with updates. Think about blue/green deployment.


