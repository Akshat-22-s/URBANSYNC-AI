# UrbanSync AI

> **Next-generation autonomous civic command platform, mobility mesh & 3D spatial digital twin**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js: 14](https://img.shields.io/badge/Next.js-14_App_Router-black.svg)](https://nextjs.org/)
[![PostGIS: 16-3.4](https://img.shields.io/badge/PostGIS-16--3.4-336791.svg)](https://postgis.net/)
[![Redis: 7.2](https://img.shields.io/badge/Redis-7.2-DC382D.svg)](https://redis.io/)
[![Docker: Compose](https://img.shields.io/badge/Docker-Compose_v3.8-2496ED.svg)](https://www.docker.com/)

---

## 🌆 Table of Contents

1. [Platform Overview](#-platform-overview)
2. [Subsystem Architecture](#-subsystem-architecture)
   - [1. UrbanSync Core (Autonomous Civic Command)](#1-urbansync-core)
   - [2. SILN / LogPose Mobility (Stochastic Mobility Mesh)](#2-siln--logpose-mobility)
   - [3. Nirbhaya-Mesh Safety (Proactive Citizen Safety Matrix)](#3-nirbhaya-mesh-safety)
3. [Technology Stack](#-technology-stack)
4. [Mathematical Formulations](#-mathematical-foundations)
   - [SafePath Composite Safety Metric ($Z_s$)](#1-safepath-composite-safety-metric-z_s)
   - [SILN Stochastic Departure & Travel Time ($T$)](#2-siln-stochastic-departure--travel-time)
   - [Capacitated Vehicle Routing Problem with Time Windows (CVRP-TW)](#3-capacitated-vehicle-routing-problem-with-time-windows-cvrp-tw)
   - [Temporal Homography & 3D Spatial Camera Projection](#4-temporal-homography--3d-spatial-camera-projection)
5. [System Architecture Diagram](#-system-architecture-diagram)
6. [Quick Start & Setup](#-quick-start--setup)
7. [API Endpoints Reference](#-api-endpoints-reference)
8. [WebSocket Real-Time Channels](#-websocket-real-time-channels)
9. [Project Directory Layout](#-project-directory-layout)
10. [License](#-license)

---

## 🔭 Platform Overview

**UrbanSync AI** is a city-scale autonomous civic operations platform. It integrates municipal sensor streams, real-time vehicular telemetry, multi-modal passenger transit, dynamic waste management, and proactive citizen safety routing into an interactive **3D Spatial Digital Twin**.

By unifying operational research optimization algorithms with sub-second geospatial event dispatch, UrbanSync AI bridges the gap between reactive municipal dispatch and predictive urban logistics.

```
+---------------------------------------------------------------------------------------+
|                                3D Spatial Digital Twin                                |
|                        (Next.js 14 App Router + Three.js / R3F)                       |
+---------------------------------------------------------------------------------------+
                                           ▲
                                    WebSocket / REST
                                           ▼
+---------------------------------------------------------------------------------------+
|                               API Gateway & Hub (FastAPI)                             |
+--------------------------+------------------------------+-----------------------------+
|     UrbanSync Core       |     SILN / LogPose Mobility   |    Nirbhaya-Mesh Safety     |
| - Civic Operations       | - Stochastic Mobility Graph  | - SafePath Routing (Zs)     |
| - Waste Fleet (CVRP-TW)  | - Multi-Modal Routing        | - Dual Duress PIN Engine    |
| - Automated Dispatch     | - Dynamic Congestion (BPR)   | - UP112 CAD Dispatch Bridging|
+--------------------------+------------------------------+-----------------------------+
                                           ▲
                                    Redis Pub/Sub & Caching
                                           ▼
+---------------------------------------------------------------------------------------+
|                    Geospatial Relational Data Layer (PostgreSQL / PostGIS)            |
+---------------------------------------------------------------------------------------+
```

---

## 🏛️ Subsystem Architecture

### 1. UrbanSync Core
The municipal central nervous system responsible for autonomous resource allocation:
- **CVRP-TW Waste Routing**: Formulates dynamic solid waste collection as a Capacitated Vehicle Routing Problem with Time Windows. Bin fill levels are streamed from IoT ultrasonic level sensors, dynamically recalculating optimal collection vehicle paths via Google OR-Tools.
- **Incident Lifecycle Engine**: Automated aggregation, deduplication, and classification of civic complaints (e.g., road hazards, water leaks, traffic anomalies) with automated severity scoring and field personnel dispatch.
- **Unified Municipal Metrics**: Real-time aggregation of municipal key performance indicators including operational emissions, fleet fuel consumption, SLA adherence, and sensor health metrics.

### 2. SILN / LogPose Mobility
A Stochastic Interdependent Logistics Network designed for metropolitan transit synchronization:
- **Multi-Modal Route Planner**: Evaluates synchronized transfers across autonomous shuttles, metro rail, rapid bus transit, and pedestrian walking legs.
- **Stochastic Congestion Accounting**: Utilizes adaptive Bureau of Public Roads (BPR) delay curves coupled with stochastic variance models to calculate real-world arrival probability bounds.
- **Dynamic Departure Engine**: Computes departure recommendations based on real-time transit congestion, minimizing transit wait times and journey variance.

### 3. Nirbhaya-Mesh Safety
An integrated woman and citizen safety matrix combining mathematical pathfinding with emergency integration:
- **SafePath Graph Engine**: Calculates walking routes optimized not solely for minimal Euclidean distance, but for maximum safety composite score ($Z_s$), factoring in street lighting intensity, pedestrian crowd density, surveillance coverage, police outpost proximity, and historic crime incidence.
- **Dual-PIN Zero-Knowledge Duress Verification**:
  - `Safe PIN` (e.g., `1234`): Disarms safety timers, concludes monitoring normally.
  - `Duress PIN` (e.g., `9999`): Emulates normal PIN entry to bad actors on the device UI while silently escalating emergency priority, transmitting high-frequency GPS telemetry, and bridging directly to police CAD systems.
- **UP112 CAD Integration**: Direct webhook dispatch to state emergency response dispatch systems (UP112 CAD) with automatic location tracking, responder dispatch, and peer guardian mesh alerting.
- **Temporal Homography Vision Projection**: Projects CCTV vision telemetry into ground-plane digital twin spatial coordinates, creating live spatial footprints without storing invasive raw video feeds.

---

## 🛠️ Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **API & Gateway** | FastAPI | 0.109.0 | High-performance asynchronous REST & WebSocket hub |
| **ASGI Server** | Uvicorn | 0.27.0 | Lightning-fast ASGI web server implementation |
| **Frontend Framework** | Next.js (App Router) | 14.x | Server Components, strict TypeScript, responsive layouts |
| **3D Digital Twin** | Three.js & React Three Fiber | Latest | WebGL city visualization, spatial camera projections |
| **Styling & Icons** | Tailwind CSS & Lucide React | Latest | Modern responsive UI components & iconography |
| **Optimization Engine** | Google OR-Tools | 9.8.3296 | CVRP-TW and discrete combinatorial optimization |
| **Graph Network** | NetworkX & SciPy | 3.2.1 / 1.12.0 | Spatial graph traversal, Dijkstra/A* SafePath routing |
| **Computer Vision** | OpenCV Headless | 4.9.0.80 | Perspective projection & temporal homography calibration |
| **Message Broker** | Redis | 7.2 | Real-time Pub/Sub broker, spatial cache & live telemetry queue |
| **Database** | PostgreSQL + PostGIS | 16 / 3.4 | Spatio-temporal relational persistence & GIS queries |
| **ORM / Data Access** | SQLAlchemy (Async) & GeoAlchemy2 | 2.0.25 | Type-safe asynchronous spatial database queries |
| **Containerization** | Docker & Docker Compose | Compose v3.8 | Orchestrated multi-service container deployment |

---

## 📐 Mathematical Foundations

### 1. SafePath Composite Safety Metric ($Z_s$)

Every candidate edge $e = (u, v)$ in the pedestrian road network graph $G = (V, E)$ is evaluated using a normalized safety penalty metric $Z_s(e) \in [0, 1]$, where lower values indicate higher safety:

$$Z_s(e) = w_l \cdot \big(1 - \hat{L}(e)\big) + w_c \cdot \big(1 - \hat{C}(e)\big) + w_p \cdot \hat{P}(e) + w_h \cdot \hat{H}(e) + w_d \cdot \hat{D}(e)$$

Subject to the weight normalization constraint:
$$\sum_{k \in \{l, c, p, h, d\}} w_k = 1, \quad w_k \ge 0$$

#### Variable Definitions:
- $\hat{L}(e) \in [0, 1]$: Normalized lumen density of street illumination along edge $e$.
- $\hat{C}(e) \in [0, 1]$: Pedestrian footfall and crowd presence index along edge $e$.
- $\hat{P}(e) \in [0, 1]$: Normalized spatial distance to nearest staffed police booth, PCR patrol unit, or 24/7 commercial kiosk.
- $\hat{H}(e) \in [0, 1]$: Historic spatial crime severity heat index aggregated across spatio-temporal sliding windows.
- $\hat{D}(e) \in [0, 1]$: Real-time distress reports or active incidents logged within neighborhood radius $R$.

#### Route Cost Minimization:
Given source $s$ and destination $t$, the SafePath routing algorithm minimizes the composite travel cost function:

$$\mathcal{J}(P) = \sum_{e \in P} \text{Length}(e) \cdot \Big[1 + \lambda \cdot Z_s(e)\Big]$$

where $\lambda \ge 0$ represents the user's safety risk-aversion coefficient ($\lambda = 0$ corresponds to pure shortest-path Dijkstra).

---

### 2. SILN Stochastic Departure & Travel Time

The travel time $T(e, t)$ on road link $e$ at departure epoch $t$ is modeled as a non-linear function of volume-to-capacity ratios incorporating the modified Bureau of Public Roads (BPR) relationship augmented with stochastic shock factor $\xi$:

$$T(e, t) = T_0(e) \left[ 1 + \alpha \left(\frac{V(e, t)}{C(e)}\right)^\beta \right] + \sigma(e, t) \cdot \Phi^{-1}(\gamma)$$

#### Parameter Definitions:
- $T_0(e)$: Free-flow link traversal duration.
- $V(e, t)$: Projected vehicle volume at time $t$.
- $C(e)$: Dynamic road carrying capacity.
- $\alpha, \beta$: Calibration parameters (empirically $\alpha = 0.15, \beta = 4.0$).
- $\sigma(e, t)$: Stochastic variance of link travel time due to micro-congestions.
- $\Phi^{-1}(\gamma)$: Inverse cumulative distribution function of standard normal distribution for reliability confidence level $\gamma \in (0, 1)$ (e.g., $\gamma = 0.95$ for 95% on-time arrival guarantee).

Optimal departure epoch $t^* \in [t_{\text{min}}, t_{\text{max}}]$ satisfies:
$$t^* = \arg\min_{t} \left\{ \mathbb{E}[T(P, t)] + \theta_e \max(0, t_{\text{target}} - (t + T(P, t))) + \theta_l \max(0, (t + T(P, t)) - t_{\text{target}}) \right\}$$

where $\theta_e$ and $\theta_l$ represent early and late arrival penalty multipliers respectively.

---

### 3. Capacitated Vehicle Routing Problem with Time Windows (CVRP-TW)

Dynamic solid waste collection and civic maintenance dispatch are formulated as integer programming problems solved via Google OR-Tools:

$$\min \sum_{k \in K} \sum_{i \in V} \sum_{j \in V} c_{ij} \, x_{ijk}$$

#### Constraints:
1. **Flow Conservation & Single Visit:**
   $$\sum_{k \in K} \sum_{j \in V, j \neq i} x_{ijk} = 1 \quad \forall i \in V \setminus \{0\}$$
2. **Vehicle Depot Departure & Return:**
   $$\sum_{j \in V \setminus \{0\}} x_{0jk} = 1 \quad \forall k \in K, \qquad \sum_{i \in V \setminus \{0\}} x_{i0k} = 1 \quad \forall k \in K$$
3. **Vehicle Capacity Bounds:**
   $$\sum_{i \in V \setminus \{0\}} q_i \sum_{j \in V} x_{ijk} \le Q_k \quad \forall k \in K$$
   where $q_i$ is the waste demand (current bin volume $v_i \cdot \text{density}$) and $Q_k$ is the maximum payload capacity of vehicle $k$.
4. **Time Window Feasibility:**
   $$a_i \le \tau_{ik} \le b_i \quad \forall i \in V, \, k \in K$$
   where $[\,a_i, b_i\,]$ is the operational collection window and $\tau_{ik}$ represents the service start time at node $i$ by vehicle $k$.
5. **Subtour Elimination & Time Propagation:**
   $$\tau_{ik} + s_i + t_{ij} - M(1 - x_{ijk}) \le \tau_{jk} \quad \forall i, j \in V, \, k \in K, \, j \neq 0$$
   where $s_i$ is the service duration at bin $i$, and $M$ is a sufficiently large positive scalar.

---

### 4. Temporal Homography & 3D Spatial Camera Projection

To convert camera frame coordinate pairs $\mathbf{p}_c = [u, v, 1]^T$ into world ground-plane coordinates $\mathbf{P}_w = [X, Y, 0, 1]^T$ on the 3D digital twin without compromising personal privacy:

$$\mathbf{p}_c \sim \mathbf{K} \left[ \mathbf{R}(t) \;\middle|\; \mathbf{t}(t) \right] \mathbf{P}_w$$

Expanding planar transformation yields the temporal homography matrix $\mathbf{H}(t) \in \mathbb{R}^{3 \times 3}$:

$$\begin{bmatrix} X \\ Y \\ 1 \end{bmatrix} \sim \mathbf{H}(t)^{-1} \begin{bmatrix} u \\ v \\ 1 \end{bmatrix} = \begin{bmatrix} h_{11}(t) & h_{12}(t) & h_{13}(t) \\ h_{21}(t) & h_{22}(t) & h_{23}(t) \\ h_{31}(t) & h_{32}(t) & h_{33}(t) \end{bmatrix}^{-1} \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}$$

Intrinsic camera calibration matrix $\mathbf{K}$ and extrinsic rotational/translational adjustments $[\mathbf{R}(t) \mid \mathbf{t}(t)]$ are continually recalibrated using stationary ground control markers (GCPs). This projects crowd velocity vectors directly onto the digital twin canvas in real time.

---

## 🔄 System Architecture Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen / App
    participant Client as Next.js 3D Twin
    participant Gateway as FastAPI Gateway
    participant Redis as Redis Pub/Sub
    participant PostGIS as PostGIS DB
    participant ORTools as OR-Tools Solver
    actor Police as UP112 CAD Service

    %% Safety Flow
    Citizen->>Client: Request Safe Route (Origin, Destination)
    Client->>Gateway: POST /api/v1/safety/safe-route
    Gateway->>PostGIS: Query road network with lighting, crowd & crime metrics
    PostGIS-->>Gateway: Graph edges with safety attributes
    Gateway->>Gateway: Compute Zs-weighted Dijkstra Path
    Gateway-->>Client: SafePath GeoJSON + Safety Score Breakdown

    %% Duress Trigger
    Citizen->>Client: Enters Silent Duress PIN (9999)
    Client->>Gateway: POST /api/v1/safety/verify-pin {pin: "9999"}
    Gateway->>Gateway: Check PIN against Zero-Knowledge Hash
    Note over Gateway: Silent Alarm Activated
    Gateway->>Redis: Publish to "safety:sos"
    Gateway->>Police: Webhook Dispatch to UP112 CAD with Live GPS
    Gateway-->>Client: {status: "ok", mode: "disarmed"} (Decoy UI)

    %% Fleet CVRP Flow
    Redis->>Gateway: Sensor tick (Bin fill levels > 85%)
    Gateway->>ORTools: Formulate CVRP-TW (Depot, Bins, Fleets)
    ORTools-->>Gateway: Optimized Routes & Timings
    Gateway->>PostGIS: Persist updated vehicle itineraries
    Gateway->>Redis: Publish to "cvrp:routes"
    Redis->>Client: Real-time 3D waste truck route animation
```

---

## 🚀 Quick Start & Setup

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (v24.0+)
- [Docker Compose](https://docs.docker.com/compose/) (v2.20+)
- *Optional for local dev without Docker:* Node.js 20+, Python 3.11+, PostgreSQL with PostGIS extension, Redis 7.

### 1. Clone & Environment Configuration

```bash
# Clone repository
git clone https://github.com/urbansync-ai/urbansync.git
cd urbansync

# Create environment file from template
cp .env.example .env
```

Review and adjust variables in `.env` if desired:
```ini
POSTGRES_USER=urbansync
POSTGRES_PASSWORD=changeme_in_production
POSTGRES_DB=urbansync_db
DATABASE_URL=postgresql+asyncpg://urbansync:changeme_in_production@postgis:5432/urbansync_db
REDIS_URL=redis://redis:6379/0
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8000
UP112_DISPATCH_ENDPOINT=https://up112-cad.example.gov.in/api/dispatch
DURESS_SAFE_PIN=1234
DURESS_TRIGGER_PIN=9999
```

### 2. Launch with Docker Compose

```bash
# Build and start all services in detached mode
docker-compose up --build -d

# Verify all containers are healthy
docker-compose ps
```

### 3. Service Access Endpoints

- **3D Spatial Digital Twin UI:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI OpenAPI Schema:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **Gateway Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **PostgreSQL / PostGIS Port:** `localhost:5432`
- **Redis In-Memory Broker Port:** `localhost:6379`

### 4. Running Without Docker (Local Development)

<details>
<summary>Click to view manual installation steps</summary>

#### Start Gateway (FastAPI):
```bash
cd services/gateway
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Start Client (Next.js):
```bash
cd client
npm install
npm run dev
```
</details>

---

## 📡 API Endpoints Reference

### UrbanSync Core

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness and service readiness check |
| `GET` | `/api/v1/core/metrics` | Real-time municipal KPIs, emissions, and fleet statuses |
| `GET` | `/api/v1/core/incidents` | List active civic complaints and anomalies |
| `POST` | `/api/v1/core/incidents` | Report a new civic incident with geo-coordinates |
| `GET` | `/api/v1/core/bins` | Retrieve all waste bins with current fill percentages |
| `POST` | `/api/v1/core/cvrp/optimize` | Trigger OR-Tools CVRP-TW route calculation |
| `GET` | `/api/v1/core/cvrp/routes` | Fetch latest active collection routes for waste fleet |

### SILN / LogPose Mobility

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/mobility/itinerary` | Multi-modal travel route planner with stochastic transfer times |
| `GET` | `/api/v1/mobility/congestion` | Fetch dynamic edge congestion indices and BPR delay metrics |
| `POST` | `/api/v1/mobility/departure-optimizer` | Calculate optimal departure epoch given target arrival window |
| `GET` | `/api/v1/mobility/vehicles` | Real-time vehicle positions, velocities, and capacities |

### Nirbhaya-Mesh Safety

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/safety/safe-route` | Compute SafePath route minimizing safety penalty $Z_s$ |
| `POST` | `/api/v1/safety/sos` | Trigger emergency SOS beacon across mesh & responders |
| `POST` | `/api/v1/safety/verify-pin` | Dual PIN check (Safe vs Silent Duress trigger PIN) |
| `POST` | `/api/v1/safety/check-in` | Update active guardian safety timer countdown |
| `GET` | `/api/v1/safety/guardians` | List designated safety guardians and peer responders |
| `POST` | `/api/v1/safety/cad/dispatch` | Direct UP112 CAD webhook bridge for dispatch escalation |

### Simulator Controls

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/simulator/start` | Start citizen, vehicle, and bin fill telemetry simulation |
| `POST` | `/api/v1/simulator/stop` | Pause synthetic simulation loop |
| `POST` | `/api/v1/simulator/inject-incident` | Inject synthetic emergency or traffic anomaly |

---

## ⚡ WebSocket Real-Time Channels

UrbanSync AI provides real-time bi-directional streaming over `ws://<host>:8000/ws`.

| Channel Name | Flow | Payload Structure | Purpose |
| :--- | :--- | :--- | :--- |
| `telemetry:citizen` | Server $\rightarrow$ Client | `{"citizen_id": str, "lat": float, "lng": float, "speed": float, "safety_score": float}` | Real-time crowd heatmaps and citizen movements |
| `telemetry:vehicle` | Server $\rightarrow$ Client | `{"vehicle_id": str, "type": "waste"\|"bus"\|"police", "lat": float, "lng": float, "capacity_pct": float}` | Live vehicular location tracking on 3D twin |
| `safety:sos` | Bidirectional | `{"alert_id": str, "user_id": str, "lat": float, "lng": float, "is_duress": bool, "timestamp": int}` | Immediate emergency broadcast & silent alarm alerts |
| `cvrp:routes` | Server $\rightarrow$ Client | `{"fleet_id": str, "waypoints": [[lat, lng]], "total_distance_km": float, "estimated_duration_min": float}` | Live update of OR-Tools computed waste routes |
| `incidents:feed` | Server $\rightarrow$ Client | `{"incident_id": str, "category": str, "severity": int, "lat": float, "lng": float, "status": str}` | Municipal incident triage updates |
| `twin:camera_projection` | Server $\rightarrow$ Client | `{"camera_id": str, "homography_matrix": [[float]], "ground_polygons": [[[lat, lng]]]}` | Dynamic camera frustum & ground footprint sync |

---

## 📂 Project Directory Layout

```
URBANSYNC AI/
├── docker-compose.yml              # Multi-container orchestration specification
├── .env.example                    # Template environment variables
├── README.md                       # Architectural documentation & reference
├── services/
│   ├── gateway/
│   │   ├── Dockerfile              # FastAPI Python 3.11 container definition
│   │   ├── requirements.txt        # Gateway dependencies (FastAPI, OR-Tools, etc.)
│   │   └── main.py                 # Core API & WebSocket gateway entrypoint
│   └── simulator/
│       ├── requirements.txt        # Simulator dependencies (NumPy, Redis, HTTPX)
│       └── sim_engine.py           # Synthetic municipal telemetry generator
└── client/
    ├── Dockerfile                  # Next.js 14 Alpine production container
    ├── package.json                # Frontend dependencies & scripts
    └── app/                        # Next.js 14 App Router (3D Twin & Dashboards)
```

---

## 📄 License

This project is licensed under the terms of the **MIT License**. See the [LICENSE](LICENSE) file for complete details.
