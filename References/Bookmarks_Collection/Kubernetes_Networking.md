# Networking in Kubernetes

**Source URL:** https://carol-hsu.github.io/post/study/k8s_network/

**Date Fetched:** 2026-04-12

## Overview

Carol Hsu's blog post provides a comprehensive overview of Kubernetes networking, structured from infrastructure-level configurations to application-level management.

## Key Topics Covered

**Foundational Concepts:**
The author explains essential K8s abstractions including Namespaces (which isolate resources), Pods (smallest compute units with assigned IPs), Services (virtual networking endpoints for applications), and CustomResourceDefinitions (allowing custom resource types).

**Communication Methods:**
Two primary access routes exist: IP-based communication through Pod IPs (managed by Container Network Interface plugins) and Service IPs (virtual references within the cluster), plus domain-name resolution via CoreDNS for internal service discovery.

**Traffic Control:**
NetworkPolicy resources enforce ingress and egress rules on selected Pods, implementing "default-deny" isolation. As Hsu notes: "NetworkPolicy defines only _allowable_ traffics" once applied to a Pod.

**Load Balancing & Exposure:**
The LoadBalancer Service type simplifies cloud integration but inherits NodePort limitations. Advanced traffic management uses Gateway API (evolving from the deprecated Ingress API) and service mesh solutions like Istio and Linkerd, which deploy proxies alongside microservices to handle routing, retries, and security centrally.

**Future Direction:**
The post highlights the convergence between Gateway API and service mesh capabilities through initiatives like GAMMA, while acknowledging ongoing transitions in the Kubernetes ecosystem.
