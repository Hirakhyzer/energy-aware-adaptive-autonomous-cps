# Research questions, hypotheses and contribution boundaries

**RQ1:** Under what combinations of workload, path geometry and sensor noise does joint adaptation of sensing, computation and control reduce modeled energy per completed mission versus fixed operation?

**RQ2:** Does joint adaptation outperform independent single-layer adaptation after accounting for increased mission time, component switching overhead and constraint violations?

**RQ3:** How sensitive is performance to mismatched energy-model coefficients and uncertainty assumptions? Can energy benefits persist after holding parameters constant on unseen scenarios?

**RQ4:** What changes when embedded hardware measurements replace model-only timing and power coefficients?

## Testable hypotheses

- H1: On at least one prespecified synthetic scenario family, joint adaptation reduces mean energy per completed mission relative to fixed operation while preserving completion rate and deadline compliance.
- H2: On at least one held-out scenario family, joint adaptation improves over the best single-layer ablation on total mission energy under common constraints.
- H3: More aggressive age limits or tighter deadlines reduce attainable energy savings (a measurable trade-off, not an assumed universal truth).

No hypothesis is established by repository creation. Benchmark code exists to investigate them. Do not imply novelty, superiority or published findings without comparing external literature, real baselines and independent experiments.
