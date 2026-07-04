"""Grafana & Observability ontology contribution (CONCEPT:AU-KG.ontology.package-federation-migration).

Data-only subpackage: it carries two ``owl:Ontology`` modules which the
agent-utilities hub federates in via the ``agent_utilities.ontology_providers``
entry-point (the loader globs every ``*.ttl`` in this directory):

* ``grafana.ttl`` — ``http://knuckles.team/kg/grafana`` (Grafana dashboards,
  panels, alert rules, datasources and the services they monitor).
* ``observability.ttl`` — ``http://knuckles.team/kg/observability`` (ops /
  observability node types and streaming observations).

It holds no business logic and no heavy imports so the hub can resolve it
cheaply.
"""
