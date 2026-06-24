# 🌍 Eco Footprint Analyzer

**Eco Footprint Analyzer** is an intelligent, multi-agent AI application designed to help users calculate, understand, and reduce their carbon footprint. Powered by Google's Agent Development Kit (ADK) and Gemini, it seamlessly processes raw utility data to generate actionable climate impact plans. Built with a core focus on empowering global sustainability, it provides deeply localized insights to drive climate action for any nation. For instance, its detailed regional factors actively support monumental national goals like India's "Panchamrit" vision of achieving Net Zero emissions by 2070.

## 🏗️ Agent Architecture

The application uses an orchestrated multi-agent workflow to securely process user data. Below is the visual output from the ADK Playground:

![Agent Architecture Graph](./adk_graph.png)

### Logical Workflow Details

> **Note:** The code block below automatically renders as a beautiful graphical flowchart when this README is viewed on GitHub or a compatible Markdown viewer.

```mermaid
graph TD
    classDef eco fill:#e6ffe6,stroke:#4caf50,stroke-width:2px,color:#2e7d32;
    classDef safe fill:#e8f5e9,stroke:#81c784,stroke-width:2px,color:#1b5e20;
    classDef alert fill:#ffebee,stroke:#ef5350,stroke-width:2px,color:#c62828;
    classDef mcp fill:#fff3e0,stroke:#ffb74d,stroke-width:2px,color:#e65100;
    classDef final fill:#a5d6a7,stroke:#2e7d32,stroke-width:3px,color:#000000,font-weight:bold;

    User([👤 User Input: Utility Data]) --> Security[🛡️ Security Checkpoint<br>Redact PII & Prevent Injection]
    Security -- safe --> HITL1[🌍 Ask Country Node<br>HITL]
    HITL1 --> DataAnalyst[📊 Data Analyst Agent<br>Extract & Summarize]
    DataAnalyst -.->|Fetches data| MCP[(🔌 MCP Server)]
    DataAnalyst --> ClimateImpact[🌱 Climate Impact Agent<br>Calculate Footprint]
    ClimateImpact -.->|Fetches emission factors| MCP
    ClimateImpact --> HITL2[✅ Final Approval Node<br>HITL]
    HITL2 --> Final[🌿 Climate Action Plan]
    Security -- error --> Blocked((🛑 Request Blocked))

    class User,HITL1,HITL2 eco;
    class Security,DataAnalyst,ClimateImpact safe;
    class MCP mcp;
    class Final final;
    class Blocked alert;
```

### 🌟 Key Features
- **Data Analysis Agent:** Automatically extracts and summarizes utility and usage data.
- **Climate Impact Agent:** Calculates precise carbon footprint metrics (kg CO2) based on region-specific emission factors.
- **Privacy-First Security:** Built-in security checkpoints to automatically redact PII (Aadhaar, PAN, SSN, Emails, etc.) and block prompt injection attacks.
- **Human-in-the-Loop (HITL):** Interactively requests user location and requires explicit human approval before finalizing the climate action plan.
- **MCP Integration:** Uses the Model Context Protocol (MCP) to seamlessly fetch real-time emission factors and utility data.

---

## 💻 Local Development

Before running the agent locally, ensure you have the `uv` package manager installed.

**1. Install dependencies:**
```bash
agents-cli install
```

**2. Launch the interactive playground:**
```bash
agents-cli playground
```
This will start a local web server where you can interact with the Eco Footprint Analyzer. Any changes you make to `app/agent.py` will auto-reload.

---
## 🎨 Project Assets

### Cover Banner
![Cover Page Banner](./assets/cover_page_banner.png)

### Workflow Diagram
![Architecture Diagram](./assets/architecture_diagram.png)

---
