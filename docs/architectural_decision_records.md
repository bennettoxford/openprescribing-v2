# Architectural Decision Records

Architectural decision records document the decisions,
including the alternatives that were ruled out,
for requirements that have a high cost of change.[^1]

[^1]:
    The [Azure Well-Architected Framework][] defines architectural decision records in terms of architecturally significant requirements,
    which [Wikipedia][3] defines as requirements that
    "have a measurable effect on a computer system's architecture".
    Absent from the Wikipedia definition,
    but present in [the paper it cites][4],
    is the idea that the measurable effect is the cost of change.

## 000: Recording architectural decisions

We have decided to record architectural decisions in this document.

Experience tells us that it is a good idea to record architectural decisions.

* Suzanne reports that doing so encouraged her to consider other options when making a architectural decision
  and as a consequence she changed her mind about which option was the best option
  (mitigating the [Einstellung effect][]).

* Suzanne reports that doing so ensured that each option had a fair hearing
  and as a consequence the amount of conflict within her team (at the time) was reduced.

* Lucy reports that members of the REX team reflect on doing so in retros, standups, and one-to-ones.
  In turn, members of the REX team report that recording architectural decisions is a good idea.

* Several projects, maintained by different teams, record architectural decisions.
  For example, Ethelred, Interactive, Job Server, Metrics, OpenCodelists, OpenPathology, Pipeline Parser, Reports, and our sysadmin scripts.

Other people and organisations advocate for recording architectural decisions.

* Michael Nygard wrote [a blog post about architectural decision records][2].
  (He suggests they feature in [Documenting Software Architectures: Views and Beyond][].)

* Microsoft consider architectural decision records to be foundational to the [Azure Well-Architected Framework][].

* The Government Digital Service has published [a framework for architectural decision records][1].

Some process guidance may be helpful.

* Does the decision have a high cost of change?
  If it doesn't, then it's not necessary to record it.

* Will a developer need the information about the decision for their day-to-day work?
  If they will, then it probably belongs nearer to the code.
  (Although it might still be a good idea to record the decision.)

* Might the decision surprise a developer?
  Might a developer want to know more about the alternatives that were ruled out?
  If it might, and they might, then it's probably a good idea to record the decision.

* One decision should correspond to one section in this document;
  section headings should follow the observable pattern.

* Records (sections) should be concise.
  They should describe the decision (What?) and explain the rationale for the decision (Why?).

* If a later decision supersedes an earlier decision, then each record should link to the other record.

* Links and typos aside,
  we should treat *records* as immutable.
  (We should treat *decisions* as mutable, as later decisions my supersede earlier decisions.)

## 001: Using a single `Org` model

We have decided to use a single `Org` model for all types of organisation (e.g. nation, region, ICB).

Experience tells us that fundamentally,
an organisation is an entity with a code, a name, and a collection of practices.
These entities exist in a hierarchy with parents and children.
The type of organisation is important, but not *that* important.

We considered using a model for each type of organisation (e.g. `Nation`, `Region`, `Icb`).
Doing so, however, makes it hard to work with objects that could belong to any type of organisation,
such as sign-ups for alerts.
To work with such objects, we could
use [generic relations][5], but [these are hard to work with][6].
Alternatively, we could use one attribute for each type of organisation,
but experience tells us that these are hard to work with, too:
if we needed to add a new type of organisation, for example,
then we would have to update each object that could belong to any type of organisation.

The [Organisation Data Service][] (ODS) provide the data in this way,
through the [Data Search and Export Service][].
We create objects from this data,
but we don't update or delete these objects.
Consequently, we don't need to enforce data integrity constraints.

## 002: Using a single codebase for the project's two apps

We have decided to use a single codebase for the project's two apps: data and web.

The data app is responsible for fetching, ingesting, and querying prescribing data and all related metadata.
The web app is responsible for representing and interacting with the data provided by the data app,
as well as for providing services to users (e.g. sign-ups for alerts).

It's important that large amounts of data can be moved quickly
from SQLite and DuckDB to the rxdb module,
and from the rxdb module to the view modules.
This means running these components in the same process;
and this means using a single codebase for the project's two apps.

The "[Architecture][]" page on the wiki contains helpful process guidance.

[1]: https://www.gov.uk/government/publications/architectural-decision-record-framework/architectural-decision-record-framework
[2]: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
[3]: https://en.wikipedia.org/wiki/Architecturally_significant_requirements
[4]: https://researchrepository.ul.ie/entities/publication/a79ae7f9-449c-4bb9-8b0b-a33d25b5af7f
[5]: https://docs.djangoproject.com/en/6.0/ref/contrib/contenttypes/#generic-relations
[6]: https://lukeplant.me.uk/blog/posts/avoid-django-genericforeignkey/
[Architecture]: https://github.com/bennettoxford/openprescribing-v2/wiki/Architecture
[Azure Well-Architected Framework]: https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record
[Data Search and Export Service]: https://www.odsdatasearchandexport.nhs.uk/
[Documenting Software Architectures: Views and Beyond]: https://learning.oreilly.com/library/view/documenting-software-architectures/9780132488617/
[Einstellung effect]: https://en.wikipedia.org/wiki/Einstellung_effect
[Organisation Data Service]: https://digital.nhs.uk/services/organisation-data-service
