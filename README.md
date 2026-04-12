# The Scaffolding - Bug Bounty & CTF Harness


## Agent-Agnostic Offensive Orchestration

The Scaffolding is a framework designed to automatically solve Capture The Flag (CTF) challenges and hunt for bugs, by bridging the gaps between high-level security reasoning and deterministic execution. By utilizing the Model Context Protocol (MCP) and a persistent self-improving agent documentation, it enables autonomous agents to solve complex, multi-stage CTF challenges and perform deep-dive bug bounty research. You can use the setup to plug and play into any of your AI agents (Claude Code, Github Copilot, Codex, Gemini, OpenCode etc.)

## Overview

This project provides a structured framework for security researchers to organize and execute CTF challenges and bug bounty assessments using AI-assisted workflows.

The following is a demo of an agent using The Scaffolding to solve a hard web challenge.

https://github.com/user-attachments/assets/5774267e-0e5c-414b-99d3-1b9de2bc0444

## Architecture

<img width="865" height="873" alt="Screenshot 2026-04-11 021928" src="https://github.com/user-attachments/assets/03f7bd4d-addc-467b-abda-a074f03db30c" />


## Project Structure

```
(root)/
├── .agents/              # Agent skill definitions
├── .cursor/              # Cursor IDE configuration
├── .gemini/              # Gemini CLI configuration
├── .github/              # GitHub integration
├── .opencode/           # OpenCode agent configuration
├── kali-mcp/            # Kali Linux MCP server integration
├── AGENTS.md            # Shared agent instructions
├── HUMAN.md             # Human-facing documentation
└── README.md
```

## Skills

The harness includes specialized skills for different security domains:

- **agent-setup**: Tool readiness and dependency checks
- **agent-calibration**: Workflow optimization and feedback
- **crypto**: Cryptographic challenges (encoding, RSA, EC, hashes)
- **forensics**: File, memory, network, and multimedia forensics
- **mobile**: Mobile application security testing
- **network**: Network reconnaissance and assessment
- **pwn**: Binary exploitation (stack, heap, format strings)
- **recon**: Target reconnaissance and discovery
- **reverse-engineering**: Binary analysis and RE
- **web**: Web application security testing

## Usage

This harness is designed to be used with most . Each skill can be activated as needed during different phases of a CTF or bug bounty assessment.

## kali-mcp

The `kali-mcp/` subdirectory contains a Model Context Protocol server for Kali Linux tools, enabling AI-assisted execution of security tools within the harness.

## Notes

- This project uses AI coding tools for research and educational purposes
- All assessments should only target systems you are authorized to test
