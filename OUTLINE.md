## Team Name
*BMC IS BOOMING*

## Team Members
- Aditya Dawadikar
- Udayan Atreya
- Harshavardhan Raghavendra Valmiki
- Sohan Vallapureddy

## Focus Area
*Agentic AI for Autonomous Infrastructure Observability and Control*
- Intelligent monitoring, analysis, and autonomous remediation for data center hardware (with LLM-powered agents).

## Description of the Problem

As data centers scale, traditional infrastructure management tools are increasingly inadequate. While legacy platforms provide monitoring and visualization, they are overwhelmingly reactive, fragmented, and require high manual intervention for fault detection and system recovery. This results in delays, human error, and missed opportunities for optimization.

*Current challenges:*
- Lack of real-time insight and predictive detection for hardware faults.
- Limited (if any) use of intelligent, autonomous agents for controlling hardware or remediating issues.
- Visualization and observability are treated as endpoints, not as enablers for action.

## What We’re Building

We are building an *agentic, AI-powered platform* that couples deep observability with autonomous, intelligent control:
- Hardware telemetry is continuously ingested and analyzed.
- Instead of just dashboards, an LLM-powered agent interprets, reasons, and acts—triggering controls, remediations, or optimizations with minimal human intervention.
- Observability is harnessed as a substrate for proactive, autonomous action—not just monitoring.

## Features to Implement

- *Real-Time Telemetry Ingestion:* Pulls frequent signals from BMCs via Redfish protocol.
- *Adaptive/Agentic Signal Processing:* Context-aware agent applies rules and LLM-driven pattern recognition to classify, predict, and react to hardware events and telemetry trends.
- *Intelligent Autonomous Control:* Agent triggers control endpoints, initiates automated remediation, and conducts self-healing operations as required.
- *LLM-Powered Conversational Interface:* Operators can query the agent about any system event, root cause, or ongoing remediation in natural language.
- *Unified Visualization:* Dashboards (Grafana) and real-time logs are provided as transparency and debugging aids—not as the primary driver of action.
- *Seamless Data Lifecycle:* All telemetry and logs are archived and snapshot in transactional DB/S3 for both real-time and deep historical analytics.

## Additional Context

- *Technical Stack:* LangChain, Gemini, FastAPI, React, MongoDB, AWS S3, Prometheus, Grafana, 
- The core agentic logic combines rule-based and LLM-powered automation, with hooks for autonomous control and human-in-the-loop where needed.
- Visualization and conversational UIs ensure system transparency, explainability, and trust.

## Day 1 Plan
1. Implement core ingestion/control pipeline.
2. Implement Visualization Dashboards

## Day 2 Plan
1. Provide conversational capabilities
2. Trigger RedFish control APIs (mock)

## Day 3 Plan
1. Refactoring/Cleanup
2. Testing (Sanity)

---
# Architecture

[Details TBD]

*Architecture Diagram:*  
![alt text](https://github.com/Axiado-Hackathon/axiado-hackathon-repo-bmc-is-booming/blob/main/AxiadoHackathonArchitecture.png)
